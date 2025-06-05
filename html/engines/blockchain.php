<?php
// --- Interfaz de comunicación con Gemini AI de Google ---
// Interfaz Name: Osiris-Blockchain-Web
// Version: gemini (interfaz web para añadir bloques)
// Idioma: Español
// Instrucciones: Interfaz web básica para añadir bloques a la blockchain de Osiris.
// ---------------------------------------------------------

// --- Configuración ---
// Rutas relativas a la ubicación de este script PHP
$dbPath = __DIR__ . '/com/blockchain/Xy2.db';
$privateKeyPath = __DIR__ . '/private_keXy2.pem';

// Asegurarse de que la zona horaria esté establecida para timestamps consistentes
date_default_timezone_set('UTC'); // Considera usar tu zona horaria local si es necesario

// --- Funciones de utilidad (equivalentes a las de Python) ---

/**
 * Calcula el hash SHA-256 de los datos serializados del bloque.
 * Debe coincidir *exactamente* con la lógica de serialización en Python.
 */
function calculateHash(string $timestamp, string $data, string $previousHash): string {
    $blockData = [
        "timestamp" => $timestamp,
        "data" => $data,
        "previous_hash" => $previousHash,
    ];
    // Ordenar claves para asegurar consistencia en la serialización JSON
    ksort($blockData);
    // JSON_UNESCAPED_SLASHES y JSON_UNESCAPED_UNICODE para coincidir mejor con la salida de Python json.dumps por defecto
    $jsonString = json_encode($blockData, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    if ($jsonString === false) {
        throw new Exception("Error serializando datos para el hash: " . json_last_error_msg());
    }
    return hash('sha256', $jsonString);
}

/**
 * Genera la cadena a firmar, replicando la salida de __str__ del objeto Block de Python
 * antes de añadir la línea de 'Signature'.
 */
function getStringToSign(string $timestamp, string $data, string $previousHash, string $currentHash): string {
     // Nota: El método __str__ de Python en tu código INCLUYE el hash calculado en el mensaje a firmar.
     // Replicamos ese formato exactamente.
    return "Timestamp: {$timestamp}\nData: {$data}\nPrevious Hash: {$previousHash}\nHash: {$currentHash}";
}

/**
 * Carga la clave privada desde el archivo.
 * Retorna un recurso de clave privada de OpenSSL o false en caso de error.
 */
function loadPrivateKey(string $privateKeyPath) {
    if (!file_exists($privateKeyPath)) {
        error_log("Error: Archivo de clave privada no encontrado en $privateKeyPath");
        return false;
    }
    if (!is_readable($privateKeyPath)) {
         error_log("Error: Permisos de lectura insuficientes para $privateKeyPath");
         return false;
    }
    // Carga la clave privada desde el archivo PEM
    // Si tu clave privada está encriptada, necesitarías pasar la contraseña como segundo argumento
    $privateKeyResource = openssl_pkey_get_private(file_get_contents($privateKeyPath));
    if ($privateKeyResource === false) {
        error_log("Error al cargar la clave privada: " . openssl_error_string());
    }
    return $privateKeyResource;
}


// --- Lógica de la Blockchain (parte de añadir bloque) ---

$message = ''; // Variable para mensajes de estado/error

// Procesar la solicitud POST para añadir un bloque
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $blockData = $_POST['block_data'] ?? ''; // Obtener los datos del formulario

    if (empty($blockData)) {
        $message = '<p style="color: orange;">⚠️ Introduce datos para el bloque.</p>';
    } else {
        // Asegurar que el directorio de la base de datos existe
        $dbDir = dirname($dbPath);
        if (!is_dir($dbDir)) {
            if (!mkdir($dbDir, 0777, true)) { // Permisos 0777 son permisivos, ajusta según tu entorno
                $message = '<p style="color: red;">❌ Error: No se pudo crear el directorio de la base de datos.</p>';
            }
        }

        if (empty($message)) { // Si no hubo error al crear el directorio
            $db = null; // Inicializar variable de base de datos a null
            $privateKeyResource = null; // Inicializar variable de clave a null

            try {
                // 1. Conectar a la base de datos SQLite
                $db = new SQLite3($dbPath);
                // Configurar row_factory para obtener columnas por nombre (similar a sqlite3.Row en Python)
                $db->enableExceptions(true); // Habilitar excepciones para un mejor manejo de errores

                // 2. Obtener el último bloque para el previous_hash
                $result = $db->query('SELECT hash FROM blocks ORDER BY id DESC LIMIT 1');
                $latestBlock = $result ? $result->fetchArray(SQLITE3_ASSOC) : null;
                $previousHash = $latestBlock ? $latestBlock['hash'] : "0"; // Hash del bloque anterior o "0" para el génesis

                // 3. Cargar la clave privada
                $privateKeyResource = loadPrivateKey($privateKeyPath);
                if ($privateKeyResource === false) {
                    throw new Exception("No se pudo cargar la clave privada.");
                }

                // 4. Preparar los datos del nuevo bloque
                $timestamp = date('c'); // Formato ISO 8601 (compatible con Python isoformat)

                // 5. Calcular el hash del nuevo bloque
                $currentHash = calculateHash($timestamp, $blockData, $previousHash);

                // 6. Generar la firma
                $stringToSign = getStringToSign($timestamp, $blockData, $previousHash, $currentHash);
                 // openssl_pkey_sign() para usar PSS padding si está soportado por la clave y PHP
                 // OPENSSL_ALGO_SHA256 es el algoritmo de digest, OPENSSL_PKCS1_PSS_PADDING el padding
                $signatureResult = openssl_pkey_sign($stringToSign, $signature, $privateKeyResource, OPENSSL_ALGO_SHA256);

                if ($signatureResult === false) {
                    throw new Exception("Error al firmar el bloque: " . openssl_error_string());
                }

                // 7. Insertar el nuevo bloque en la base de datos
                $stmt = $db->prepare('INSERT INTO blocks (timestamp, data, previous_hash, hash, signature) VALUES (:timestamp, :data, :previous_hash, :hash, :signature)');
                $stmt->bindValue(':timestamp', $timestamp, SQLITE3_TEXT);
                $stmt->bindValue(':data', $blockData, SQLITE3_TEXT);
                $stmt->bindValue(':previous_hash', $previousHash, SQLITE3_TEXT);
                $stmt->bindValue(':hash', $currentHash, SQLITE3_TEXT);
                $stmt->bindValue(':signature', $signature, SQLITE3_BLOB); // Guardar la firma como BLOB

                $result = $stmt->execute();

                if ($result === false) {
                    throw new Exception("Error al insertar el bloque: " . $db->lastErrorMsg());
                }

                $message = '<p style="color: green;">✅ Bloque añadido con éxito!</p>';
                // Limpiar el campo de entrada después de añadir
                 $blockData = ''; // Esto borra el valor del campo en el formulario después de un post exitoso

            } catch (Exception $e) {
                error_log("Error al añadir bloque desde web: " . $e->getMessage());
                error_log("Trace: " . $e->getTraceAsString()); // Log completo del error
                $message = '<p style="color: red;">❌ Error al añadir bloque: ' . htmlspecialchars($e->getMessage()) . '</p>';
                 // Puedes añadir más detalles del error aquí si estás depurando, pero ten cuidado en producción
            } finally {
                // 8. Cerrar la conexión a la base de datos y liberar recursos de la clave
                if ($db) {
                    $db->close();
                }
                if ($privateKeyResource) {
                    openssl_pkey_free($privateKeyResource);
                }
            }
        }
    }
}

