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
        "title" => "Goyim Nation of Goys",
        "description" => "Goym World United",
        "image" => "https://goyimz.duckdns.org/img/goyimzh.png"
    ]);
    ?>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>

<style>
    html, body { 
        height: 100%; 
        margin: 0; 
        padding: 0; 
        overflow: hidden; 
        background: #000000; 
        color: #0f0; 
        font-family: 'Courier New', monospace; 
    }
    body { display: flex; flex-direction: column; align-items: center; justify-content: flex-start; }

    #wrapper { 
        width: 95%; 
        max-width: 640px; 
        height: 100vh;
        display: flex; 
        flex-direction: column; 
        padding: 5px 0;
        text-align: center;
    }
    
    .header-img { display: block; max-width: 100%; max-height: 30px; margin: 0 auto 2px auto; flex-shrink: 0; }
    
    .view-modes { display: flex; justify-content: flex-end; gap: 10px; margin-bottom: 5px; flex-shrink: 0; }
    .mode-btn { background: none; border: 1px solid #3a3a3a; color: #b8a840 !important; font-size: 0.7em; cursor: pointer; padding: 2px 6px; border-radius: 3px; transition: 0.3s; }
    .mode-btn:hover { color: #0f0 !important; border-color: #0f0; }
    .mode-btn.active { color: #0f0 !important; border-color: #0f0; background: #052505; }

    #chat-box { 
        background: #0a0a0a; 
        border: 1px solid #333; 
        flex: 1 1 0;
        min-height: 0;
        overflow-y: auto; 
        padding: 10px; 
        margin-bottom: 5px; 
        text-align: left; 
        border-radius: 5px; 
    }
    
    .msg { margin-bottom: 8px; border-bottom: 1px dashed #111; padding-bottom: 4px; white-space: pre-wrap; word-wrap: break-word; }
    .msg a { color: #ffff00; text-decoration: underline; font-weight: bold; }
    .msg a:hover { color: #fff; background: #444000; }
    .server { color: #0f0; }
    .user { color: #ccc; }
    .sys { color: #555; font-size: 0.8em; }

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

    /* ===== WIDGETS FLOTANTES ===== */
    #widget-fab {
        position: fixed; top: 0; left: 0; right: 0;
        display: none; flex-direction: row; flex-wrap: wrap;
        gap: 3px; padding: 3px 8px; align-items: center;
        background: #050505; border-bottom: 1px solid #1a1a1a;
        z-index: 200;
    }
    #widget-fab.has-items { display: flex; }
    body.has-widgets #wrapper { margin-top: 28px; }

    .widget-fab-btn {
        background: #0a0a0a; border: 1px solid #333; color: #b8a840;
        font-size: 0.62em; padding: 2px 8px; cursor: pointer;
        border-radius: 2px; white-space: nowrap;
        font-family: 'Courier New', monospace; transition: 0.15s;
    }
    .widget-fab-btn:hover  { background: #0f0; color: #000; border-color: #0f0; }
    .widget-fab-btn.active { background: #052505; border-color: #0f0; color: #0f0; }
    .widget-fab-btn.stale  { border-color: #333; color: #7a6e20; }

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

    /* TV widget */
    .tv-item { display: flex; align-items: center; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #111; }
    .tv-name { color: #0c0; flex-grow: 1; }
    .tv-btn { background: #000; border: 1px solid #0f0; color: #0f0; font-size: 0.65em; padding: 2px 6px; cursor: pointer; border-radius: 2px; text-decoration: none; }
    .tv-btn:hover { background: #0f0; color: #000; }

    /* Info widget */
    .info-section { margin-bottom: 8px; }
    .info-section h4 { color: #0f0; margin: 4px 0 3px 0; font-size: 0.9em; border-bottom: 1px solid #1a1a1a; padding-bottom: 2px; }
    .info-row { display: flex; justify-content: space-between; padding: 1px 0; }
    .info-label { color: #555; }
    .info-value { color: #0f0; }
    .ram-bar { background: #111; border: 1px solid #222; height: 6px; border-radius: 3px; margin-top: 4px; }
    .ram-bar-fill { height: 100%; border-radius: 3px; transition: width 0.5s; background: #0f0; }
    .ram-bar-fill.warn   { background: #ff0; }
    .ram-bar-fill.danger { background: #f44; }

    /* Models widget */
    .model-item { display: flex; align-items: center; gap: 5px; padding: 4px 2px; border-bottom: 1px solid #111; cursor: pointer; }
    .model-item:hover { background: #0a150a; }
    .model-idx  { color: #333; min-width: 18px; font-size: 0.85em; }
    .model-name { flex-grow: 1; color: #0c0; }
    .model-name.active { color: #fff; font-weight: bold; }
    .mbadge { font-size: 0.6em; padding: 1px 4px; border-radius: 2px; }
    .mb-ram    { background: #002200; border: 1px solid #0f0; color: #0f0; }
    .mb-nofit  { background: #220000; border: 1px solid #f44; color: #f44; }
    .mb-active { background: #003300; border: 1px solid #0f0; color: #0f0; }

    /* ===== /WHO WIDGET ===== */
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
        font-size: 0.65em; padding: 2px 5px; cursor: pointer; border-radius: 2px;
    }
    .who-pm-btn:hover { background: #66f; color: #000; }

    /* ===== CHAT SOCIAL ===== */
    /* Panel de chat reutiliza .widget-panel — solo estilos internos aquí */
    #chat-social-body {
        display: flex; flex-direction: column; gap: 0;
    }
    #chat-social-msgs {
        min-height: 80px; max-height: 220px; overflow-y: auto;
        background: #040404; border: 1px solid #1a1a1a;
        padding: 6px; margin-bottom: 6px; border-radius: 3px;
        font-size: 0.95em;
    }
    .cmsg { padding: 3px 0; border-bottom: 1px solid #0d0d0d; display: flex; gap: 6px; align-items: baseline; }
    .cmsg-from { color: #0a0; font-weight: bold; white-space: nowrap; font-size: 0.85em; }
    .cmsg-from.self { color: #ff0; }
    .cmsg-from.pm   { color: #66f; }
    .cmsg-text { color: #aaa; word-break: break-word; flex: 1; }
    .cmsg-pm-label { font-size: 0.7em; color: #336; padding: 0 3px; border: 1px solid #224; border-radius: 2px; }

    #chat-social-form { display: flex; gap: 4px; }
    #chat-social-input {
        flex: 1; background: #080808; border: 1px solid #1e1e1e;
        color: #0f0; padding: 6px 8px; font-family: inherit; font-size: 0.9em;
        border-radius: 2px;
    }
    #chat-social-input:focus { outline: none; border-color: #0f0; }
    #chat-social-send {
        background: #001a00; border: 1px solid #0f0; color: #0f0;
        padding: 6px 12px; cursor: pointer; font-family: inherit; font-size: 0.85em;
        border-radius: 2px;
    }
    #chat-social-send:hover { background: #0f0; color: #000; }
    #chat-social-clear {
        background: none; border: 1px solid #2a2a2a; color: #444;
        padding: 6px 8px; cursor: pointer; font-size: 0.75em; border-radius: 2px;
    }
    #chat-social-clear:hover { border-color: #f44; color: #f44; }

    .chat-online-bar {
        font-size: 0.7em; color: #333; padding: 3px 0 5px 0;
        display: flex; justify-content: space-between;
    }
    .chat-online-count { color: #0a0; }

    /* ===== TICKER DE PRESENCIA ===== */
    #presence-ticker {
        position: fixed; bottom: 0; left: 0; right: 0;
        height: 18px; overflow: hidden;
        background: rgba(0,0,0,0.85);
        border-top: 1px solid #0d0d0d;
        z-index: 300; pointer-events: none;
        display: none; /* visible solo cuando hay eventos */
    }
    #presence-ticker.visible { display: block; }
    #presence-ticker-inner {
        white-space: nowrap;
        font-size: 0.65em; line-height: 18px;
        padding: 0 8px;
        color: #2a2a2a;
        transition: opacity 2s;
    }
    #presence-ticker-inner.join { color: #0a4a0a; }
    #presence-ticker-inner.leave { color: #3a1a00; }
</style>
    
</head>

<body>
<div id="wrapper">
    <br>
    <div class="view-modes">
       
        <img src="img/goyimzh.png" class="header-img" >  
        <button class="header-img" onclick="setMode('text', this);"> <a href="/search/?" target="_newGoyim" style="color:#a0f0b0;"><img src="img/goys1.png" class="header-img" style="max-height: 20px;width:85px;background:rgba(221,222,221,.1)"></a></button>
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
            <button onclick='cmdRapido("/search");'> <a href="search/index.php" target="_newGoyim" style="all:inherit;"> /buscar </a> </button>
        </div>
    </div>
</div>

<!-- Barra FAB de widgets -->
<div id="widget-fab"></div>
<!-- Contenedor de paneles flotantes -->
<div id="widget-panels"></div>
<!-- Ticker de presencia (entradas/salidas) -->
<div id="presence-ticker"><div id="presence-ticker-inner"></div></div>

<script type="text/javascript">
    let socket;
    let currentMode = 'text';
    let history = []; 
    const chatBox      = document.getElementById('chat-box');
    const messageInput = document.getElementById('message-input');
    
    let activeHost        = window.location.hostname;
    let reconnectInterval = 3000;
    let reconnectTimer    = null;
    let lastServerMsgDiv  = null;
    let lastCommandSent   = "";

    // Mi identidad (se rellena al recibir el widget "welcome")
    let myShortId  = "";
    let myVname    = "";

    // =====================================================================
    // TICKER DE PRESENCIA
    // =====================================================================
    let tickerTimer = null;

    function mostrarTicker(text, type) { // type: "join" | "leave"
        const ticker = document.getElementById('presence-ticker');
        const inner  = document.getElementById('presence-ticker-inner');
        inner.textContent = text;
        inner.className   = type;
        ticker.classList.add('visible');
        if (tickerTimer) clearTimeout(tickerTimer);
        tickerTimer = setTimeout(() => {
            ticker.classList.remove('visible');
        }, 4000);
    }

    // =====================================================================
    // CHAT SOCIAL — estado
    // =====================================================================
    const socialMsgs = [];   // { from, text, pm, self, ts }
    let   onlineCount = 0;
    const MAX_SOCIAL_MSGS = 100;

    function pushSocialMsg(entry) {
        socialMsgs.push(entry);
        if (socialMsgs.length > MAX_SOCIAL_MSGS) socialMsgs.shift();
        _renderSocialMsgs();
        _updateOnlineBar();
    }

    function _renderSocialMsgs() {
        const box = document.getElementById('chat-social-msgs');
        if (!box) return;
        box.innerHTML = socialMsgs.map(m => {
            const isSelf  = m.self || m.from === myVname;
            const isPm    = !!m.pm;
            const fromCls = isPm ? 'cmsg-from pm' : (isSelf ? 'cmsg-from self' : 'cmsg-from');
            const pmLabel = isPm ? `<span class="cmsg-pm-label">PM${m.self ? '→' + escH(m.to) : ''}</span> ` : '';
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

    function iniciarPmDesde(targetId) {
        const inp = document.getElementById('chat-social-input');
        if (inp) { inp.value = `/pm ${targetId} `; inp.focus(); }
    }

    function escH(str) {
        return String(str)
            .replace(/&/g,'&amp;').replace(/</g,'&lt;')
            .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    // =====================================================================
    // SISTEMA DE WIDGETS
    // =====================================================================
    const widgetStore = {};
    const WIDGET_TTL  = 5 * 60 * 1000;
    const WIDGET_LABELS = {
        tv_channels:  '📺 TV',
        servers:      '🌐 Servidores',
        info:         '📊 Info',
        models:       '🤖 Modelos',
        welcome:      '👋 Sesión',
        who:          '👥 Usuarios',
        social_chat:  '💬 Chat'
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

    // Crear el panel de Chat social sin necesidad de widget del servidor
    function _asegurarChatSocial() {
        const id    = 'social_chat';
        const label = '💬 Chat';
        if (!document.getElementById('panel-' + id)) {
            _crearFab(id, label);
            _crearPanel(id);
            _renderPanel(id, label, null);
            _actualizarFab(id, label);
        }
    }

    function _fabBarHeight() {
        const fab = document.getElementById('widget-fab');
        return Math.max(fab ? fab.offsetHeight : 0, 28);
    }

    function _reposicionarPaneles() {
        const top = _fabBarHeight();
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
        if (p)   { p.style.top = _fabBarHeight() + 'px'; p.classList.add('visible'); }
        if (btn) btn.classList.add('active');
    }

    function togglePanel(id) {
        const p = document.getElementById('panel-' + id);
        if (!p) { _asegurarChatSocial(); mostrarPanel(id); return; }
        const wasVisible = p.classList.contains('visible');
        document.querySelectorAll('.widget-panel').forEach(el => el.classList.remove('visible'));
        document.querySelectorAll('.widget-fab-btn').forEach(b => b.classList.remove('active'));
        if (!wasVisible) {
            p.style.top = _fabBarHeight() + 'px';
            p.classList.add('visible');
            const btn = document.getElementById('fab-' + id);
            if (btn) btn.classList.add('active');
            // Enfocar input al abrir el chat
            if (id === 'social_chat') {
                setTimeout(() => { const i = document.getElementById('chat-social-input'); if(i) i.focus(); }, 50);
            }
        }
    }

    function cerrarPanel(id) {
        const p   = document.getElementById('panel-' + id);
        const btn = document.getElementById('fab-' + id);
        if (p)   p.classList.remove('visible');
        if (btn) btn.classList.remove('active');
    }

    function _renderPanel(id, label, data) {
        const p = document.getElementById('panel-' + id);
        if (!p) return;

        if (!p.querySelector('.widget-body')) {
            const ts_el     = document.createElement('span'); ts_el.className = 'widget-ts';
            const close_el  = document.createElement('span'); close_el.className = 'widget-close'; close_el.textContent = '✕';
            close_el.onclick = (e) => { e.stopPropagation(); cerrarPanel(id); };
            const title_right = document.createElement('span');
            title_right.appendChild(ts_el); title_right.appendChild(close_el);
            const title_left = document.createElement('span'); title_left.textContent = label;
            const title = document.createElement('div'); title.className = 'widget-panel-title';
            title.appendChild(title_left); title.appendChild(title_right);
            const body = document.createElement('div'); body.className = 'widget-body';
            p.appendChild(title); p.appendChild(body);
        }

        const ts_el = p.querySelector('.widget-ts');
        if (ts_el && id !== 'social_chat') ts_el.textContent = new Date().toLocaleTimeString();

        let html = '';
        if      (id === 'tv_channels')  html = _renderTV(data);
        else if (id === 'servers')      html = _renderServers(data);
        else if (id === 'info')         html = _renderInfo(data);
        else if (id === 'models')       html = _renderModels(data);
        else if (id === 'welcome')      html = _renderWelcome(data);
        else if (id === 'who')          html = _renderWho(data);
        else if (id === 'social_chat')  { _renderSocialChat(p); return; }

        const body = p.querySelector('.widget-body');
        if (body) body.innerHTML = html;
    }

    // --- Renders de cada widget ---

    function _renderTV(data) {
        if (!data?.channels?.length) return '<p style="color:#555">No hay canales.</p>';
        return data.channels.map(ch =>
            `<div class="tv-item">
                <span class="tv-name">${escH(ch.canal)}</span>
                <a class="tv-btn" href="https://osiris000.duckdns.org/app/mitv/tv/player2.php?chn=${escH(ch.url)}" target="_blank">▶ VER</a>
            </div>`
        ).join('');
    }

    function _renderServers(data) {
        if (!data?.servers?.length) return '<p style="color:#555">No hay servidores.</p>';
        const origin = window.location.hostname;
        return data.servers.map(s => {
            const h = s.host;
            const isCurrent = h === activeHost;
            const isOrigin  = h === origin;
            const label = isCurrent ? '[ACTIVO]' : (isOrigin ? '[ORIGEN]' : '[REMOTO]');
            const style = isCurrent ? 'border-left-color:#ff0;background:#111;' : '';
            return `<div class="server-line" style="${style}">
                <span class="server-url">${escH(h)}</span>
                <span class="server-info" style="${isCurrent ? 'color:#0f0;' : ''}">${label}</span>
                <div class="server-actions">
                    <button class="srv-btn ping-btn" onclick="pingServer('${escH(h)}')">PING</button>
                    <button class="srv-btn" onclick="connectToServer('${escH(h)}')">${isCurrent ? 'RECON.' : 'LINK'}</button>
                </div>
            </div>`;
        }).join('');
    }

    function _renderInfo(data) {
        const sv   = data?.server || {};
        const r    = data?.ram    || {};
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
            return `<div class="model-item" onclick="cmdRapido('/model ${m.index}'); togglePanel('models')">
                <span class="model-idx">${m.index}</span>
                <span class="${nc}">${escH(m.name)}</span>
                ${ram}${act}
            </div>`;
        }).join('');
        return header + items + `<div style="color:#333;font-size:0.72em;margin-top:6px">Pulsa para cambiar de modelo</div>`;
    }

    function _renderWelcome(data) {
        if (!data) return '';
        // Guardar identidad propia
        myShortId = data.id  || '';
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
            const pmBtn  = !isSelf
                ? `<button class="who-pm-btn" onclick="iniciarPmDesde('${escH(u.id)}');togglePanel('social_chat')">PM</button>`
                : '<span style="color:#333;font-size:0.7em">tú</span>';
            return `<div class="who-item">
                <span class="${nc}">${escH(u.vname)}</span>
                <span class="who-meta">${escH(u.since)} · ${u.msgs}msg</span>
                ${busy}${pmBtn}
            </div>`;
        }).join('');
        return items + `<div style="color:#333;font-size:0.7em;margin-top:6px;text-align:right">${data.users.length} conectado(s)</div>`;
    }

    // El chat social se construye como HTML estático con IDs fijos, no como innerHTML
    function _renderSocialChat(panel) {
        const body = panel.querySelector('.widget-body');
        if (!body) return;
        // Solo construir la estructura una vez
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
                <input id="chat-social-input" type="text" placeholder="Escribe aquí… · /pm &lt;id&gt; &lt;msg&gt; para privado" autocomplete="off">
                <button id="chat-social-send" onclick="enviarChatSocial()">↩</button>
                <button id="chat-social-clear" title="Limpiar historial local" onclick="limpiarChatSocial()">🗑</button>
            </div>
            <div style="color:#333;font-size:0.68em;margin-top:5px">
                Privados: escribe <b style="color:#336">/pm id mensaje</b> (id sin @server)
            </div>`;
        // Enter en el input del chat
        document.getElementById('chat-social-input').addEventListener('keydown', e => {
            if (e.key === 'Enter') { e.preventDefault(); enviarChatSocial(); }
        });
        _renderSocialMsgs();
        _updateOnlineBar();
    }

    // Refresco de badges cada minuto
    setInterval(() => {
        Object.keys(widgetStore).forEach(id => _actualizarFab(id, WIDGET_LABELS[id] || id));
        _actualizarFab('social_chat', '💬 Chat');
    }, 60000);

    // =====================================================================
    // LÓGICA ORIGINAL DE CHAT IA (íntegra, sin cambios excepto onmessage)
    // =====================================================================

    marked.use({
        renderer: {
            link(href, title, text) {
                return `<a target="_blank" href="${href}">${text}</a>`;
            }
        }
    });

    function escaparHTML(str) {
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
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

    function isURL(str) {
        const pattern = /[a-zA-Z0-9.-]+\.[a-zA-Z]{2,63}/;
        return pattern.test(str.trim());
    }

    function pingServer(url) {
        if (url !== activeHost) {
            render(`>>> AVISO: Estás conectado a ${activeHost}. Para pinguear ${url} primero pulsa LINK.`, "sys");
            return;
        }
        render(`>>> PING ENVIADO A ${activeHost}...`, "sys");
        socket.send(`/info`);
        socket.send(`/way`);
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
                const url = match[0];
                const isCurrent   = (url === activeHost);
                const isHostOrigin = (url === originalHost);
                let label = isHostOrigin ? "[ORIGEN]" : "[REMOTO]";
                if (isCurrent) label = "[ACTIVO]";
                htmlResponse += `
                <div class="server-line" style="${isCurrent ? 'border-left-color: #ffff00; background: #111;' : ''}">
                    <span class="server-url">${url}</span>
                    <span class="server-info" style="${isCurrent ? 'color: #0f0;' : ''}">${label}</span>
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
            history.push({text: parsedHTML, type: 'server_html'});
            renderToDOM(parsedHTML, 'server_html');
            lastCommandSent = ""; 
            return;
        }

        if (type !== 'server' || text.includes("📺") || text.includes(">>>")) {
            lastServerMsgDiv = null; 
            history.push({text, type});
            renderToDOM(text, type);
            return;
        }

        if (text === '\n') { lastServerMsgDiv = null; return; }

        if (lastServerMsgDiv && type === 'server') {
            history[history.length - 1].text += text;
            updateDOM(lastServerMsgDiv, history[history.length - 1].text);
        } else {
            history.push({text, type});
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

    function conectar(targetHost) {
        const host = targetHost || activeHost;
        if (reconnectTimer) clearTimeout(reconnectTimer);

        socket = new WebSocket('wss://' + host + '/ws/');
        
        socket.onopen = () => { 
            render(">>> ENLACE ESTABLECIDO CON: " + host, "sys");
            // Crear el panel de chat social al conectar
            _asegurarChatSocial();
        };

        // ─────────────────────────────────────────────────────────────────
        // onmessage: distingue widget / presencia / chat / pm / texto plano
        // ─────────────────────────────────────────────────────────────────
        socket.onmessage = (e) => {
            if (!e.data || e.data.length === 0) return;
            try {
                const obj = JSON.parse(e.data);

                // Widget del servidor (info, models, tv, etc.)
                if (obj.type === 'widget') {
                    procesarWidget(obj);
                    return;
                }

                // Presencia: entrada/salida de usuarios
                if (obj.type === 'presence') {
                    onlineCount = obj.clients || 0;
                    _actualizarFab('social_chat', '💬 Chat');
                    _updateOnlineBar();
                    if (obj.event === 'join') {
                        mostrarTicker(`⬤ ${obj.id} se ha conectado  ·  ${onlineCount} en línea`, 'join');
                    } else if (obj.event === 'leave') {
                        mostrarTicker(`○ ${obj.id} se ha desconectado  ·  ${onlineCount} en línea`, 'leave');
                    }
                    return;
                }

                // Mensaje de chat común
                if (obj.type === 'chat') {
                    pushSocialMsg({ from: obj.from, text: obj.text, ts: Date.now() });
                    // Notificación discreta si el panel está cerrado
                    const panel = document.getElementById('panel-social_chat');
                    if (!panel || !panel.classList.contains('visible')) {
                        _actualizarFab('social_chat', '💬 Chat ●');
                    }
                    return;
                }

                // Mensaje privado (recibido o eco propio)
                if (obj.type === 'pm') {
                    pushSocialMsg({
                        from: obj.from,
                        text: obj.text,
                        to:   obj.to,
                        pm:   true,
                        self: !!obj.self,
                        ts:   Date.now()
                    });
                    if (!document.getElementById('panel-social_chat')?.classList.contains('visible')) {
                        mostrarTicker(`✉ PM de ${obj.from}`, 'join');
                    }
                    return;
                }

                // Error del chat (sin interferir con el chat IA)
                if (obj.type === 'chat_error') {
                    pushSocialMsg({ from: '⚠', text: obj.text, ts: Date.now() });
                    return;
                }

            } catch (_) {}

            // Texto plano → pipeline normal de IA
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
        if(e) e.preventDefault();
        const msg = messageInput.value.trim();
        if (msg && socket && socket.readyState === WebSocket.OPEN) {
            lastCommandSent = msg;
            lastServerMsgDiv = null;
            socket.send(msg);
            render("TÚ: " + msg, "user");
            messageInput.value = "";
        }
        return false;
    }

    render(">>> ESCRIBIR /help Para Ayuda", "sys");
    conectar(activeHost);
</script>
</body>
</html>