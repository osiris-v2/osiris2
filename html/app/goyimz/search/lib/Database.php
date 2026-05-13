<?php
/**
 * Gooyims Search Engine — Database Layer
 * Adapter para SQLite (search.db generado por SpiderBot)
 */
class Database {
    private static ?PDO $pdo = null;
    private static string $dbPath = '';

    public static function init(string $dbPath): void {
        self::$dbPath = $dbPath;
    }

    public static function get(): PDO {
        if (self::$pdo === null) {
            $path = self::$dbPath ?: dirname(__DIR__) . '/search.db';
            if (!file_exists($path)) {
                throw new RuntimeException("Base de datos no encontrada: $path");
            }
            self::$pdo = new PDO('sqlite:' . $path, null, null, [
                PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ]);
            self::$pdo->exec("PRAGMA journal_mode=WAL; PRAGMA cache_size=5000;");
        }
        return self::$pdo;
    }

    /** Ejecuta query con parámetros y devuelve todos los resultados */
    public static function fetchAll(string $sql, array $params = []): array {
        $stmt = self::get()->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll();
    }

    /** Devuelve una sola fila */
    public static function fetchOne(string $sql, array $params = []): ?array {
        $stmt = self::get()->prepare($sql);
        $stmt->execute($params);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    /** Devuelve un escalar */
    public static function fetchScalar(string $sql, array $params = []): mixed {
        $stmt = self::get()->prepare($sql);
        $stmt->execute($params);
        $row = $stmt->fetch(PDO::FETCH_NUM);
        return $row ? $row[0] : null;
    }
}