?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Osiris Blockchain - Añadir Bloque</title>
    <style>
        body { font-family: sans-serif; line-height: 1.6; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 600px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #555; }
        form div { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
        button { display: block; width: 100%; padding: 10px; background-color: #5cb85c; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background-color: #4cae4c; }
        .message { margin-top: 20px; padding: 10px; border-radius: 4px; }
        .message p { margin: 0; }
        .message .success { background-color: #dff0d8; border-color: #d0e9c6; color: #3c763d; }
        .message .error { background-color: #f2dede; border-color: #ebccd1; color: #a94442; }
        .message .warning { background-color: #fcf8e3; border-color: #faebcc; color: #8a6d3b; }
        .security-warning { margin-top: 30px; padding: 15px; background-color: #ffdddd; border-left: 6px solid #f44336; margin-bottom: 20px; font-size: 0.9em; color: #555; }
        .security-warning strong { color: #f44336; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Osiris Blockchain - Añadir Bloque</h2>
        <p>Añade un nuevo bloque a la blockchain de Osiris.</p>

        <div class="security-warning">
            <strong>Advertencia de Seguridad:</strong> Este script es un ejemplo básico. Exponer la clave privada en un entorno web de esta manera es INSEGURO para producción. Implementa medidas de seguridad adecuadas (autenticación, validación, gestión segura de claves) para cualquier uso real.
        </div>

        <?php if (!empty($message)): ?>
            <div class="message"><?= $message ?></div>
        <?php endif; ?>

        <form method="POST" action="">
            <div>
                <label for="block_data">Datos para el Bloque:</label>
                <input type="text" id="block_data" name="block_data" required value="<?= htmlspecialchars($blockData ?? '') ?>">
            </div>
            <button type="submit">Añadir Bloque</button>
        </form>

        <?php
        // Opcional: Mostrar los últimos bloques añadidos para verificar
        try {
             $db = new SQLite3($dbPath, SQLITE3_OPEN_READONLY);
             $db->enableExceptions(true);
             $result = $db->query('SELECT id, timestamp, hash, SUBSTR(data, 1, 50) AS data_preview FROM blocks ORDER BY id DESC LIMIT 5'); // Mostrar los últimos 5
             $recentBlocks = [];
             while($row = $result->fetchArray(SQLITE3_ASSOC)) {
                 $recentBlocks[] = $row;
             }
             $db->close();

             if (!empty($recentBlocks)): ?>
                 <h3 style="margin-top: 30px;">Últimos Bloques Añadidos:</h3>
                 <ul>
                     <?php foreach($recentBlocks as $block): ?>
                         <li><strong>ID #<?= $block['id'] ?>:</strong> <?= htmlspecialchars($block['data_preview']) ?>... (Hash: <?= substr($block['hash'], 0, 8) ?>...)</li>
                     <?php endforeach; ?>
                 </ul>
             <?php endif;

        } catch (Exception $e) {
             error_log("Error al mostrar bloques recientes: " . $e->getMessage());
             // No mostramos el error detallado al usuario en la página web por seguridad, solo lo loggeamos.
        }
        ?>

    </div>
</body>
</html>