<?php
/**
 * Osiris Documentation Viewer
 *
 * Este script PHP actúa como un router para servir y buscar la documentación
 * almacenada en archivos Markdown (.md) en la carpeta 'templates/'.
 * Convierte el Markdown a HTML y maneja las peticiones AJAX del frontend.
 */

// Incluir la biblioteca Parsedown para la conversión de Markdown
require_once '../lib/php/Parsedown.php';

// Directorio de los templates de documentación
define('TEMPLATES_DIR', __DIR__ . '/templates/');

// Instancia de Parsedown
$Parsedown = new Parsedown();

/**
 * Función de sanitización básica para nombres de archivo y rutas.
 * Evita ataques de Path Traversal (../)
 */
function sanitize_filename($filename) {
    // Elimina cualquier carácter que no sea alfanumérico, guion, guion bajo o punto
    $filename = preg_replace('/[^a-zA-Z0-9_\-.]/', '', $filename);
    // Asegura que no haya segmentos de ruta como '../'
    $filename = str_replace(['../', './'], '', $filename);
    // Limita la longitud para prevenir problemas
    return substr($filename, 0, 255);
}

/**
 * Función para obtener la lista de capítulos (archivos .md)
 */
function get_chapter_list() {
    $files = [];
    if (is_dir(TEMPLATES_DIR)) {
        foreach (scandir(TEMPLATES_DIR) as $file) {
            if (pathinfo($file, PATHINFO_EXTENSION) === 'md') {
                // Generamos un título más amigable eliminando la extensión y reemplazando guiones
                $title = ucwords(str_replace(['_', '-'], ' ', basename($file, '.md')));
                $files[] = [
                    'filename' => $file,
                    'title' => $title
                ];
            }
        }
    }
    // Ordenar alfabéticamente para una mejor UX
    usort($files, function($a, $b) {
        return strcmp($a['title'], $b['title']);
    });
    return $files;
}

/**
 * Función para cargar y convertir un capítulo específico.
 */
function load_chapter_content($filename) {
    global $Parsedown;
    $sanitized_filename = sanitize_filename($filename);
    $filepath = realpath(TEMPLATES_DIR . $sanitized_filename);

    // Seguridad: Asegurarse de que el archivo exista y esté dentro del directorio de templates.
    if ($filepath && file_exists($filepath) && strpos($filepath, realpath(TEMPLATES_DIR)) === 0) {
        $markdown_content = file_get_contents($filepath);
        // Convertir Markdown a HTML
        $html_content = $Parsedown->text($markdown_content);
        return [
            'status' => 'success',
            'content' => $html_content,
            'title' => ucwords(str_replace(['_', '-'], ' ', basename($sanitized_filename, '.md')))
        ];
    } else {
        return [
            'status' => 'error',
            'message' => 'Capítulo no encontrado o ruta inválida.',
            'content' => '<h1>Error 404: Capítulo no encontrado</h1><p>Parece que el capítulo que buscas no existe o ha sido movido. Intenta buscar en la lista de capítulos.</p>'
        ];
    }
}

/**
 * Función para buscar texto en los capítulos.
 */
function search_documentation($query) {
    $results = [];
    $query = strtolower(trim($query));

    if (empty($query)) {
        return ['status' => 'success', 'chapters' => []]; // No se encontraron capítulos para una query vacía
    }

    $chapter_list = get_chapter_list();

    foreach ($chapter_list as $chapter) {
        $filepath = realpath(TEMPLATES_DIR . $chapter['filename']);
        if ($filepath && file_exists($filepath) && strpos($filepath, realpath(TEMPLATES_DIR)) === 0) {
            $content = file_get_contents($filepath);
            // Búsqueda simple de subcadena (puedes expandir esto con regex o indexación para algo más robusto)
            if (stripos($content, $query) !== false || stripos($chapter['title'], $query) !== false) {
                $results[] = $chapter; // Retorna el capítulo completo si hay una coincidencia
            }
        }
    }
    return ['status' => 'success', 'chapters' => $results];
}

// -------------------------------------------------------------------------
// Lógica de ruteo para peticiones AJAX
// -------------------------------------------------------------------------

