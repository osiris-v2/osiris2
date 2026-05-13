<?php
/**
 * Gooyims Search Engine — Search Model
 * Toda la lógica de consulta sobre las tablas scans/ports/links
 */

require_once __DIR__ . '/Database.php';

class SearchModel {

    /* ─── Paginación ─────────────────────────────────────────── */
    const PER_PAGE_DEFAULT = 10;

    /**
     * Búsqueda principal. Devuelve array con:
     *   total, page, per_page, results[]
     *
     * Campos buscables: ip, domain, html_content (ports), url (links)
     */
    public static function search(
        string $query,
        string $tab    = 'web',   // web | images | links | ports | live
        int    $page   = 1,
        int    $perPage = self::PER_PAGE_DEFAULT,
        array  $filters = []
    ): array {

        $page    = max(1, $page);
        $offset  = ($page - 1) * $perPage;
        $q       = '%' . $query . '%';

        switch ($tab) {
            case 'ports':  return self::searchPorts($q, $page, $perPage, $offset, $filters);
            case 'links':  return self::searchLinks($q, $page, $perPage, $offset);
            case 'live':   return self::searchLive ($q, $page, $perPage, $offset);
            default:       return self::searchWeb  ($q, $page, $perPage, $offset, $filters);
        }
    }

    /* ─── Web: unión scans + ports (http) ───────────────────── */
    private static function searchWeb(string $q, int $page, int $perPage, int $offset, array $filters): array {
        $whereClauses = ['(s.ip LIKE :q OR s.domain LIKE :q OR p.html_content LIKE :q)'];
        $params       = [':q' => $q];

        if (!empty($filters['only_http'])) {
            $whereClauses[] = 'p.is_http = 1';
        }
        if (!empty($filters['port'])) {
            $whereClauses[] = 'p.port = :port';
            $params[':port'] = (int)$filters['port'];
        }
        if (!empty($filters['fresh'])) {
            $whereClauses[] = "s.scan_time >= datetime('now', '-1 hour')";
        }

        $where = implode(' AND ', $whereClauses);
        $order = !empty($filters['serendipia']) ? 'RANDOM()' : 's.scan_time DESC';

        $countSql = "
            SELECT COUNT(DISTINCT s.id)
            FROM scans s
            LEFT JOIN ports p ON p.scan_id = s.id
            WHERE $where";

        $dataSql = "
            SELECT
                s.id, s.ip, s.domain, s.scan_time,
                p.port, p.protocol, p.service, p.is_http,
                SUBSTR(p.html_content, 1, 320) AS snippet,
                (SELECT COUNT(*) FROM links l WHERE l.scan_id = s.id) AS link_count
            FROM scans s
            LEFT JOIN ports p ON p.scan_id = s.id
            WHERE $where
            GROUP BY s.id
            ORDER BY $order
            LIMIT :limit OFFSET :offset";

        $total = (int)Database::fetchScalar($countSql, $params);
        $params[':limit']  = $perPage;
        $params[':offset'] = $offset;
        $rows  = Database::fetchAll($dataSql, $params);

        return self::wrap($rows, $total, $page, $perPage, $query, $tab);
    }

    /* ─── Ports: listado de puertos abiertos ─────────────────── */
    private static function searchPorts(string $q, int $page, int $perPage, int $offset, array $filters): array {
        $params = [':q' => $q];
        $extra  = '';
        if (!empty($filters['port'])) {
            $extra = 'AND p.port = :port';
            $params[':port'] = (int)$filters['port'];
        }

        $countSql = "
            SELECT COUNT(*)
            FROM ports p
            JOIN scans s ON s.id = p.scan_id
            WHERE (s.ip LIKE :q OR s.domain LIKE :q OR p.service LIKE :q) $extra";

        $dataSql = "
            SELECT
                p.id, p.port, p.protocol, p.service, p.is_http,
                s.ip, s.domain, s.scan_time,
                SUBSTR(p.html_content, 1, 200) AS snippet
            FROM ports p
            JOIN scans s ON s.id = p.scan_id
            WHERE (s.ip LIKE :q OR s.domain LIKE :q OR p.service LIKE :q) $extra
            ORDER BY s.scan_time DESC
            LIMIT :limit OFFSET :offset";

        $total = (int)Database::fetchScalar($countSql, $params);
        $params[':limit']  = $perPage;
        $params[':offset'] = $offset;
        $rows = Database::fetchAll($dataSql, $params);

        return self::wrap($rows, $total, $page, $perPage, $q, 'ports');
    }

