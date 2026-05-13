<?php
/**
 * Gooyims — View Helpers
 * Funciones puras de presentación (sin lógica de negocio)
 */

function h(string $s): string {
    return htmlspecialchars($s, ENT_QUOTES, 'UTF-8');
}

function highlight(string $text, string $query): string {
    if (!$query || strlen($query) < 2) return h($text);
    $q = preg_quote(trim($query, '%'), '/');
    return preg_replace(
        "/($q)/iu",
        '<mark>$1</mark>',
        h($text)
    );
}

function buildUrl(array $params): string {
    $current = $_GET;
    $merged  = array_merge($current, $params);
    return '?' . http_build_query($merged);
}

function pagination(int $page, int $totalPages, int $total, string $query): string {
    if ($totalPages <= 1) return '';
    $out  = '<nav class="pager" aria-label="Paginación">';
    $out .= '<span class="pager-info">' . number_format($total) . ' resultados</span>';
    $out .= '<div class="pager-btns">';

    if ($page > 1) {
        $out .= '<a class="pager-btn" href="' . h(buildUrl(['page' => $page - 1])) . '">← Anterior</a>';
    }

    $start = max(1, $page - 2);
    $end   = min($totalPages, $page + 2);
    for ($i = $start; $i <= $end; $i++) {
        $active = $i === $page ? ' active' : '';
        $out   .= '<a class="pager-btn num' . $active . '" href="' . h(buildUrl(['page' => $i])) . '">' . $i . '</a>';
    }

    if ($page < $totalPages) {
        $out .= '<a class="pager-btn" href="' . h(buildUrl(['page' => $page + 1])) . '">Siguiente →</a>';
    }

    $out .= '</div></nav>';
    return $out;
}

function renderWebResult(array $r, string $query): string {
    $ip      = h($r['ip'] ?? '');
    $domain  = $r['domain'] ? h($r['domain']) : $ip;
    $port    = $r['port']   ? ':' . h($r['port']) : '';
    $proto   = ($r['is_http'] ?? 0) ? 'http' : 'tcp';
    $url     = $proto . '://' . $ip . $port;
    $snippet = highlight(strip_tags($r['snippet'] ?? ''), trim($_GET['q'] ?? '', '%'));
    $time    = $r['scan_time'] ? date('d M Y H:i', strtotime($r['scan_time'])) : '—';
    $links   = (int)($r['link_count'] ?? 0);
    $service = $r['service'] ? ' · <span class="badge">' . h($r['service']) . '</span>' : '';

    return <<<HTML
    <article class="result-card">
      <div class="result-meta">
        <span class="result-domain">$domain$port</span>
        <span class="result-url">$url</span>
        $service
      </div>
      <h3 class="result-title">
        <a href="search.php?action=detail&id={$r['id']}" class="result-link">$domain</a>
      </h3>
      <p class="result-snippet">$snippet</p>
      <footer class="result-footer">
        <span>$time</span>
        <span>$links enlaces</span>
        <span class="result-ip">IP: $ip</span>
      </footer>
    </article>
    HTML;
}

function renderPortResult(array $r, string $query): string {
    $ip   = h($r['ip'] ?? '');
    $port = h($r['port'] ?? '');
    $svc  = h($r['service'] ?? '—');
    $http = ($r['is_http'] ?? 0) ? '<span class="badge http">HTTP</span>' : '';
    $snip = highlight(strip_tags($r['snippet'] ?? ''), trim($query, '%'));
    $time = $r['scan_time'] ? date('d M Y H:i', strtotime($r['scan_time'])) : '—';

    return <<<HTML
    <article class="result-card port-card">
      <div class="result-meta">
        <span class="result-domain">$ip</span>
        <span class="badge port-badge">:$port</span>
        $http
      </div>
      <h3 class="result-title">$svc en $ip:$port</h3>
      <p class="result-snippet">$snip</p>
      <footer class="result-footer">
        <span>$time</span>
        <span>Proto: {$r['protocol']}</span>
      </footer>
    </article>
    HTML;
}

function renderLinkResult(array $r, string $query): string {
    $url    = h($r['url'] ?? '');
    $domain = h($r['domain'] ?? $r['ip'] ?? '');
    $type   = h($r['link_type'] ?? '');
    $time   = $r['scan_time'] ? date('d M Y H:i', strtotime($r['scan_time'])) : '—';
    $hl     = highlight($r['url'] ?? '', trim($query, '%'));

    return <<<HTML
    <article class="result-card link-card">
      <div class="result-meta">
        <span class="result-domain">$domain</span>
        <span class="badge">$type</span>
      </div>
      <h3 class="result-title">
        <a href="$url" rel="noopener" target="_blank" class="result-link ext-link">$hl</a>
      </h3>
      <footer class="result-footer"><span>$time</span></footer>
    </article>
    HTML;
}

function renderLiveResult(array $r, string $query): string {
    $ip     = h($r['ip'] ?? '');
    $domain = $r['domain'] ? h($r['domain']) : '—';
    $ports  = h($r['open_ports'] ?? '—');
    $time   = $r['scan_time'] ? date('d M Y H:i:s', strtotime($r['scan_time'])) : '—';
    $tid    = (int)($r['thread_id'] ?? 0);

    return <<<HTML
    <article class="result-card live-card">
      <div class="live-pulse" aria-hidden="true"></div>
      <div class="result-meta">
        <span class="result-domain">$ip</span>
        <span class="result-url">$domain</span>
      </div>
      <h3 class="result-title">
        <a href="search.php?action=detail&id={$r['id']}" class="result-link">$ip</a>
      </h3>
      <p class="result-snippet">Puertos abiertos: <strong>$ports</strong></p>
      <footer class="result-footer">
        <span>$time</span>
        <span>Thread #$tid</span>
      </footer>
    </article>
    HTML;
}