if (isset($_GET['action'])) {
    header('Content-Type: application/json'); // Aseguramos que la respuesta sea JSON

    switch ($_GET['action']) {
        case 'list':
            echo json_encode(get_chapter_list());
            break;
        case 'load':
            if (isset($_GET['chapter'])) {
                echo json_encode(load_chapter_content($_GET['chapter']));
            } else {
                echo json_encode(['status' => 'error', 'message' => 'Falta el parámetro "chapter".']);
            }
            break;
        case 'search':
            if (isset($_GET['query'])) {
                echo json_encode(search_documentation($_GET['query']));
            } else {
                echo json_encode(['status' => 'error', 'message' => 'Falta el parámetro "query".']);
            }
            break;
        default:
            echo json_encode(['status' => 'error', 'message' => 'Acción inválida.']);
            break;
    }
    exit; // Importante para evitar que se renderice el HTML después del JSON
}

// -------------------------------------------------------------------------
// HTML principal de la aplicación (solo se renderiza si no es una petición AJAX)
// -------------------------------------------------------------------------
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Osiris Documentation System</title>
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23FFD700' d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-12h2v6h-2zm0 8h2v2h-2z'/%3E%3C/svg%3E" type="image/svg+xml">

    <!-- Estilos CSS con vw/vh y calc() - ¡Sorpréndeme! -->
    <style>
        :root {
            --primary-color: #FFD700; /* Osiris Gold */
            --secondary-color: #00BFFF; /* Deep Sky Blue */
            --background-dark: #1a1a2e; /* Dark theme background */
            --background-light: #2c0b0b; /* Dark theme slightly lighter */
            --text-color: #e0e0e0;
            --border-color: #3b3b5c;
            --highlight-bg: rgba(255, 215, 0, 0.2);
            --transition-speed: 0.3s;
        }

        /* Reset y box-sizing */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body {
            height: 100%;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--background-dark);
            color: var(--text-color);
            line-height: 1.6;
            overflow: hidden; /* Controla el scroll principal */
        }

        body {
            display: flex;
            flex-direction: column;
        }

        /* Header */
        header {
            background-color: var(--background-light);
            padding: calc(1vh + 1vw);
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--border-color);
            height: calc(8vh); /* Altura dinámica */
            min-height: 50px;
        }

        header h1 {
            font-size: calc(1.8vw + 0.5rem); /* Tamaño de texto responsivo */
            color: var(--primary-color);
            text-shadow: 0 0 5px rgba(255, 215, 0, 0.5);
            letter-spacing: 0.1vw;
        }

        /* Contenedor principal: Sidebar y Contenido */
        main {
            display: flex;
            flex: 1; /* Ocupa el espacio restante */
            overflow: hidden; /* Para que los scrolls internos funcionen bien */
        }

        /* Sidebar de navegación */
        #sidebar {
            width: calc(25vw); /* Ancho dinámico */
            min-width: 250px; /* Ancho mínimo para legibilidad */
            max-width: 350px; /* Ancho máximo para no ocupar demasiado */
            background-color: var(--background-light);
            border-right: 1px solid var(--border-color);
            padding: calc(1vh + 1vw);
            overflow-y: auto; /* Scroll si hay muchos capítulos */
            display: flex;
            flex-direction: column;
            gap: calc(0.5vh);
        }

        #sidebar h2 {
            font-size: calc(1.5vw + 0.3rem);
            color: var(--secondary-color);
            margin-bottom: calc(1vh);
            text-align: center;
        }

        #searchInput {
            width: 100%;
            padding: calc(0.8vh + 0.5vw);
            margin-bottom: calc(1.5vh);
            border: 1px solid var(--border-color);
            border-radius: calc(0.5vw);
            background-color: var(--background-dark);
            color: var(--text-color);
            font-size: calc(0.9vw + 0.3rem);
            transition: border-color var(--transition-speed);
        }

        #searchInput::placeholder {
            color: var(--text-color);
            opacity: 0.7;
        }

        #searchInput:focus {
            outline: none;
            border-color: var(--primary-color);
        }

        #chapterList {
            list-style: none;
            flex-grow: 1;
            overflow-y: auto; /* Scroll para la lista de capítulos */
        }

        #chapterList li {
            margin-bottom: calc(0.5vh);
        }

        #chapterList li a {
            display: block;
            padding: calc(0.8vh + 0.3vw);
            color: var(--text-color);
            text-decoration: none;
            font-size: calc(0.85vw + 0.2rem);
            border-radius: calc(0.3vw);
            transition: background-color var(--transition-speed), color var(--transition-speed);
        }

        #chapterList li a:hover,
        #chapterList li a.active {
            background-color: var(--primary-color);
            color: var(--background-dark);
            box-shadow: 0 0 8px rgba(255, 215, 0, 0.4);
            transform: translateX(calc(0.5vw)); /* Pequeño efecto de desplazamiento */
        }
        #chapterList li a.active {
             font-weight: bold;
        }


        /* Área de contenido */
        #contentArea {
            flex: 1; /* Ocupa el espacio restante */
            padding: calc(2vh + 2vw); /* Relleno responsivo */
            overflow-y: auto; /* Scroll para el contenido */
            scroll-behavior: smooth; /* Desplazamiento suave */
        }

        #contentArea #chapterTitle {
            font-size: calc(2.2vw + 0.8rem);
            color: var(--primary-color);
            margin-bottom: calc(2vh);
            border-bottom: 2px solid var(--secondary-color);
            padding-bottom: calc(1vh);
        }

        #chapterContent {
            font-size: calc(1vw + 0.2rem);
            line-height: 1.8;
            max-width: 80ch; /* Ancho de línea ideal para lectura */
            margin: 0 auto; /* Centra el contenido */
            padding-right: calc(1vw); /* Espacio para el scrollbar */
        }

        /* Estilos para el contenido Markdown renderizado */
        #chapterContent h1, h2, h3, h4, h5, h6 {
            color: var(--secondary-color);
            margin-top: calc(2.5vh);
            margin-bottom: calc(1.5vh);
            line-height: 1.3;
        }
        #chapterContent h1 { font-size: calc(1.8vw + 0.6rem); border-bottom: 1px dashed var(--border-color); padding-bottom: calc(0.5vh); }
        #chapterContent h2 { font-size: calc(1.5vw + 0.5rem); }
        #chapterContent h3 { font-size: calc(1.2vw + 0.4rem); }
        #chapterContent p {
            margin-bottom: calc(1.5vh);
        }
        #chapterContent ul, ol {
            margin-left: calc(2vw);
            margin-bottom: calc(1.5vh);
        }
        #chapterContent code {
            background-color: var(--background-light);
            padding: calc(0.3vh + 0.3vw);
            border-radius: calc(0.3vw);
            font-family: 'Cascadia Code', 'Fira Code', 'monospace';
            color: var(--primary-color);
            font-size: calc(0.8vw + 0.1rem);
        }
        #chapterContent pre {
            background-color: var(--background-light);
            padding: calc(1vh + 1vw);
            border-radius: calc(0.5vw);
            overflow-x: auto;
            margin-bottom: calc(2vh);
        }
        #chapterContent pre code {
            display: block;
            padding: 0;
            background: none;
            color: inherit;
            font-size: calc(0.9vw + 0.1rem);
        }
        #chapterContent a {
            color: var(--primary-color);
            text-decoration: none;
            transition: color var(--transition-speed);
        }
        #chapterContent a:hover {
            text-decoration: underline;
            color: var(--secondary-color);
        }
        #chapterContent blockquote {
            border-left: 4px solid var(--secondary-color);
            padding-left: calc(1vw);
            margin: calc(2vh) 0;
            color: var(--text-color);
            background-color: rgba(0, 191, 255, 0.1);
            border-radius: calc(0.5vw);
        }

        /* Estilos de carga (loading spinner) */
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(26, 26, 46, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: opacity var(--transition-speed), visibility var(--transition-speed);
        }

        .loading-overlay.active {
            opacity: 1;
            visibility: visible;
        }

        .spinner {
            border: calc(0.5vw) solid rgba(255, 215, 0, 0.2);
            border-top: calc(0.5vw) solid var(--primary-color);
            border-radius: 50%;
            width: calc(6vw);
            height: calc(6vw);
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Mensajes de error/info */
        .message-box {
            background-color: rgba(255, 0, 0, 0.2);
            border: 1px solid red;
            padding: calc(1.5vh + 1vw);
            margin: calc(2vh) 0;
            border-radius: calc(0.5vw);
            color: #ffcccc;
        }
        .message-box.success {
            background-color: rgba(0, 255, 0, 0.2);
            border-color: green;
            color: #ccffcc;
        }

        /* Scrollbar styling (Webkit) */
        ::-webkit-scrollbar {
            width: calc(0.8vw);
            height: calc(0.8vw);
        }
        ::-webkit-scrollbar-track {
            background: var(--background-dark);
            border-radius: calc(0.5vw);
        }
        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: calc(0.5vw);
        }
        ::-webkit-scrollbar-thumb:hover {
            background: var(--secondary-color);
        }

        /* Media Queries para pantallas más pequeñas (adaptación básica) */
        @media (max-width: 768px) {
            header h1 {
                font-size: calc(3vw + 0.5rem);
            }
            main {
                flex-direction: column; /* Apilar sidebar y contenido */
            }
            #sidebar {
                width: 100%; /* Sidebar ocupa todo el ancho */
                max-width: none;
                min-width: unset;
                height: calc(30vh); /* Altura del sidebar para móviles */
                border-right: none;
                border-bottom: 1px solid var(--border-color);
                overflow-y: auto; /* Scroll vertical para el sidebar */
            }
            #sidebar h2 {
                font-size: calc(4vw + 0.3rem);
            }
            #searchInput {
                font-size: calc(2.5vw + 0.3rem);
                padding: calc(1.5vh + 0.5vw);
            }
            #chapterList li a {
                font-size: calc(2.5vw + 0.2rem);
                padding: calc(1.5vh + 0.3vw);
            }
            #contentArea {
                padding: calc(3vh + 3vw);
                flex: 1;
            }
            #contentArea #chapterTitle {
                font-size: calc(4vw + 0.8rem);
            }
            #chapterContent {
                font-size: calc(3vw + 0.2rem);
            }
            #chapterContent pre code {
                font-size: calc(2.8vw + 0.1rem);
            }
        }
    </style>

    <!-- highlight.js para resaltado de sintaxis -->
    <link rel="stylesheet" href="//cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
    <script src="//cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>