    /* ─── Links: URLs descubiertas ───────────────────────────── */
    private static function searchLinks(string $q, int $page, int $perPage, int $offset): array {
        $params = [':q' => $q];

        $countSql = "
            SELECT COUNT(*)
            FROM links l
            JOIN scans s ON s.id = l.scan_id
            WHERE l.url LIKE :q OR s.domain LIKE :q OR s.ip LIKE :q";

        $dataSql = "
            SELECT l.id, l.url, l.link_type,
                   s.ip, s.domain, s.scan_time
            FROM links l
            JOIN scans s ON s.id = l.scan_id
            WHERE l.url LIKE :q OR s.domain LIKE :q OR s.ip LIKE :q
            ORDER BY s.scan_time DESC
            LIMIT :limit OFFSET :offset";

        $total = (int)Database::fetchScalar($countSql, $params);
        $params[':limit']  = $perPage;
        $params[':offset'] = $offset;
        $rows = Database::fetchAll($dataSql, $params);

        return self::wrap($rows, $total, $page, $perPage, $q, 'links');
    }

    /* ─── Live: los más recientes, sin filtro ─────────────────── */
    private static function searchLive(string $q, int $page, int $perPage, int $offset): array {
        $params = [':q' => $q];

        $countSql = "
            SELECT COUNT(DISTINCT s.id)
            FROM scans s
            LEFT JOIN ports p ON p.scan_id = s.id
            WHERE s.ip LIKE :q OR s.domain LIKE :q
               OR p.html_content LIKE :q";

        $dataSql = "
            SELECT s.id, s.ip, s.domain, s.scan_time, s.thread_id,
                   GROUP_CONCAT(DISTINCT p.port) AS open_ports
            FROM scans s
            LEFT JOIN ports p ON p.scan_id = s.id
            WHERE s.ip LIKE :q OR s.domain LIKE :q OR p.html_content LIKE :q
            GROUP BY s.id
            ORDER BY s.scan_time DESC
            LIMIT :limit OFFSET :offset";

        $total = (int)Database::fetchScalar($countSql, $params);
        $params[':limit']  = $perPage;
        $params[':offset'] = $offset;
        $rows = Database::fetchAll($dataSql, $params);

        return self::wrap($rows, $total, $page, $perPage, $q, 'live');
    }

    /* ─── Stats globales (para el dashboard) ─────────────────── */
    public static function stats(): array {
        return [
            'total_scans'  => (int)Database::fetchScalar("SELECT COUNT(*) FROM scans"),
            'total_ports'  => (int)Database::fetchScalar("SELECT COUNT(*) FROM ports"),
            'total_http'   => (int)Database::fetchScalar("SELECT COUNT(*) FROM ports WHERE is_http=1"),
            'total_links'  => (int)Database::fetchScalar("SELECT COUNT(*) FROM links"),
            'total_domains'=> (int)Database::fetchScalar("SELECT COUNT(DISTINCT domain) FROM scans WHERE domain IS NOT NULL AND domain != ''"),
            'last_scan'    => Database::fetchScalar("SELECT MAX(scan_time) FROM scans"),
            'top_ports'    => Database::fetchAll("SELECT port, COUNT(*) as c FROM ports GROUP BY port ORDER BY c DESC LIMIT 8"),
        ];
    }

    /* ─── Detalle de un scan ─────────────────────────────────── */
    public static function detail(int $id): ?array {
        $scan  = Database::fetchOne("SELECT * FROM scans WHERE id = ?", [$id]);
        if (!$scan) return null;
        $scan['ports'] = Database::fetchAll("SELECT * FROM ports WHERE scan_id = ?", [$id]);
        $scan['links'] = Database::fetchAll("SELECT * FROM links WHERE scan_id = ? LIMIT 200", [$id]);
        return $scan;
    }

    /* ─── Envuelve resultados con metadatos de paginación ─────── */
    private static function wrap(array $rows, int $total, int $page, int $perPage, string $query, string $tab): array {
        return [
            'query'      => $query,
            'tab'        => $tab,
            'total'      => $total,
            'page'       => $page,
            'per_page'   => $perPage,
            'total_pages'=> max(1, (int)ceil($total / $perPage)),
            'results'    => $rows,
        ];
    }
}
