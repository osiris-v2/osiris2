<?php
/**
 * Gooyims — API REST ligera
 * GET /api/search.php?q=...&tab=web&page=1&per_page=10
 * GET /api/search.php?action=stats
 * GET /api/search.php?action=detail&id=42
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');

require_once __DIR__ . '/../lib/Database.php';
require_once __DIR__ . '/../lib/SearchModel.php';

// Ruta a la DB: ajusta si es necesario
Database::init(dirname(__DIR__) . '/search.db');

function respond(mixed $data, int $status = 200): void {
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
    exit;
}

try {
    $action  = $_GET['action'] ?? 'search';

    if ($action === 'stats') {
        respond(SearchModel::stats());
    }

    if ($action === 'detail') {
        $id = (int)($_GET['id'] ?? 0);
        if (!$id) respond(['error' => 'id requerido'], 400);
        $row = SearchModel::detail($id);
        if (!$row) respond(['error' => 'no encontrado'], 404);
        respond($row);
    }

    // — Búsqueda —
    $q       = trim($_GET['q'] ?? '');
    if ($q === '') respond(['error' => 'Parámetro q requerido'], 400);

    $tab     = in_array($_GET['tab'] ?? '', ['web','ports','links','live']) ? $_GET['tab'] : 'web';
    $page    = max(1, (int)($_GET['page']    ?? 1));
    $perPage = min(50, max(5, (int)($_GET['per_page'] ?? 10)));

    $filters = [
        'only_http'  => !empty($_GET['only_http']),
        'port'       => isset($_GET['port']) ? (int)$_GET['port'] : null,
        'serendipia' => !empty($_GET['serendipia']),
        'fresh'      => !empty($_GET['fresh']),
    ];

    $result = SearchModel::search($q, $tab, $page, $perPage, $filters);
    respond($result);

} catch (RuntimeException $e) {
    respond(['error' => $e->getMessage()], 503);
} catch (Throwable $e) {
    respond(['error' => 'Error interno: ' . $e->getMessage()], 500);
}
