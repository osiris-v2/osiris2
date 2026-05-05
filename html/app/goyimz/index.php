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
    $html = "\n";
    $html .= '<meta property="og:type" content="website">' . "\n";
    $html .= '<meta property="og:url" content="' . htmlspecialchars($card['url']) . '">' . "\n";
    $html .= '<meta property="og:title" content="' . htmlspecialchars($card['title']) . '">' . "\n";
    $html .= '<meta property="og:description" content="' . htmlspecialchars($card['description']) . '">' . "\n";
    $html .= '<meta property="og:image" content="' . htmlspecialchars($card['image']) . '">' . "\n";
    $html .= '<meta property="og:site_name" content="' . htmlspecialchars($card['site_name']) . '">' . "\n";
    $html .= '<meta name="twitter:card" content="' . htmlspecialchars($card['card_type']) . '">' . "\n";
    $html .= '<meta name="twitter:title" content="' . htmlspecialchars($card['title']) . '">' . "\n";
    $html .= '<meta name="twitter:description" content="' . htmlspecialchars($card['description']) . '">' . "\n";
    $html .= '<meta name="twitter:image" content="' . htmlspecialchars($card['image']) . '">' . "\n";
    return $html;
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="initial-scale=1, maximum-scale=1">
    <?php
    echo makecard([
        "title"       => "Goyim Nation of Goys",
        "description" => "Goym World United",
        "image"       => "https://goyimz.duckdns.org/img/goyimzh.png"
    ]);
    ?>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
/* ─── BASE ─── */
html, body {
    height: 100%; margin: 0; padding: 0; overflow: hidden;
    background: #000; color: #0f0; font-family: 'Courier New', monospace;
}
body { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; }