</head>
<body>
    <header>
        <h1>Osiris Documentation</h1>
    </header>

    <main>
        <nav id="sidebar">
            <h2>Capítulos</h2>
            <input type="text" id="searchInput" placeholder="Buscar capítulo...">
            <ul id="chapterList">
                <!-- Los capítulos se cargarán aquí vía JavaScript -->
                <li class="loading">Cargando capítulos...</li>
            </ul>
        </nav>

        <section id="contentArea">
            <div class="loading-overlay" id="loadingOverlay">
                <div class="spinner"></div>
            </div>
            <h1 id="chapterTitle">Bienvenido a la Documentación de Osiris</h1>
            <div id="chapterContent">
                <!-- El contenido del capítulo se cargará aquí vía AJAX -->
                <p>Selecciona un capítulo de la izquierda para empezar a previsualizarlo, o usa la barra de búsqueda.</p>
                <p>Esta es una interfaz dinámica para tu documentación, construida con PHP, JavaScript y un toque de magia de Osiris.</p>
                <p>¡Disfruta la experiencia!</p>
            </div>
        </section>
    </main>

    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const sidebar = document.getElementById('sidebar');
            const searchInput = document.getElementById('searchInput');
            const chapterList = document.getElementById('chapterList');
            const contentArea = document.getElementById('contentArea');
            const chapterTitle = document.getElementById('chapterTitle');
            const chapterContent = document.getElementById('chapterContent');
            const loadingOverlay = document.getElementById('loadingOverlay');

            let allChapters = []; // Almacena la lista completa de capítulos

            // Función para mostrar/ocultar el spinner de carga
            const toggleLoading = (show) => {
                if (show) {
                    loadingOverlay.classList.add('active');
                } else {
                    loadingOverlay.classList.remove('active');
                }
            };

            // Función para renderizar el contenido HTML y aplicar resaltado de sintaxis
            const renderContent = (title, content) => {
                chapterTitle.textContent = title;
                chapterContent.innerHTML = content;
                contentArea.scrollTop = 0; // Vuelve al inicio del contenido

                // Aplicar resaltado de sintaxis si hay bloques de código
                document.querySelectorAll('#chapterContent pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
            };

            // Función para cargar un capítulo específico
            const loadChapter = async (filename, skipHistory = false) => {
                toggleLoading(true);
                try {
                    const response = await fetch(`index.php?action=load&chapter=${filename}`);
                    const data = await response.json();

                    if (data.status === 'success') {
                        renderContent(data.title, data.content);
                        // Actualizar el hash de la URL sin recargar
                        if (!skipHistory) {
                            history.pushState({ chapter: filename }, data.title, `#${filename}`);
                        }
                    } else {
                        // Manejo de errores si el archivo no se encuentra o hay problemas
                        renderContent('Error de Carga', `<div class="message-box">${data.message}</div>`);
                    }
                } catch (error) {
                    console.error('Error al cargar el capítulo:', error);
                    renderContent('Error de Conexión', `<div class="message-box">No se pudo cargar el capítulo. Por favor, revisa tu conexión o los logs del servidor.</div>`);
                } finally {
                    toggleLoading(false);
                    // Actualizar el estado 'active' en la lista de capítulos
                    document.querySelectorAll('#chapterList li a').forEach(link => {
                        link.classList.remove('active');
                        if (link.dataset.filename === filename) {
                            link.classList.add('active');
                        }
                    });
                }
            };

            // Función para renderizar la lista de capítulos
            const renderChapterList = (chaptersToRender) => {
                chapterList.innerHTML = ''; // Limpiar lista existente
                if (chaptersToRender.length === 0) {
                    chapterList.innerHTML = '<li><a href="#">No se encontraron capítulos.</a></li>';
                    return;
                }
                chaptersToRender.forEach(chapter => {
                    const listItem = document.createElement('li');
                    const link = document.createElement('a');
                    link.href = `#${chapter.filename}`; // Para enlaces directos
                    link.textContent = chapter.title;
                    link.dataset.filename = chapter.filename; // Almacenar el nombre del archivo
                    link.addEventListener('click', (e) => {
                        e.preventDefault(); // Evitar el comportamiento de enlace predeterminado
                        loadChapter(chapter.filename);
                    });
                    listItem.appendChild(link);
                    chapterList.appendChild(listItem);
                });
            };

            // Función para cargar la lista inicial de capítulos
            const loadChapterList = async () => {
                try {
                    const response = await fetch('index.php?action=list');
                    allChapters = await response.json();
                    renderChapterList(allChapters);

                    // Cargar el capítulo inicial (desde URL o por defecto)
                    const initialChapter = window.location.hash.substring(1);
                    if (initialChapter && allChapters.some(c => c.filename === initialChapter)) {
                        loadChapter(initialChapter, true); // True para no añadir al historial de nuevo
                    } else if (allChapters.length > 0) {
                        // Cargar el primer capítulo si no hay hash o es inválido
                        loadChapter(allChapters[0].filename);
                    } else {
                        renderContent('Sin Documentación', `<div class="message-box success">¡Parece que no hay archivos Markdown en la carpeta 'templates/'!</div>`);
                    }

                } catch (error) {
                    console.error('Error al cargar la lista de capítulos:', error);
                    chapterList.innerHTML = '<li><a href="#" class="message-box">Error al cargar capítulos.</a></li>';
                }
            };

            // Implementación de debounce para la búsqueda
            let searchTimeout;
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.toLowerCase();
                searchTimeout = setTimeout(async () => {
                    if (query.length > 0) {
                        // Realizar búsqueda en el servidor para contenido completo
                        try {
                            toggleLoading(true);
                            const response = await fetch(`index.php?action=search&query=${encodeURIComponent(query)}`);
                            const data = await response.json();
                            toggleLoading(false);
                            if (data.status === 'success') {
                                renderChapterList(data.chapters); // Renderiza solo los capítulos que coinciden
                            } else {
                                renderChapterList([]); // Muestra vacío si hay error
                            }
                        } catch (error) {
                            console.error('Error en la búsqueda:', error);
                            toggleLoading(false);
                            renderChapterList([]);
                        }
                    } else {
                        renderChapterList(allChapters); // Mostrar todos los capítulos si la búsqueda está vacía
                    }
                }, 300); // Debounce de 300ms
            });

            // Manejar cambios en el hash de la URL (navegación del navegador)
            window.addEventListener('hashchange', () => {
                const chapterFromHash = window.location.hash.substring(1);
                if (chapterFromHash && allChapters.some(c => c.filename === chapterFromHash)) {
                    loadChapter(chapterFromHash, true);
                }
            });

            // Iniciar la carga
            loadChapterList();
        });
    </script>
</body>
</html>