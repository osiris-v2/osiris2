<?php
function makecard($params = []) {
    $defaults = [
        "title"       => "Mi Sitio Web",
        "description" => "Bienvenido a mi página personal.",
        "image"       => "https://tusitio.com/default-image.jpg",
        "url"         => (isset($_SERVER['HTTPS']) ? "https" : "http") . "://$_SERVER[HTTP_HOST]$_SERVER[REQUEST_URI]",
        "site_name"   => "Mi Marca",
        "twitter_id"  => "@tu_usuario",
        "card_type"   => "summary_large_image"
    ];
    $card = array_merge($defaults, $params);
    $html  = "\n";
    $html .= '<meta property="og:type" content="website">' . "\n";
    $html .= '<meta property="og:url" content="'         . htmlspecialchars($card['url'])         . '">' . "\n";
    $html .= '<meta property="og:title" content="'       . htmlspecialchars($card['title'])       . '">' . "\n";
    $html .= '<meta property="og:description" content="' . htmlspecialchars($card['description']) . '">' . "\n";
    $html .= '<meta property="og:image" content="'       . htmlspecialchars($card['image'])       . '">' . "\n";
    $html .= '<meta property="og:site_name" content="'   . htmlspecialchars($card['site_name'])   . '">' . "\n";
    $html .= '<meta name="twitter:card" content="'        . htmlspecialchars($card['card_type'])   . '">' . "\n";
    $html .= '<meta name="twitter:title" content="'       . htmlspecialchars($card['title'])       . '">' . "\n";
    $html .= '<meta name="twitter:description" content="' . htmlspecialchars($card['description']) . '">' . "\n";
    $html .= '<meta name="twitter:image" content="'       . htmlspecialchars($card['image'])       . '">' . "\n";
    return $html;
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <?php
    echo makecard([
        "title"       => "Goyim Nation of Goys",
        "description" => "Goym World United",
        "image"       => "https://goyimz.duckdns.org/img/goyimzh.png"
    ]);
    ?>
    <link rel="stylesheet" href="style.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>

<body>

<!-- ═══════════════════════════════════════════
     WRAPPER PRINCIPAL (chat IA)
═══════════════════════════════════════════ -->
<div id="wrapper">
    <br>
    <div class="view-modes">
        <img src="img/goyimzh.png" class="header-img" alt="logo">
        <button class="header-img">
            <a href="/search/?" target="_newGoyim" style="color:#a0f0b0;">
                <img src="img/goys1.png" class="header-img"
                     style="max-height:20px;width:85px;background:rgba(221,222,221,.1)" alt="buscar">
            </a>
        </button>
        <button class="mode-btn active" onclick="setMode('text', this)">TEXT</button>
        <button class="mode-btn"        onclick="setMode('md',   this)">MD</button>
    </div>

    <div id="chat-box"></div>

    <form id="chat-form" onsubmit="enviarMensaje(event); return false;">
        <input type="text" id="message-input"
               placeholder="Comando o pregunta a la IA…" required autocomplete="off">
        <button type="submit" id="send-btn">›</button>
    </form>

    <div id="command-drawer">
        <button class="drawer-btn" onclick="toggleDrawer()">[+] COMANDOS RÁPIDOS</button>
        <div id="quick-commands">
            <button onclick="cmdRapido('/help')">/help</button>
            <button onclick="cmdRapido('/listtv')">/listtv</button>
            <button onclick="cmdRapido('/servers')">/servers</button>
            <button onclick="cmdRapido('/info')">/info</button>
            <button onclick="cmdRapido('/way')">/way</button>
            <button onclick="cmdRapido('/models')">/models</button>
            <button onclick="cmdRapido('/limit')">/limit</button>
            <button onclick="cmdRapido('/who')">/who</button>
            <button onclick="togglePanel('social_chat')">💬 Chat</button>
            <button onclick="togglePanel('posts')">📢 Posts</button>
            <button onclick="cmdRapido('/stop')">/stop</button>
            <button onclick="cmdRapido('/clearcontext')">/clearcontext</button>
            <button>
                <a href="search/index.php" target="_newGoyim" style="all:inherit;">/buscar</a>
            </button>
        </div>
    </div>
</div>

<!-- ═══════════════════════════════════════════
     FAB BAR — barra superior de paneles
═══════════════════════════════════════════ -->
<div id="widget-fab"></div>

<!-- ═══════════════════════════════════════════
     TV EMBED — iframe fijo con resize handle
═══════════════════════════════════════════ -->
<div id="tv-embed-bar">
    <div id="tv-embed-header">
        <span>📺</span>
        <span id="tv-embed-title">—</span>
        <span id="tv-embed-resize" title="Arrastrar para redimensionar">⠿</span>
        <span id="tv-embed-close" onclick="cerrarTvEmbed()" title="Cerrar visor">✕</span>
    </div>
    <iframe id="tv-embed-frame" src="" scrolling="no" allowfullscreen></iframe>
</div>

<!-- ═══════════════════════════════════════════
     WIDGET PANELS — contenedor
═══════════════════════════════════════════ -->
<div id="widget-panels"></div>

<!-- ═══════════════════════════════════════════
     VENTANAS PM — draggables
═══════════════════════════════════════════ -->
<div id="pm-windows-container"></div>

<!-- ═══════════════════════════════════════════
     TICKER DE PRESENCIA
═══════════════════════════════════════════ -->
<div id="presence-ticker">
    <div id="presence-ticker-inner"></div>
</div>

<script src="app.js"></script>
</body>
</html>