#wrapper {
    width: 95%; max-width: 640px; height: 100vh;
    display: flex; flex-direction: column; padding: 5px 0; text-align: center;
}
.header-img { display: block; max-width: 100%; max-height: 30px; margin: 0 auto 2px auto; flex-shrink: 0; }
.view-modes { display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 5px; flex-shrink: 0; }
.mode-btn { background: none; border: 1px solid #3a3a3a; color: #b8a840 !important; font-size: 0.7em; cursor: pointer; padding: 2px 6px; border-radius: 3px; transition: 0.3s; }
.mode-btn:hover { color: #0f0 !important; border-color: #0f0; }
.mode-btn.active { color: #0f0 !important; border-color: #0f0; background: #052505; }

#chat-box {
    background: #0a0a0a; border: 1px solid #333;
    flex: 1 1 0; min-height: 0; overflow-y: auto;
    padding: 10px; margin-bottom: 5px; text-align: left; border-radius: 5px;
}
.msg { margin-bottom: 8px; border-bottom: 1px dashed #111; padding-bottom: 4px; white-space: pre-wrap; word-wrap: break-word; }
.msg a { color: #ffff00; text-decoration: underline; font-weight: bold; }
.msg a:hover { color: #fff; background: #444000; }
.server { color: #0f0; }
.user   { color: #ccc; }
.sys    { color: #555; font-size: 0.8em; }

#chat-form { display: flex; gap: 5px; flex-shrink: 0; }
input { flex-grow: 1; background: #111; border: 1px solid #333; color: #0f0; padding: 10px; font-family: inherit; }
button#send-btn { background: #0f0; border: none; padding: 10px 20px; cursor: pointer; font-weight: bold; }

#command-drawer { width: 100%; margin-top: 5px; flex-shrink: 0; padding-bottom: 5px; }
.drawer-btn { background: none; border: 1px solid #2a2a2a; color: #666; font-size: 0.7em; cursor: pointer; padding: 4px; width: 100%; border-radius: 3px; }
#quick-commands { display: none; flex-wrap: wrap; gap: 5px; padding: 10px; background: #050505; border: 1px solid #222; margin-top: -1px; }
#quick-commands button { background: #111; border: 1px solid #333; color: #0c0; font-size: 0.75em; padding: 4px 8px; cursor: pointer; }
#quick-commands button:hover { background: #0f0; color: #000; }
.show { display: flex !important; }

.server-line { display: flex; align-items: center; justify-content: space-between; background: #080808; padding: 5px; margin: 2px 0; border-left: 2px solid #0f0; }
.server-url { font-weight: bold; flex-grow: 1; font-size: 0.85em; }
.server-info { font-size: 0.7em; color: #555; margin-right: 10px; }
.server-actions { display: flex; gap: 5px; }
.srv-btn { background: #000; border: 1px solid #0f0; color: #0f0; font-size: 0.65em; padding: 2px 5px; cursor: pointer; border-radius: 2px; }
.srv-btn:hover { background: #0f0; color: #000; }
.srv-btn.ping-btn { border-color: #ffff00; color: #ffff00; }

/* ─── FAB BAR ─── */
#widget-fab {
    position: fixed; top: 0; left: 0; right: 0;
    display: none; flex-direction: row; flex-wrap: wrap;
    gap: 3px; padding: 3px 8px; align-items: center;
    background: #050505; border-bottom: 1px solid #1a1a1a; z-index: 200;
}
#widget-fab.has-items { display: flex; }
body.has-widgets #wrapper { margin-top: 28px; }

.widget-fab-btn {
    background: #0a0a0a; border: 1px solid #333; color: #b8a840;
    font-size: 0.62em; padding: 2px 8px; cursor: pointer;
    border-radius: 2px; white-space: nowrap;
    font-family: 'Courier New', monospace; transition: 0.15s; position: relative;
}
.widget-fab-btn:hover  { background: #0f0; color: #000; border-color: #0f0; }
.widget-fab-btn.active { background: #052505; border-color: #0f0; color: #0f0; }
.widget-fab-btn.stale  { border-color: #333; color: #7a6e20; }

/* Piloto de notificación en el botón FAB */
.fab-notif-dot {
    position: absolute; top: -3px; right: -3px;
    width: 7px; height: 7px; border-radius: 50%;
    background: #f44; border: 1px solid #000;
    animation: blink-dot 0.9s infinite;
    display: none;
}
.fab-notif-dot.on { display: block; }
@keyframes blink-dot { 0%,100%{ opacity:1; } 50%{ opacity:0.15; } }

/* ─── WIDGET PANELS ─── */
.widget-panel {
    display: none; position: fixed; left: 0; right: 0;
    max-height: calc(100vh - 120px); overflow-y: auto;
    background: #080808; border-bottom: 2px solid #0f0;
    z-index: 199; padding: 10px 14px;
    font-size: 0.78em; box-shadow: 0 6px 24px #0f04;
    pointer-events: none;
}
.widget-panel.visible { display: block; }
.widget-panel .widget-panel-title,
.widget-panel .widget-body { pointer-events: all; }
.widget-panel-title {
    color: #0f0; font-weight: bold; margin-bottom: 6px;
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid #1a1a1a; padding-bottom: 4px;
}
.widget-close { cursor: pointer; color: #444; padding: 0 4px; font-size: 1.1em; }
.widget-close:hover { color: #f00; }
.widget-ts { font-size: 0.75em; color: #333; }

/* ─── TV WIDGET con visor embebido ─── */
#tv-embed-bar {
    position: fixed; left: 0; right: 0; z-index: 198;
    background: #000; border-bottom: 2px solid #0a3a0a;
    display: none; flex-direction: column;
}
#tv-embed-bar.visible { display: flex; }
#tv-embed-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 2px 8px; background: #030f03; font-size: 0.7em; color: #0a0;
    flex-shrink: 0;
}
#tv-embed-title { color: #0c0; font-weight: bold; }
#tv-embed-close {
    cursor: pointer; color: #444; font-size: 1.1em; padding: 0 4px;
    border: 1px solid #1a1a1a; border-radius: 2px; background: #050505;
}
#tv-embed-close:hover { color: #f00; border-color: #f00; }
#tv-embed-frame { width: 100%; border: none; display: block; flex-shrink: 0; }

/* Modo selector en TV widget */
.tv-mode-bar {
    display: flex; gap: 6px; margin-bottom: 8px; align-items: center;
    padding: 4px 0; border-bottom: 1px solid #111;
}
.tv-mode-lbl { color: #333; font-size: 0.8em; margin-right: 4px; }
.tv-mode-btn {
    background: #0a0a0a; border: 1px solid #2a2a2a; color: #555;
    font-size: 0.72em; padding: 2px 8px; cursor: pointer; border-radius: 2px;
}
.tv-mode-btn.active { border-color: #0f0; color: #0f0; background: #031403; }
.tv-mode-btn:hover  { border-color: #0f0; color: #0c0; }

.tv-item { display: flex; align-items: center; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #111; }
.tv-name { color: #0c0; flex-grow: 1; }
.tv-btn { background: #000; border: 1px solid #0f0; color: #0f0; font-size: 0.65em; padding: 2px 6px; cursor: pointer; border-radius: 2px; text-decoration: none; }
.tv-btn:hover { background: #0f0; color: #000; }

/* ─── INFO WIDGET ─── */
.info-section { margin-bottom: 8px; }
.info-section h4 { color: #0f0; margin: 4px 0 3px 0; font-size: 0.9em; border-bottom: 1px solid #1a1a1a; padding-bottom: 2px; }
.info-row { display: flex; justify-content: space-between; padding: 1px 0; }
.info-label { color: #555; }
.info-value { color: #0f0; }
.ram-bar { background: #111; border: 1px solid #222; height: 6px; border-radius: 3px; margin-top: 4px; }
.ram-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s; background: #0f0; }
.ram-bar-fill.warn   { background: #ff0; }
.ram-bar-fill.danger { background: #f44; }

/* ─── MODELS WIDGET ─── */
.model-item { display: flex; align-items: center; gap: 5px; padding: 4px 2px; border-bottom: 1px solid #111; cursor: pointer; }
.model-item:hover { background: #0a150a; }
.model-idx  { color: #333; min-width: 18px; font-size: 0.85em; }
.model-name { flex-grow: 1; color: #0c0; }
.model-name.active { color: #fff; font-weight: bold; }
.mbadge { font-size: 0.6em; padding: 1px 4px; border-radius: 2px; }
.mb-ram    { background: #002200; border: 1px solid #0f0; color: #0f0; }
.mb-nofit  { background: #220000; border: 1px solid #f44; color: #f44; }
.mb-active { background: #003300; border: 1px solid #0f0; color: #0f0; }

/* ─── WHO WIDGET ─── */
.who-item {
    display: flex; align-items: center; gap: 6px;
    padding: 5px 3px; border-bottom: 1px solid #111;
}
.who-vname { flex-grow: 1; color: #0c0; font-size: 0.9em; }
.who-vname.self { color: #fff; font-weight: bold; }
.who-meta  { color: #444; font-size: 0.75em; }
.who-busy  { font-size: 0.65em; padding: 1px 4px; border-radius: 2px; background: #300; border: 1px solid #f44; color: #f44; }
.who-pm-btn {
    background: #0a0a0a; border: 1px solid #336; color: #66f;
    font-size: 0.65em; padding: 2px 7px; cursor: pointer; border-radius: 2px;
    transition: 0.15s;
}
.who-pm-btn:hover { background: #66f; color: #000; border-color: #66f; }

/* ─── VENTANAS PRIVADAS DE PM ─── */
/*
   Cada ventana PM es un .pm-window, flotante, redimensionable verticalmente.
   Se apilan con z-index dinámico. Las activas tienen borde verde, las con
   notificación pendiente tienen borde rojo parpadeante.
*/
.pm-window {
    position: fixed; right: 8px; width: 290px;
    background: #060606; border: 1px solid #1a1a1a;
    border-radius: 4px; box-shadow: 0 4px 20px #0008;
    z-index: 250; display: flex; flex-direction: column;
    font-size: 0.76em; font-family: 'Courier New', monospace;
    transition: border-color 0.2s;
    max-height: 340px; min-height: 160px;
}
.pm-window.focused { border-color: #0f0; }
.pm-window.notify  { border-color: #f44; animation: pm-blink 0.7s infinite; }
@keyframes pm-blink { 0%,100%{ border-color:#f44; } 50%{ border-color:#300; } }

.pm-win-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 4px 8px; background: #090909;
    border-bottom: 1px solid #111; border-radius: 4px 4px 0 0;
    cursor: pointer; flex-shrink: 0;
}
.pm-win-title { color: #66f; font-size: 0.9em; font-weight: bold; }
.pm-win-title.notify { color: #f44; }
.pm-win-actions { display: flex; gap: 4px; align-items: center; }
.pm-win-min {
    color: #555; cursor: pointer; font-size: 1em; padding: 0 3px;
    border: 1px solid #1a1a1a; border-radius: 2px; line-height: 1;
}
.pm-win-min:hover  { color: #ff0; border-color: #ff0; }
.pm-win-close { color: #444; cursor: pointer; font-size: 1em; padding: 0 3px; border: 1px solid #1a1a1a; border-radius: 2px; }
.pm-win-close:hover { color: #f00; border-color: #f00; }

/* Piloto de notificación en la cabecera de la ventana PM */
.pm-notif-dot {
    width: 7px; height: 7px; border-radius: 50%; background: #f44;
    border: 1px solid #000; flex-shrink: 0;
    animation: blink-dot 0.7s infinite; display: none;
}
.pm-notif-dot.on { display: block; }

.pm-win-msgs {
    flex: 1 1 0; min-height: 0; overflow-y: auto;
    padding: 6px 8px; background: #040404;
    display: flex; flex-direction: column; gap: 3px;
}
.pm-msg { display: flex; gap: 5px; align-items: baseline; }
.pm-msg-from { font-weight: bold; white-space: nowrap; flex-shrink: 0; }
.pm-msg-from.me   { color: #ff0; }
.pm-msg-from.them { color: #66f; }
.pm-msg-text { color: #aaa; word-break: break-word; }

.pm-win-form { display: flex; gap: 3px; padding: 4px 6px; background: #070707; border-top: 1px solid #111; flex-shrink: 0; }
.pm-win-input {
    flex: 1; background: #050505; border: 1px solid #1a1a1a;
    color: #0f0; padding: 4px 6px; font-family: inherit; font-size: 0.95em;
    border-radius: 2px;
}
.pm-win-input:focus { outline: none; border-color: #336; }
.pm-win-send {
    background: #050515; border: 1px solid #336; color: #66f;
    padding: 4px 10px; cursor: pointer; border-radius: 2px; font-size: 0.9em;
}
.pm-win-send:hover { background: #66f; color: #000; }

/* Minimizado */
.pm-window.minimized .pm-win-msgs,
.pm-window.minimized .pm-win-form { display: none; }
.pm-window.minimized { min-height: 0; }

/* ─── CHAT SOCIAL ─── */
#chat-social-msgs {
    min-height: 80px; max-height: 220px; overflow-y: auto;
    background: #040404; border: 1px solid #1a1a1a;
    padding: 6px; margin-bottom: 6px; border-radius: 3px; font-size: 0.95em;
}
.cmsg { padding: 3px 0; border-bottom: 1px solid #0d0d0d; display: flex; gap: 6px; align-items: baseline; }
.cmsg-from { color: #0a0; font-weight: bold; white-space: nowrap; font-size: 0.85em; }
.cmsg-from.self { color: #ff0; }
.cmsg-pm-label { font-size: 0.7em; color: #336; padding: 0 3px; border: 1px solid #224; border-radius: 2px; }
.cmsg-text { color: #aaa; word-break: break-word; flex: 1; }

#chat-social-form { display: flex; gap: 4px; }
#chat-social-input {
    flex: 1; background: #080808; border: 1px solid #1e1e1e;
    color: #0f0; padding: 6px 8px; font-family: inherit; font-size: 0.9em; border-radius: 2px;
}
#chat-social-input:focus { outline: none; border-color: #0f0; }
#chat-social-send {
    background: #001a00; border: 1px solid #0f0; color: #0f0;
    padding: 6px 12px; cursor: pointer; font-family: inherit; font-size: 0.85em; border-radius: 2px;
}
#chat-social-send:hover { background: #0f0; color: #000; }
#chat-social-clear {
    background: none; border: 1px solid #2a2a2a; color: #444;
    padding: 6px 8px; cursor: pointer; font-size: 0.75em; border-radius: 2px;
}
#chat-social-clear:hover { border-color: #f44; color: #f44; }
.chat-online-bar { font-size: 0.7em; color: #333; padding: 3px 0 5px 0; display: flex; justify-content: space-between; }
.chat-online-count { color: #0a0; }

/* ─── TICKER DE PRESENCIA ─── */
#presence-ticker {
    position: fixed; bottom: 0; left: 0; right: 0;
    height: 18px; overflow: hidden; background: rgba(0,0,0,0.85);
    border-top: 1px solid #0d0d0d; z-index: 300; pointer-events: none; display: none;
}
#presence-ticker.visible { display: block; }
#presence-ticker-inner {
    white-space: nowrap; font-size: 0.65em; line-height: 18px;
    padding: 0 8px; color: #2a2a2a;
}
#presence-ticker-inner.join  { color: #0a4a0a; }
#presence-ticker-inner.leave { color: #3a1a00; }
</style>
</head>

<body>
<div id="wrapper">
    <br>
    <div class="view-modes">
        <img src="img/goyimzh.png" class="header-img">
        <button class="header-img" onclick="setMode('text', this);">
            <a href="/search/?" target="_newGoyim" style="color:#a0f0b0;">
                <img src="img/goys1.png" class="header-img" style="max-height:20px;width:85px;background:rgba(221,222,221,.1)">
            </a>
        </button>
        <button class="mode-btn active" onclick="setMode('text', this)">TEXT</button>
        <button class="mode-btn" onclick="setMode('md', this)">MD</button>
    </div>

    <div id="chat-box"></div>

    <form id="chat-form" onsubmit="enviarMensaje(event); return false;">
        <input type="text" id="message-input" placeholder="Comando o pregunta a la IA..." required autocomplete="off">
        <button type="submit" id="send-btn">></button>
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
            <button onclick="cmdRapido('/stop')">/stop</button>
            <button onclick="cmdRapido('/clearcontext')">/clearcontext</button>
            <button onclick='cmdRapido("/search");'>
                <a href="search/index.php" target="_newGoyim" style="all:inherit;">/buscar</a>
            </button>
        </div>
    </div>
</div>

<!-- Barra FAB de widgets -->
<div id="widget-fab"></div>
<!-- Contenedor de paneles flotantes -->
<div id="widget-panels"></div>

<!-- Visor TV embebido (iframe fijo arriba, bajo la FAB bar) -->
<div id="tv-embed-bar">
    <div id="tv-embed-header">
        <span>📺 </span>
        <span id="tv-embed-title">—</span>
        <span id="tv-embed-close" onclick="cerrarTvEmbed()" title="Cerrar visor">✕</span>
    </div>
    <iframe id="tv-embed-frame" src="" scrolling="no" allowfullscreen></iframe>
</div>

<!-- Ticker de presencia -->
<div id="presence-ticker"><div id="presence-ticker-inner"></div></div>

<!-- Contenedor de ventanas PM privadas (gestionadas por JS) -->
<div id="pm-windows-container"></div>

<script>
/* ═══════════════════════════════════════════════════════════════════════
   ESTADO GLOBAL
═══════════════════════════════════════════════════════════════════════ */
let socket;
let currentMode       = 'text';
let history           = [];
const chatBox         = document.getElementById('chat-box');
const messageInput    = document.getElementById('message-input');
let activeHost        = window.location.hostname;
let reconnectInterval = 3000;
let reconnectTimer    = null;
let lastServerMsgDiv  = null;
let lastCommandSent   = "";

// Identidad propia (rellena al recibir widget "welcome")
let myShortId = "";
let myVname   = "";

/* ═══════════════════════════════════════════════════════════════════════
   TICKER DE PRESENCIA
═══════════════════════════════════════════════════════════════════════ */
let tickerTimer = null;

function mostrarTicker(text, type) {
    const ticker = document.getElementById('presence-ticker');
    const inner  = document.getElementById('presence-ticker-inner');
    inner.textContent = text;
    inner.className   = type;
    ticker.classList.add('visible');
    if (tickerTimer) clearTimeout(tickerTimer);
    tickerTimer = setTimeout(() => ticker.classList.remove('visible'), 4500);
}

/* ═══════════════════════════════════════════════════════════════════════
   CHAT SOCIAL — canal común
═══════════════════════════════════════════════════════════════════════ */
const socialMsgs   = [];
let   onlineCount  = 0;
const MAX_SOCIAL   = 100;

function pushSocialMsg(entry) {
    socialMsgs.push(entry);
    if (socialMsgs.length > MAX_SOCIAL) socialMsgs.shift();
    _renderSocialMsgs();
    _updateOnlineBar();
}

function _renderSocialMsgs() {
    const box = document.getElementById('chat-social-msgs');
    if (!box) return;
    box.innerHTML = socialMsgs.map(m => {
        const isSelf  = m.self || m.from === myVname;
        const isPm    = !!m.pm;
        const fromCls = isSelf ? 'cmsg-from self' : 'cmsg-from';
        const pmLabel = isPm ? `<span class="cmsg-pm-label">PM</span> ` : '';
        return `<div class="cmsg">${pmLabel}<span class="${fromCls}">${escH(m.from)}</span><span class="cmsg-text">${escH(m.text)}</span></div>`;
    }).join('');
    box.scrollTop = box.scrollHeight;
}

function _updateOnlineBar() {
    const el = document.getElementById('chat-online-count-el');
    if (el) el.textContent = onlineCount + ' en línea';
}

function enviarChatSocial() {
    const inp = document.getElementById('chat-social-input');
    if (!inp) return;
    const text = inp.value.trim();
    if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: 'chat', text }));
    inp.value = '';
}

function limpiarChatSocial() {
    socialMsgs.length = 0;
    _renderSocialMsgs();
}

function escH(str) {
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ═══════════════════════════════════════════════════════════════════════
   VENTANAS PRIVADAS DE PM
   - Una ventana por par de conversación (keyed por short_id del otro)
   - Cada una tiene su historial local
   - Piloto rojo parpadeante cuando hay mensajes no leídos
   - Se apilan verticalmente desde la esquina inferior derecha
═══════════════════════════════════════════════════════════════════════ */
const pmWindows = {};        // { [peerId]: { el, msgs, minimized, unread } }
let   pmZBase   = 250;
const PM_WIN_H  = 320;       // altura cuando abierta
const PM_WIN_GAP = 6;        // espacio entre ventanas

function _pmStackBottom(idx) {
    // Posiciona la ventana idx desde abajo, apilando de a PM_WIN_H
    // idx 0 = la más reciente (más abajo)
    return 20 + idx * (PM_WIN_H + PM_WIN_GAP);
}

function _reapilaPM() {
    const ids = Object.keys(pmWindows);
    ids.forEach((id, i) => {
        const win = pmWindows[id];
        win.el.style.bottom = _pmStackBottom(i) + 'px';
    });
}

/** Abre (o focaliza) una ventana PM con un peer. */
function abrirPM(peerId, peerVname) {
    if (pmWindows[peerId]) {
        // Ya existe: desminimizar y focalizar
        const win = pmWindows[peerId];
        win.el.classList.remove('minimized', 'notify');
        win.el.classList.add('focused');
        win.unread = 0;
        _actualizarPMtitle(peerId);
        _limpiarNotifPM(peerId);
        win.el.querySelector('.pm-win-input').focus();
        return;
    }

    const win = { msgs: [], minimized: false, unread: 0, peerVname };
    const idx = Object.keys(pmWindows).length;
    pmWindows[peerId] = win;

    const el = document.createElement('div');
    el.className = 'pm-window focused';
    el.id        = `pm-win-${peerId}`;
    el.style.bottom = _pmStackBottom(idx) + 'px';
    el.style.zIndex = pmZBase + idx;
    el.innerHTML = `
        <div class="pm-win-header" onclick="toggleMinPM('${escH(peerId)}')">
            <span class="pm-notif-dot" id="pm-dot-${escH(peerId)}"></span>
            <span class="pm-win-title" id="pm-title-${escH(peerId)}">✉ ${escH(peerVname)}</span>
            <div class="pm-win-actions">
                <span class="pm-win-min" title="Minimizar" onclick="event.stopPropagation();toggleMinPM('${escH(peerId)}')">─</span>
                <span class="pm-win-close" title="Cerrar" onclick="event.stopPropagation();cerrarPM('${escH(peerId)}')">✕</span>
            </div>
        </div>
        <div class="pm-win-msgs" id="pm-msgs-${escH(peerId)}"></div>
        <div class="pm-win-form">
            <input class="pm-win-input" type="text" placeholder="Mensaje privado…" autocomplete="off"
                   id="pm-inp-${escH(peerId)}">
            <button class="pm-win-send" onclick="enviarPM('${escH(peerId)}')">↩</button>
        </div>`;

    // Enter para enviar
    el.querySelector('.pm-win-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); enviarPM(peerId); }
    });
    // Click en la ventana la trae al frente
    el.addEventListener('mousedown', () => focusPM(peerId));

    win.el = el;
    document.getElementById('pm-windows-container').appendChild(el);
    _reapilaPM();
    el.querySelector('.pm-win-input').focus();
}

function toggleMinPM(peerId) {
    const win = pmWindows[peerId];
    if (!win) return;
    win.minimized = !win.minimized;
    win.el.classList.toggle('minimized', win.minimized);
    if (!win.minimized) {
        // Al restaurar, limpiar notificación
        win.unread = 0;
        win.el.classList.remove('notify');
        _actualizarPMtitle(peerId);
        _limpiarNotifPM(peerId);
        focusPM(peerId);
    }
}

function cerrarPM(peerId) {
    const win = pmWindows[peerId];
    if (!win) return;
    win.el.remove();
    delete pmWindows[peerId];
    _reapilaPM();
    // Limpiar piloto en FAB /who si existiera
    _limpiarNotifPM(peerId);
}

function focusPM(peerId) {
    // Trae la ventana al frente subiendo su z-index
    pmZBase++;
    const win = pmWindows[peerId];
    if (win) win.el.style.zIndex = pmZBase;
    // Quitar notify si estaba
    win.el.classList.remove('notify');
    win.unread = 0;
    _actualizarPMtitle(peerId);
    _limpiarNotifPM(peerId);
}

function enviarPM(peerId) {
    const win = pmWindows[peerId];
    if (!win) return;
    const inp  = document.getElementById(`pm-inp-${peerId}`);
    const text = inp?.value.trim();
    if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;
    // Enviar al servidor via chat con sintaxis /pm
    socket.send(JSON.stringify({ type: 'chat', text: `/pm ${peerId} ${text}` }));
    inp.value = '';
    // El eco lo añade el onmessage cuando recibe {type:"pm", self:true}
}

/** Recibe un PM entrante y lo añade a la ventana correcta. */
function recibirPM(obj) {
    // Determinar si soy el remitente (eco) o el receptor
    const isSelf  = !!obj.self;
    const peerId  = isSelf
        ? (obj.to.replace('@server',''))   // eco: la otra parte es el to
        : (obj.from.replace('@server','')); // recibido: la otra parte es el from
    const peerVname = isSelf ? obj.to : obj.from;

    // Si la ventana no existe y soy el receptor, la creamos (con notificación)
    if (!pmWindows[peerId]) {
        abrirPM(peerId, peerVname);
    }

    const win = pmWindows[peerId];
    win.msgs.push({ from: isSelf ? myVname : obj.from, text: obj.text, self: isSelf });

    // Renderizar
    const box = document.getElementById(`pm-msgs-${peerId}`);
    if (box) {
        const div = document.createElement('div');
        div.className = 'pm-msg';
        div.innerHTML = `<span class="pm-msg-from ${isSelf ? 'me' : 'them'}">${escH(isSelf ? 'yo' : obj.from)}</span><span class="pm-msg-text">${escH(obj.text)}</span>`;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    }

    // Si la ventana está minimizada o sin foco (notify)
    if (!isSelf) {
        if (win.minimized || !win.el.classList.contains('focused')) {
            win.unread++;
            win.el.classList.add('notify');
            win.el.classList.remove('focused');
            _actualizarPMtitle(peerId);
            _encenderNotifPM(peerId);
            // Ticker de aviso
            mostrarTicker(`✉ PM de ${obj.from}`, 'join');
        }
    }
}

function _actualizarPMtitle(peerId) {
    const win = pmWindows[peerId];
    if (!win) return;
    const titleEl = document.getElementById(`pm-title-${peerId}`);
    if (!titleEl) return;
    const badge = win.unread > 0 ? ` [${win.unread}]` : '';
    titleEl.textContent = `✉ ${win.peerVname}${badge}`;
    titleEl.className   = win.unread > 0 ? 'pm-win-title notify' : 'pm-win-title';
}

/** Enciende el piloto rojo en el botón FAB del usuario (/who) */
function _encenderNotifPM(peerId) {
    const dot = document.getElementById(`pm-dot-${peerId}`);
    if (dot) dot.classList.add('on');
    // También en el FAB de quien
    const fabDot = document.getElementById(`who-dot-${peerId}`);
    if (fabDot) fabDot.classList.add('on');
}

function _limpiarNotifPM(peerId) {
    const dot = document.getElementById(`pm-dot-${peerId}`);
    if (dot) dot.classList.remove('on');
    const fabDot = document.getElementById(`who-dot-${peerId}`);
    if (fabDot) fabDot.classList.remove('on');
}

/* ═══════════════════════════════════════════════════════════════════════
   TV VISOR EMBEBIDO
═══════════════════════════════════════════════════════════════════════ */
let tvMode = 'embed'; // 'embed' | 'window'

function setTvMode(mode, btn) {
    tvMode = mode;
    document.querySelectorAll('.tv-mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}

function abrirCanal(url, nombre) {
    const fullUrl = `https://osiris000.duckdns.org/app/mitv/tv/player2.php?chn=${encodeURIComponent(url)}`;
    if (tvMode === 'window') {
        window.open(fullUrl, '_blank');
        return;
    }
    // Modo embebido
    const bar   = document.getElementById('tv-embed-bar');
    const frame = document.getElementById('tv-embed-frame');
    const title = document.getElementById('tv-embed-title');
    frame.src   = fullUrl;
    title.textContent = nombre;
    bar.classList.add('visible');
    _ajustarLayoutTV();
    // El panel de TV queda visible detrás (debajo del iframe)
}

function cerrarTvEmbed() {
    const bar   = document.getElementById('tv-embed-bar');
    const frame = document.getElementById('tv-embed-frame');
    frame.src   = '';
    bar.classList.remove('visible');
    _ajustarLayoutTV();
}

function _ajustarLayoutTV() {
    const bar    = document.getElementById('tv-embed-bar');
    const isOpen = bar.classList.contains('visible');
    const fabH   = _fabBarHeight();

    if (isOpen) {
        // iframe bajo la FAB: ocupa ~35% de la pantalla
        const ifrH = Math.floor(window.innerHeight * 0.35);
        const frame = document.getElementById('tv-embed-frame');
        frame.style.height = ifrH + 'px';
        bar.style.top = fabH + 'px';

        // Los paneles de widgets se posicionan debajo del iframe
        const panelTop = fabH + bar.offsetHeight;
        document.querySelectorAll('.widget-panel').forEach(p => { p.style.top = panelTop + 'px'; });
    } else {
        // Sin iframe: paneles vuelven debajo de la FAB
        _reposicionarPaneles();
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   SISTEMA DE WIDGETS
═══════════════════════════════════════════════════════════════════════ */
const widgetStore = {};
const WIDGET_TTL  = 5 * 60 * 1000;
const WIDGET_LABELS = {
    tv_channels: '📺 TV',
    servers:     '🌐 Servidores',
    info:        '📊 Info',
    models:      '🤖 Modelos',
    welcome:     '👋 Sesión',
    who:         '👥 Usuarios',
    social_chat: '💬 Chat'
};

function procesarWidget(obj) {
    const id    = obj.widget;
    const label = WIDGET_LABELS[id] || id;
    const isNew = !widgetStore[id];
    widgetStore[id] = { data: obj.data, timestamp: Date.now() };
    if (isNew) { _crearFab(id, label); _crearPanel(id); }
    _renderPanel(id, label, obj.data);
    _actualizarFab(id, label);
    mostrarPanel(id);
}

function _asegurarChatSocial() {
    const id = 'social_chat';
    if (!document.getElementById('panel-' + id)) {
        _crearFab(id, WIDGET_LABELS[id]);
        _crearPanel(id);
        _renderPanel(id, WIDGET_LABELS[id], null);
        _actualizarFab(id, WIDGET_LABELS[id]);
    }
}

function _fabBarHeight() {
    const fab = document.getElementById('widget-fab');
    return Math.max(fab ? fab.offsetHeight : 0, 28);
}

function _reposicionarPaneles() {
    const bar    = document.getElementById('tv-embed-bar');
    const isTV   = bar.classList.contains('visible');
    const top    = isTV ? (_fabBarHeight() + bar.offsetHeight) : _fabBarHeight();
    document.querySelectorAll('.widget-panel').forEach(p => { p.style.top = top + 'px'; });
}

function _crearFab(id, label) {
    const fab = document.getElementById('widget-fab');
    const btn = document.createElement('button');
    btn.className = 'widget-fab-btn';
    btn.id        = 'fab-' + id;
    btn.onclick   = (e) => { e.stopPropagation(); _reposicionarPaneles(); togglePanel(id); };
    fab.appendChild(btn);
    fab.classList.add('has-items');
    document.body.classList.add('has-widgets');
    requestAnimationFrame(_reposicionarPaneles);
}

function _actualizarFab(id, label) {
    const btn = document.getElementById('fab-' + id);
    if (!btn) return;
    if (id === 'social_chat') {
        const cnt = onlineCount > 0 ? ` (${onlineCount})` : '';
        btn.textContent = label + cnt;
        btn.title = 'Canal de chat común';
        return;
    }
    const stale = (Date.now() - (widgetStore[id]?.timestamp || 0)) > WIDGET_TTL;
    btn.textContent = label + (stale ? ' ⚠' : ' ●');
    btn.classList.toggle('stale', stale);
    btn.title = stale ? 'Datos desactualizados' : 'Datos frescos';
}

function _crearPanel(id) {
    const div = document.createElement('div');
    div.className = 'widget-panel';
    div.id        = 'panel-' + id;
    div.style.top = _fabBarHeight() + 'px';
    document.getElementById('widget-panels').appendChild(div);
}

function mostrarPanel(id) {
    document.querySelectorAll('.widget-panel').forEach(p => p.classList.remove('visible'));
    document.querySelectorAll('.widget-fab-btn').forEach(b => b.classList.remove('active'));
    const p   = document.getElementById('panel-' + id);
    const btn = document.getElementById('fab-' + id);
    if (p)   { _reposicionarPaneles(); p.classList.add('visible'); }
    if (btn) btn.classList.add('active');
}

function togglePanel(id) {
    const p = document.getElementById('panel-' + id);
    if (!p) { _asegurarChatSocial(); mostrarPanel(id); return; }
    const wasVisible = p.classList.contains('visible');
    document.querySelectorAll('.widget-panel').forEach(el => el.classList.remove('visible'));
    document.querySelectorAll('.widget-fab-btn').forEach(b => b.classList.remove('active'));
    if (!wasVisible) {
        _reposicionarPaneles();
        p.classList.add('visible');
        const btn = document.getElementById('fab-' + id);
        if (btn) btn.classList.add('active');
        if (id === 'social_chat') {
            setTimeout(() => { const i = document.getElementById('chat-social-input'); if(i) i.focus(); }, 50);
        }
    }
}

function cerrarPanel(id) {
    document.getElementById('panel-' + id)?.classList.remove('visible');
    document.getElementById('fab-' + id)?.classList.remove('active');
}

function _renderPanel(id, label, data) {
    const p = document.getElementById('panel-' + id);
    if (!p) return;

    if (!p.querySelector('.widget-body')) {
        const ts_el    = document.createElement('span'); ts_el.className = 'widget-ts';
        const close_el = document.createElement('span'); close_el.className = 'widget-close'; close_el.textContent = '✕';
        close_el.onclick = (e) => { e.stopPropagation(); cerrarPanel(id); };
        const right = document.createElement('span');
        right.appendChild(ts_el); right.appendChild(close_el);
        const left = document.createElement('span'); left.textContent = label;
        const title = document.createElement('div'); title.className = 'widget-panel-title';
        title.appendChild(left); title.appendChild(right);
        const body = document.createElement('div'); body.className = 'widget-body';
        p.appendChild(title); p.appendChild(body);
    }

    const ts_el = p.querySelector('.widget-ts');
    if (ts_el && id !== 'social_chat') ts_el.textContent = new Date().toLocaleTimeString();

    if (id === 'social_chat') { _renderSocialChat(p); return; }

    let html = '';
    if      (id === 'tv_channels') html = _renderTV(data);
    else if (id === 'servers')     html = _renderServers(data);
    else if (id === 'info')        html = _renderInfo(data);
    else if (id === 'models')      html = _renderModels(data);
    else if (id === 'welcome')     html = _renderWelcome(data);
    else if (id === 'who')         html = _renderWho(data);

    const body = p.querySelector('.widget-body');
    if (body) body.innerHTML = html;
}

/* ─── RENDERS ─── */

function _renderTV(data) {
    if (!data?.channels?.length) return '<p style="color:#555">No hay canales.</p>';

    const modeBar = `
        <div class="tv-mode-bar">
            <span class="tv-mode-lbl">Modo:</span>
            <button class="tv-mode-btn ${tvMode==='embed'?'active':''}" onclick="setTvMode('embed',this)">📺 Embebido</button>
            <button class="tv-mode-btn ${tvMode==='window'?'active':''}" onclick="setTvMode('window',this)">🔲 Ventana nueva</button>
        </div>`;

    const items = data.channels.map(ch => `
        <div class="tv-item">
            <span class="tv-name">${escH(ch.canal)}</span>
            <button class="tv-btn" onclick="abrirCanal('${escH(ch.url)}','${escH(ch.canal)}')">▶ VER</button>
        </div>`).join('');

    return modeBar + items;
}

function _renderServers(data) {
    if (!data?.servers?.length) return '<p style="color:#555">No hay servidores.</p>';
    const origin = window.location.hostname;
    return data.servers.map(s => {
        const h         = s.host;
        const isCurrent = h === activeHost;
        const isOrigin  = h === origin;
        const label     = isCurrent ? '[ACTIVO]' : (isOrigin ? '[ORIGEN]' : '[REMOTO]');
        const style     = isCurrent ? 'border-left-color:#ff0;background:#111;' : '';
        return `<div class="server-line" style="${style}">
            <span class="server-url">${escH(h)}</span>
            <span class="server-info" style="${isCurrent?'color:#0f0;':''}">${label}</span>
            <div class="server-actions">
                <button class="srv-btn ping-btn" onclick="pingServer('${escH(h)}')">PING</button>
                <button class="srv-btn" onclick="connectToServer('${escH(h)}')">${isCurrent?'RECON.':'LINK'}</button>
            </div>
        </div>`;
    }).join('');
}

function _renderInfo(data) {
    const sv   = data?.server  || {};
    const r    = data?.ram     || {};
    const sess = data?.session || {};
    const pct  = r.used_pct || 0;
    const cls  = pct > 85 ? 'danger' : pct > 65 ? 'warn' : '';
    const inRam = (data?.models_in_ram || []).join(', ') || 'ninguno';
    return `
    <div class="info-section" style="text-align:center;color:#0f0;font-size:1.05em;padding:4px 0 6px">${escH(data?.datetime||'')}</div>
    <div class="info-section">
        <h4>🖥️ Servidor</h4>
        <div class="info-row"><span class="info-label">Uptime</span><span class="info-value">${escH(sv.uptime||'')}</span></div>
        <div class="info-row"><span class="info-label">Uptime OS</span><span class="info-value">${escH(sv.uptime_os||'')}</span></div>
        <div class="info-row"><span class="info-label">Clientes</span><span class="info-value">${sv.clients||0}</span></div>
        <div class="info-row"><span class="info-label">IA activas</span><span class="info-value">${sv.ai_active||0}/${sv.ai_max||0}</span></div>
    </div>
    <div class="info-section">
        <h4>💾 RAM</h4>
        <div class="info-row"><span class="info-label">Usada</span><span class="info-value">${r.used_mb||0}MB/${r.total_mb||0}MB (${pct}%)</span></div>
        <div class="info-row"><span class="info-label">Libre</span><span class="info-value">${r.available_mb||0}MB</span></div>
        <div class="ram-bar"><div class="ram-bar-fill ${cls}" style="width:${pct}%"></div></div>
        <div class="info-row" style="margin-top:4px"><span class="info-label">En RAM</span><span class="info-value" style="font-size:0.82em">${escH(inRam)}</span></div>
    </div>
    <div class="info-section">
        <h4>👤 Tu sesión</h4>
        <div class="info-row"><span class="info-label">ID</span><span class="info-value">${escH(sess.vname||sess.id||'')}</span></div>
        <div class="info-row"><span class="info-label">Modelo</span><span class="info-value">${escH(sess.model||'')}</span></div>
        <div class="info-row"><span class="info-label">Conectado</span><span class="info-value">${escH(sess.connected_since||'')}</span></div>
        <div class="info-row"><span class="info-label">Mensajes</span><span class="info-value">${sess.messages||0}</span></div>
        <div class="info-row"><span class="info-label">Ctx turnos</span><span class="info-value">${sess.context_turns||0}</span></div>
    </div>`;
}

function _renderModels(data) {
    if (!data?.models?.length) return '<p style="color:#555">No hay modelos.</p>';
    const header = `<div style="color:#444;font-size:0.85em;margin-bottom:6px">RAM libre: ${data.ram_available_mb}MB / ${data.ram_total_mb}MB</div>`;
    const items  = data.models.map(m => {
        const nc  = m.active ? 'model-name active' : 'model-name';
        const ram = m.in_ram ? '<span class="mbadge mb-ram">RAM</span>' : (!m.fits_ram ? '<span class="mbadge mb-nofit">⚠RAM</span>' : '');
        const act = m.active ? '<span class="mbadge mb-active">✓</span>' : '';
        return `<div class="model-item" onclick="cmdRapido('/model ${m.index}');togglePanel('models')">
            <span class="model-idx">${m.index}</span>
            <span class="${nc}">${escH(m.name)}</span>${ram}${act}
        </div>`;
    }).join('');
    return header + items + `<div style="color:#333;font-size:0.72em;margin-top:6px">Pulsa para cambiar de modelo</div>`;
}

function _renderWelcome(data) {
    if (!data) return '';
    myShortId = data.id    || '';
    myVname   = data.vname || (data.id + '@server');
    return `<div style="padding:4px">
        <div style="color:#0f0;font-size:1.1em;font-weight:bold">${escH(myVname)}</div>
        <div style="margin:4px 0">Modelo: <span style="color:#0f0;font-weight:bold">${escH(data.model||'')}</span></div>
        <div style="color:#444;font-size:0.85em">${escH(data.message||'')}</div>
    </div>`;
}

function _renderWho(data) {
    if (!data?.users?.length) return '<p style="color:#555">Nadie conectado.</p>';
    const items = data.users.map(u => {
        const isSelf = u.id === myShortId;
        const nc     = isSelf ? 'who-vname self' : 'who-vname';
        const busy   = u.busy ? '<span class="who-busy">IA</span>' : '';
        // Piloto de notificación de PM junto al botón
        const dot    = `<span class="pm-notif-dot" id="who-dot-${escH(u.id)}" style="display:inline-block;margin-right:3px;vertical-align:middle"></span>`;
        const pmBtn  = !isSelf
            ? `${dot}<button class="who-pm-btn" onclick="abrirPM('${escH(u.id)}','${escH(u.vname)}');cerrarPanel('who')">💬 PM</button>`
            : '<span style="color:#333;font-size:0.7em">tú</span>';
        return `<div class="who-item">
            <span class="${nc}">${escH(u.vname)}</span>
            <span class="who-meta">${escH(u.since)} · ${u.msgs}msg</span>
            ${busy}${pmBtn}
        </div>`;
    }).join('');
    return items + `<div style="color:#333;font-size:0.7em;margin-top:6px;text-align:right">${data.users.length} conectado(s) · pulsa 💬 PM para chat privado</div>`;
}

function _renderSocialChat(panel) {
    const body = panel.querySelector('.widget-body');
    if (!body) return;
    if (body.querySelector('#chat-social-msgs')) {
        _renderSocialMsgs();
        _updateOnlineBar();
        return;
    }
    body.innerHTML = `
        <div class="chat-online-bar">
            <span>Canal común · todos los conectados</span>
            <span class="chat-online-count" id="chat-online-count-el">${onlineCount} en línea</span>
        </div>
        <div id="chat-social-msgs"></div>
        <div id="chat-social-form">
            <input id="chat-social-input" type="text" placeholder="Escribe aquí… · texto libre para todos" autocomplete="off">
            <button id="chat-social-send" onclick="enviarChatSocial()">↩</button>
            <button id="chat-social-clear" title="Limpiar historial local" onclick="limpiarChatSocial()">🗑</button>
        </div>
        <div style="color:#333;font-size:0.68em;margin-top:5px">
            Para mensajes privados abre la lista 👥 Usuarios y pulsa <b style="color:#336">💬 PM</b>
        </div>`;
    document.getElementById('chat-social-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); enviarChatSocial(); }
    });
    _renderSocialMsgs();
    _updateOnlineBar();
}

// Refresco de badges cada minuto
setInterval(() => {
    Object.keys(widgetStore).forEach(id => _actualizarFab(id, WIDGET_LABELS[id] || id));
    _actualizarFab('social_chat', WIDGET_LABELS.social_chat);
}, 60000);

/* ═══════════════════════════════════════════════════════════════════════
   LÓGICA ORIGINAL DE CHAT IA
═══════════════════════════════════════════════════════════════════════ */
marked.use({
    renderer: {
        link(href, title, text) {
            return `<a target="_blank" href="${href}">${text}</a>`;
        }
    }
});

function escaparHTML(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function toggleDrawer() {
    document.getElementById('quick-commands').classList.toggle('show');
}

function cmdRapido(cmd) {
    messageInput.value = cmd;
    enviarMensaje();
}

function setMode(mode, btn) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    refreshChat();
}

function refreshChat() {
    chatBox.innerHTML = "";
    history.forEach(m => renderToDOM(m.text, m.type));
}

function pingServer(url) {
    if (url !== activeHost) {
        render(`>>> AVISO: Estás conectado a ${activeHost}. Para pinguear ${url} primero pulsa LINK.`, "sys");
        return;
    }
    render(`>>> PING ENVIADO A ${activeHost}...`, "sys");
    socket.send('/info');
    socket.send('/way');
}

function connectToServer(url) {
    if (url === activeHost && socket && socket.readyState === WebSocket.OPEN) {
        render(">>> YA ESTÁS CONECTADO A ESTE NODO", "sys");
        return;
    }
    activeHost = url;
    render(`>>> CAMBIANDO DESTINO PREDETERMINADO A: ${activeHost}`, "sys");
    if (socket) { socket.onclose = null; socket.close(); }
    conectar(activeHost);
}

function parseServers(text) {
    const lines = text.split('\n');
    let htmlResponse = "";
    const originalHost = window.location.hostname;
    lines.forEach(line => {
        const cleanLine = line.trim();
        const match = cleanLine.match(/[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}/);
        if (match) {
            const url         = match[0];
            const isCurrent   = (url === activeHost);
            const isHostOrigin = (url === originalHost);
            let label = isHostOrigin ? "[ORIGEN]" : "[REMOTO]";
            if (isCurrent) label = "[ACTIVO]";
            htmlResponse += `
            <div class="server-line" style="${isCurrent ? 'border-left-color:#ffff00;background:#111;' : ''}">
                <span class="server-url">${url}</span>
                <span class="server-info" style="${isCurrent ? 'color:#0f0;' : ''}">${label}</span>
                <div class="server-actions">
                    <button class="srv-btn ping-btn" onclick="pingServer('${url}')">PING</button>
                    <button class="srv-btn" onclick="connectToServer('${url}')">${isCurrent ? 'RECONECTAR' : 'LINK'}</button>
                </div>
            </div>`;
        } else if (cleanLine !== "") {
            htmlResponse += `<div>${line}</div>`;
        }
    });
    return htmlResponse;
}

function render(text, type = 'server') {
    if (type === 'server' && lastCommandSent === "/servers") {
        const parsedHTML = parseServers(text);
        history.push({ text: parsedHTML, type: 'server_html' });
        renderToDOM(parsedHTML, 'server_html');
        lastCommandSent = "";
        return;
    }
    if (type !== 'server' || text.includes("📺") || text.includes(">>>")) {
        lastServerMsgDiv = null;
        history.push({ text, type });
        renderToDOM(text, type);
        return;
    }
    if (text === '\n') { lastServerMsgDiv = null; return; }
    if (lastServerMsgDiv && type === 'server') {
        history[history.length - 1].text += text;
        updateDOM(lastServerMsgDiv, history[history.length - 1].text);
    } else {
        history.push({ text, type });
        lastServerMsgDiv = renderToDOM(text, type);
    }
    if (text.includes("\n")) lastServerMsgDiv = null;
}

function renderToDOM(text, type) {
    const div = document.createElement('div');
    div.className = 'msg ' + (type === 'server_html' ? 'server' : type);
    updateDOM(div, text, type);
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div;
}

function updateDOM(div, text, type = 'server') {
    if (type === 'server_html') {
        div.innerHTML = text;
    } else if (type === 'server') {
        if (currentMode === 'md') div.innerHTML = marked.parse(escaparHTML(text));
        else div.textContent = text;
    } else {
        div.textContent = text;
    }
    chatBox.scrollTop = chatBox.scrollHeight;
}

/* ═══════════════════════════════════════════════════════════════════════
   WEBSOCKET
═══════════════════════════════════════════════════════════════════════ */
function conectar(targetHost) {
    const host = targetHost || activeHost;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    socket = new WebSocket('wss://' + host + '/ws/');

    socket.onopen = () => {
        render(">>> ENLACE ESTABLECIDO CON: " + host, "sys");
        _asegurarChatSocial();
    };

    socket.onmessage = (e) => {
        if (!e.data || e.data.length === 0) return;
        try {
            const obj = JSON.parse(e.data);

            if (obj.type === 'widget') {
                procesarWidget(obj);
                return;
            }

            if (obj.type === 'presence') {
                onlineCount = obj.clients || 0;
                _actualizarFab('social_chat', WIDGET_LABELS.social_chat);
                _updateOnlineBar();
                if (obj.event === 'join')  mostrarTicker(`⬤ ${obj.id} se ha conectado  ·  ${onlineCount} en línea`, 'join');
                if (obj.event === 'leave') mostrarTicker(`○ ${obj.id} se ha desconectado  ·  ${onlineCount} en línea`, 'leave');
                return;
            }

            if (obj.type === 'chat') {
                pushSocialMsg({ from: obj.from, text: obj.text, ts: Date.now() });
                const panel = document.getElementById('panel-social_chat');
                if (!panel || !panel.classList.contains('visible')) {
                    const btn = document.getElementById('fab-social_chat');
                    if (btn) btn.textContent = '💬 Chat ●';
                }
                return;
            }

            // PM: va a la ventana privada dedicada, NO al chat común
            if (obj.type === 'pm') {
                recibirPM(obj);
                return;
            }

            if (obj.type === 'chat_error') {
                pushSocialMsg({ from: '⚠', text: obj.text, ts: Date.now() });
                return;
            }

        } catch (_) {}

        // Texto plano → pipeline IA normal
        render(e.data, "server");
    };

    socket.onclose = () => {
        render(`>>> CONEXIÓN PERDIDA EN ${activeHost} - REINTENTANDO...`, "sys");
        lastServerMsgDiv = null;
        reconnectTimer = setTimeout(() => conectar(activeHost), reconnectInterval);
    };

    socket.onerror = () => {
        render(">>> ERROR DE NODO EN " + host, "sys");
    };
}

function enviarMensaje(e) {
    if (e) e.preventDefault();
    const msg = messageInput.value.trim();
    if (msg && socket && socket.readyState === WebSocket.OPEN) {
        lastCommandSent  = msg;
        lastServerMsgDiv = null;
        socket.send(msg);
        render("TÚ: " + msg, "user");
        messageInput.value = "";
    }
    return false;
}

// Ajustar layout si se redimensiona la ventana
window.addEventListener('resize', () => {
    const bar = document.getElementById('tv-embed-bar');
    if (bar.classList.contains('visible')) _ajustarLayoutTV();
    else _reposicionarPaneles();
});

render(">>> ESCRIBIR /help Para Ayuda", "sys");
conectar(activeHost);
</script>
</body>
</html>