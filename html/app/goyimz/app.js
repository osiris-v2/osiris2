/* ═══════════════════════════════════════════════════════════════════════
   GOYIM AI — app.js  (v2 — identidad, perfiles, salas, ayuda)
═══════════════════════════════════════════════════════════════════════ */

/* ─── ESTADO GLOBAL ─── */
let socket;
let currentMode       = 'text';
let history           = [];
let activeHost        = window.location.hostname;
let reconnectInterval = 3000;
let reconnectTimer    = null;
let lastServerMsgDiv  = null;
let lastCommandSent   = "";
let myShortId         = "";
let myVname           = "";
let myUsername        = "";          // @usuario si está registrado
let myUserId          = null;
let onlineCount       = 0;

// Salas en las que participa el usuario: { room_id: { name, msgs:[] } }
const misRooms = {};

const chatBox      = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');

/* ═══════════════════════════════════════════════════════════════════════
   UTILIDADES
═══════════════════════════════════════════════════════════════════════ */
function escH(str) {
    return String(str)
        .replace(/&/g,'&amp;').replace(/</g,'&lt;')
        .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function fmtTime(ts) {
    const d = new Date(ts);
    return d.getHours().toString().padStart(2,'0') + ':' + d.getMinutes().toString().padStart(2,'0');
}

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
const socialMsgs = [];
const MAX_SOCIAL  = 100;

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
        const fromCls = isSelf ? 'cmsg-from self' : 'cmsg-from';
        return `<div class="cmsg"><span class="${fromCls}">${escH(m.from)}</span><span class="cmsg-text">${escH(m.text)}</span></div>`;
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

/* ═══════════════════════════════════════════════════════════════════════
   SALAS PRIVADAS
═══════════════════════════════════════════════════════════════════════ */
function recibirRoomMsg(obj) {
    const roomId = obj.room_id;
    if (!misRooms[roomId]) {
        misRooms[roomId] = { name: roomId, msgs: [] };
    }
    misRooms[roomId].msgs.push({ from: obj.from, text: obj.text, ts: Date.now() });
    if (misRooms[roomId].msgs.length > 200) misRooms[roomId].msgs.shift();
    _renderRoomMsgs(roomId);

    // Badge en FAB si el panel no está visible
    const btn = document.getElementById('fab-salas');
    const panel = document.getElementById('panel-salas');
    if (btn && !panel?.classList.contains('visible')) {
        btn.textContent = '🏠 Salas ●';
        btn.classList.add('notif');
    }
    // Sonido visual: mostrar ticker
    mostrarTicker(`[${roomId}] ${obj.from}: ${obj.text}`, 'join');
}

function recibirRoomInvite(obj) {
    mostrarTicker(`📨 Invitación: ${obj.text}`, 'join');
    // Mostrar notificación en el chat IA
    render(`📨 INVITACIÓN A SALA: ${obj.text}`, 'sys');
    // Actualizar widget de salas si está abierto
    if (document.getElementById('panel-salas')?.classList.contains('visible')) {
        _renderWidgetSalas();
    }
}

function _renderRoomMsgs(roomId) {
    const box = document.getElementById(`room-msgs-${roomId}`);
    if (!box) return;
    const msgs = misRooms[roomId]?.msgs || [];
    box.innerHTML = msgs.map(m => {
        const isSelf = m.from === myVname || m.from === ('@' + myUsername);
        return `<div class="cmsg">
            <span class="cmsg-from ${isSelf?'self':''}">${escH(m.from)}</span>
            <span class="cmsg-text">${escH(m.text)}</span>
        </div>`;
    }).join('');
    box.scrollTop = box.scrollHeight;
}

function enviarMsgSala(roomId) {
    const inp = document.getElementById(`room-inp-${roomId}`);
    if (!inp) return;
    const text = inp.value.trim();
    if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: 'room_msg', room_id: roomId, text }));
    inp.value = '';
    // Echo local
    if (!misRooms[roomId]) misRooms[roomId] = { name: roomId, msgs: [] };
    misRooms[roomId].msgs.push({ from: myVname || 'yo', text, ts: Date.now() });
    _renderRoomMsgs(roomId);
}

function _renderWidgetSalas() {
    const body = document.querySelector('#panel-salas .widget-body');
    if (!body) return;

    // Invitaciones pendientes (si el server las envía por presencia, las mostramos)
    const rooms = Object.keys(misRooms);

    let html = `
    <div class="sala-section">
        <div class="sala-section-title">⚡ Acciones</div>
        <div class="sala-actions">
            <input id="sala-nueva-nombre" type="text" placeholder="Nombre de la sala…" class="sala-input">
            <button class="sala-btn" onclick="crearSala()">+ Crear sala</button>
        </div>
        <div class="sala-actions" style="margin-top:6px">
            <input id="sala-inv-id" type="text" placeholder="ID sala (sala-xxxx)…" class="sala-input" style="width:45%">
            <input id="sala-inv-user" type="text" placeholder="Usuario a invitar…" class="sala-input" style="width:45%">
            <button class="sala-btn" onclick="invitarASala()">📨 Invitar</button>
        </div>
        <div class="sala-actions" style="margin-top:6px">
            <input id="sala-aceptar-id" type="text" placeholder="ID sala a aceptar…" class="sala-input">
            <button class="sala-btn accent" onclick="aceptarSala()">✅ Aceptar inv.</button>
        </div>
    </div>`;

    if (rooms.length === 0) {
        html += `<div style="color:#555;font-size:0.85em;padding:8px 0">Sin salas activas. Crea una o acepta una invitación.</div>`;
    } else {
        rooms.forEach(roomId => {
            const room = misRooms[roomId];
            html += `
            <div class="sala-card" id="sala-card-${escH(roomId)}">
                <div class="sala-card-header">
                    <span class="sala-card-title">🏠 ${escH(room.name || roomId)}</span>
                    <span class="sala-card-id">${escH(roomId)}</span>
                    <button class="sala-btn-sm danger" onclick="salirDeSala('${escH(roomId)}')">Salir</button>
                </div>
                <div class="room-msgs" id="room-msgs-${escH(roomId)}"></div>
                <div class="room-form">
                    <input class="sala-input" id="room-inp-${escH(roomId)}" type="text" placeholder="Mensaje…" autocomplete="off">
                    <button class="sala-btn-sm" onclick="enviarMsgSala('${escH(roomId)}')">↩</button>
                </div>
            </div>`;
        });
    }

    body.innerHTML = html;

    // Rebind inputs de sala (Enter para enviar)
    rooms.forEach(roomId => {
        const inp = document.getElementById(`room-inp-${roomId}`);
        if (inp) inp.addEventListener('keydown', e => {
            if (e.key === 'Enter') { e.preventDefault(); enviarMsgSala(roomId); }
        });
        _renderRoomMsgs(roomId);
    });

    // Bind sala nueva input
    const inpNueva = document.getElementById('sala-nueva-nombre');
    if (inpNueva) inpNueva.addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); crearSala(); }
    });
}

function crearSala() {
    const inp = document.getElementById('sala-nueva-nombre');
    const nombre = inp ? inp.value.trim() : '';
    const cmd = nombre ? `/sala crear ${nombre}` : '/sala crear';
    cmdRapido(cmd);
    if (inp) inp.value = '';
}

function invitarASala() {
    const id   = document.getElementById('sala-inv-id')?.value.trim();
    const user = document.getElementById('sala-inv-user')?.value.trim();
    if (!id || !user) { mostrarTicker('Rellena ID de sala y usuario', 'leave'); return; }
    cmdRapido(`/sala invitar ${id} ${user}`);
}

function aceptarSala() {
    const id = document.getElementById('sala-aceptar-id')?.value.trim();
    if (!id) { mostrarTicker('Introduce el ID de la sala', 'leave'); return; }
    cmdRapido(`/sala aceptar ${id}`);
    // Añadir a misRooms si no existe
    if (!misRooms[id]) misRooms[id] = { name: id, msgs: [] };
    setTimeout(() => _renderWidgetSalas(), 500);
}

function salirDeSala(roomId) {
    cmdRapido(`/sala salir ${roomId}`);
    delete misRooms[roomId];
    _renderWidgetSalas();
}

/* Widget de salas como panel */
function abrirWidgetSalas() {
    const id    = 'salas';
    const label = '🏠 Salas';
    if (!widgetStore[id]) {
        _crearFab(id, label);
        _crearPanel(id);
        widgetStore[id] = { data: {}, timestamp: Date.now() };
        _actualizarFab(id, label);
    }
    // Construir cabecera si no existe
    const p = document.getElementById('panel-salas');
    if (p && !p.querySelector('.widget-body')) {
        const title = document.createElement('div'); title.className = 'widget-panel-title';
        title.innerHTML = `<span>${label}</span><span><span class="widget-ts"></span><span class="widget-close" onclick="cerrarPanel('salas')">✕</span></span>`;
        const body = document.createElement('div'); body.className = 'widget-body';
        p.appendChild(title); p.appendChild(body);
    }
    _renderWidgetSalas();
    mostrarPanel(id);
}

/* Cuando el servidor responde con widget "salas" */
function _renderWidgetSalasData(data) {
    if (data?.salas) {
        data.salas.forEach(s => {
            if (!misRooms[s.id]) {
                misRooms[s.id] = { name: s.name || s.id, msgs: [] };
            } else {
                misRooms[s.id].name = s.name || s.id;
            }
        });
    }
    _renderWidgetSalas();
}

/* ═══════════════════════════════════════════════════════════════════════
   WIDGET CUENTA / AUTENTICACIÓN
═══════════════════════════════════════════════════════════════════════ */
function abrirWidgetCuenta() {
    abrirLayer('cuenta', '👤 Cuenta / Identidad', 'html:' + _htmlCuenta(), { w: 380, h: 480 });
}

function _htmlCuenta() {
    const esRegistrado = !!myUsername;
    if (esRegistrado) {
        return `
        <div class="cuenta-wrap">
            <div class="cuenta-avatar">👤</div>
            <div class="cuenta-nombre">${escH(myUsername)}</div>
            <div class="cuenta-vname">${escH(myVname)}</div>
            <div class="cuenta-sep"></div>
            <button class="cuenta-btn" onclick="cmdLayer('cuenta','/cuenta')">📋 Ver datos de cuenta</button>
            <button class="cuenta-btn" onclick="abrirWidgetPerfil()">✏️ Editar perfil</button>
            <button class="cuenta-btn" onclick="cmdLayer('cuenta','/sala lista')">🏠 Mis salas</button>
            <div class="cuenta-sep"></div>
            <button class="cuenta-btn danger" onclick="cmdLayer('cuenta','/logout')">🚪 Cerrar sesión</button>
        </div>`;
    }
    return `
    <div class="cuenta-wrap">
        <div class="cuenta-avatar">🔐</div>
        <div class="cuenta-nombre" style="color:#888">Sesión anónima</div>
        <div class="cuenta-vname">${escH(myVname)}</div>
        <div class="cuenta-sep"></div>

        <div class="cuenta-section-title">Iniciar sesión</div>
        <input id="login-user" class="cuenta-input" type="text" placeholder="@usuario" autocomplete="username">
        <input id="login-pass" class="cuenta-input" type="password" placeholder="Contraseña" autocomplete="current-password">
        <button class="cuenta-btn accent" onclick="hacerLogin()">🔓 Login</button>

        <div class="cuenta-sep"></div>
        <div class="cuenta-section-title">Crear cuenta nueva</div>
        <input id="reg-user"  class="cuenta-input" type="text"     placeholder="@usuario (3-24 chars)" autocomplete="username">
        <input id="reg-email" class="cuenta-input" type="email"    placeholder="email@ejemplo.com"      autocomplete="email">
        <input id="reg-pass"  class="cuenta-input" type="password" placeholder="Contraseña (mín. 8)"   autocomplete="new-password">
        <button class="cuenta-btn accent" onclick="hacerRegistro()">✅ Registrarse</button>
    </div>`;
}

function hacerLogin() {
    const user = document.getElementById('login-user')?.value.trim().replace(/^@/,'');
    const pass = document.getElementById('login-pass')?.value;
    if (!user || !pass) { mostrarTicker('Rellena usuario y contraseña', 'leave'); return; }
    if (socket?.readyState === WebSocket.OPEN) {
        socket.send(`/login @${user} ${pass}`);
        cerrarLayer('cuenta');
    }
}

function hacerRegistro() {
    const user  = document.getElementById('reg-user')?.value.trim().replace(/^@/,'');
    const email = document.getElementById('reg-email')?.value.trim();
    const pass  = document.getElementById('reg-pass')?.value;
    if (!user || !email || !pass) { mostrarTicker('Rellena todos los campos', 'leave'); return; }
    if (socket?.readyState === WebSocket.OPEN) {
        socket.send(`/registro @${user} ${email} ${pass}`);
        cerrarLayer('cuenta');
    }
}

/** Envía un comando desde dentro de una layer y la cierra */
function cmdLayer(layerId, cmd) {
    if (socket?.readyState === WebSocket.OPEN) socket.send(cmd);
    cerrarLayer(layerId);
}

/* ═══════════════════════════════════════════════════════════════════════
   WIDGET PERFIL
═══════════════════════════════════════════════════════════════════════ */
function abrirWidgetPerfil() {
    abrirLayer('perfil', '✏️ Perfil de usuario', 'html:' + _htmlPerfil(), { w: 400, h: 520 });
}

function _htmlPerfil() {
    return `
    <div class="cuenta-wrap">
        <div class="cuenta-section-title">Tipo de perfil</div>
        <div style="display:flex;gap:8px;margin-bottom:10px">
            <button class="perfil-tipo-btn active" id="ptipo-personal" onclick="selTipoPerfil('personal')">👤 Personal</button>
            <button class="perfil-tipo-btn" id="ptipo-empresa" onclick="selTipoPerfil('empresa')">🏢 Empresa</button>
        </div>

        <div class="cuenta-section-title">Datos</div>
        <input id="p-nombre"  class="cuenta-input" type="text" placeholder='Nombre completo  (comillas si tiene espacios)'>
        <input id="p-desc"    class="cuenta-input" type="text" placeholder="Descripción / quién eres">
        <input id="p-sector"  class="cuenta-input" type="text" placeholder="Sector (solo empresa)" id="p-sector-row">
        <input id="p-tono"    class="cuenta-input" type="text" placeholder="Tono: informal / formal / técnico…">

        <div class="cuenta-section-title" style="margin-top:10px">Visibilidad pública</div>
        <div class="perfil-vis-row">
            <label><input type="checkbox" id="pv-nombre" checked> Nombre</label>
            <label><input type="checkbox" id="pv-tipo"   checked> Tipo</label>
            <label><input type="checkbox" id="pv-desc"> Descripción</label>
        </div>

        <div class="cuenta-sep"></div>
        <button class="cuenta-btn accent" onclick="guardarPerfil()">💾 Guardar perfil</button>
        <button class="cuenta-btn" onclick="cmdLayer('perfil','/perfil ver')">👁 Ver perfil actual</button>
        <button class="cuenta-btn" onclick="cmdLayer('perfil','/perfil borrar')">🗑 Borrar perfil</button>
    </div>`;
}

let _tipoPerfilActivo = 'personal';
function selTipoPerfil(tipo) {
    _tipoPerfilActivo = tipo;
    document.querySelectorAll('.perfil-tipo-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`ptipo-${tipo}`)?.classList.add('active');
    const sectorRow = document.getElementById('p-sector');
    if (sectorRow) sectorRow.style.display = tipo === 'empresa' ? '' : 'none';
}

function guardarPerfil() {
    const nombre  = document.getElementById('p-nombre')?.value.trim() || '';
    const desc    = document.getElementById('p-desc')?.value.trim()   || '';
    const sector  = document.getElementById('p-sector')?.value.trim() || '';
    const tono    = document.getElementById('p-tono')?.value.trim()   || '';
    const pvNombre = document.getElementById('pv-nombre')?.checked;
    const pvTipo   = document.getElementById('pv-tipo')?.checked;
    const pvDesc   = document.getElementById('pv-desc')?.checked;

    // Construir comando con comillas para soportar espacios
    const tipo = _tipoPerfilActivo;
    const args = [
        nombre  ? `nombre="${nombre}"`   : '',
        desc    ? `desc="${desc}"`       : '',
        sector  ? `sector="${sector}"`   : '',
        tono    ? `tono="${tono}"`       : '',
    ].filter(Boolean).join(' ');

    if (socket?.readyState === WebSocket.OPEN) {
        socket.send(`/perfil ${tipo} ${args}`);
        // Actualizar visibilidades si registrado
        if (myUsername) {
            setTimeout(() => {
                if (pvNombre !== undefined) socket.send(`/perfil publico nombre ${pvNombre ? 'on' : 'off'}`);
                if (pvTipo   !== undefined) socket.send(`/perfil publico tipo   ${pvTipo   ? 'on' : 'off'}`);
                if (pvDesc   !== undefined) socket.send(`/perfil publico desc   ${pvDesc   ? 'on' : 'off'}`);
            }, 300);
        }
    }
    cerrarLayer('perfil');
    mostrarTicker('Perfil guardado', 'join');
}

/* ═══════════════════════════════════════════════════════════════════════
   WIDGET AYUDA
═══════════════════════════════════════════════════════════════════════ */
function abrirWidgetAyuda() {
    abrirLayer('ayuda', '📖 Ayuda y funcionamiento', 'html:' + _htmlAyuda(), { w: 460, h: 560 });
}

function _htmlAyuda() {
    return `
    <div class="ayuda-wrap">

        <div class="ayuda-section">
            <div class="ayuda-title">🔐 Identidad</div>
            <div class="ayuda-body">
                <p>El sistema tiene <strong>tres niveles</strong> de identidad:</p>
                <ul>
                    <li><strong>Anónimo</strong> — ID efímero (ej. <code>a3f2b1c0@server</code>). Se pierde al desconectar.</li>
                    <li><strong>Registrado</strong> — Cuenta única en el servidor (<code>@usuario</code>). Perfil persistente.</li>
                </ul>
                <p>Comandos rápidos:</p>
                <code>/registro @usuario email contraseña</code><br>
                <code>/login @usuario contraseña</code><br>
                <code>/logout</code> — vuelve a anónimo<br>
                <code>/cuenta</code> — ver tus datos privados
            </div>
        </div>

        <div class="ayuda-section">
            <div class="ayuda-title">👤 Perfil</div>
            <div class="ayuda-body">
                <p>El perfil se inyecta en el contexto de la IA para respuestas personalizadas.</p>
                <code>/perfil personal nombre="X" desc="Y" tono=Z</code><br>
                <code>/perfil empresa  nombre="X" sector=S desc="Y"</code><br>
                <code>/perfil publico nombre on|off</code> — controlar visibilidad<br>
                <code>/perfil ver</code> · <code>/perfil borrar</code>
                <p style="margin-top:6px">Si estás registrado, el perfil se guarda en la base de datos automáticamente.</p>
            </div>
        </div>

        <div class="ayuda-section">
            <div class="ayuda-title">🏠 Salas privadas</div>
            <div class="ayuda-body">
                <p>Canales de chat privados por invitación. Solo ven los mensajes los miembros.</p>
                <code>/sala crear "Mi sala secreta"</code><br>
                <code>/sala invitar sala-xxxx usuario</code><br>
                <code>/sala aceptar sala-xxxx</code><br>
                <code>/sala msg sala-xxxx Hola</code><br>
                <code>/sala salir sala-xxxx</code> · <code>/sala lista</code>
                <p style="margin-top:6px">También puedes gestionarlas desde el botón <strong>🏠 Salas</strong>.</p>
            </div>
        </div>

        <div class="ayuda-section">
            <div class="ayuda-title">🤖 IA (Ollama)</div>
            <div class="ayuda-body">
                <code>/models</code> — ver modelos disponibles<br>
                <code>/model N</code> — cambiar de modelo<br>
                <code>/clearcontext</code> — borrar historial de conversación<br>
                <code>/stop</code> — detener generación en curso<br>
                <code>/limit</code> — instancias IA activas ahora mismo
                <p style="margin-top:6px">El historial de conversación (últimos 20 turnos) se inyecta automáticamente.</p>
            </div>
        </div>

        <div class="ayuda-section">
            <div class="ayuda-title">💬 Chat y mensajería</div>
            <div class="ayuda-body">
                <p><strong>Canal global:</strong> botón 💬 Chat — todos los conectados lo ven.</p>
                <p><strong>PM (privado):</strong> en 👥 Usuarios → botón 💬 PM junto al usuario.</p>
                <code>/pm usuario mensaje</code> — también por texto directo<br>
                <p><strong>Posts:</strong> 📢 Posts — mural público, máx. 500 caracteres.</p>
            </div>
        </div>

        <div class="ayuda-section">
            <div class="ayuda-title">🎨 Skins y aspecto</div>
            <div class="ayuda-body">
                <p>Cambia el tema visual con:</p>
                <code>setSkin('default')</code> — verde terminal<br>
                <code>setSkin('matrix')</code> — matrix verde<br>
                <code>setSkin('neon')</code> — neón oscuro<br>
                <code>setSkin('retro')</code> — ámbar retro<br>
                <code>setSkin('light')</code> — claro
                <p style="margin-top:6px">La preferencia se guarda en localStorage.</p>
            </div>
        </div>

        <div class="ayuda-section">
            <div class="ayuda-title">📺 TV y servidores</div>
            <div class="ayuda-body">
                <code>/listtv</code> — canales TV disponibles<br>
                <code>/servers</code> — nodos remotos disponibles<br>
                <code>/info</code> — métricas del servidor<br>
                <code>/way</code> — info del sistema ODyN
            </div>
        </div>

        <div style="color:#333;font-size:0.72em;text-align:center;margin-top:12px;padding-top:8px;border-top:1px solid #1a1a1a">
            GoyimAI — sistema ODyN — GoyCorp
        </div>
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════════════
   POST PUBLISHER
═══════════════════════════════════════════════════════════════════════ */
const posts   = [];
const MAX_POSTS = 50;
const MAX_POST_CHARS = 500;

function _initPostPublisher(body) {
    if (body.querySelector('#post-publisher')) return;
    body.innerHTML = `
        <div id="post-publisher">
            <textarea id="post-input" placeholder="Escribe algo para publicar en el mural…" maxlength="${MAX_POST_CHARS}"></textarea>
            <div class="post-actions">
                <button id="post-send" onclick="enviarPost()">📢 Publicar</button>
                <span id="post-char-count">0/${MAX_POST_CHARS}</span>
            </div>
        </div>
        <div id="post-feed"></div>`;
    const ta = document.getElementById('post-input');
    ta.addEventListener('input', () => {
        document.getElementById('post-char-count').textContent = ta.value.length + '/' + MAX_POST_CHARS;
    });
    ta.addEventListener('keydown', e => {
        e.stopPropagation();
        if (e.key === 'Enter') { e.preventDefault(); if (e.ctrlKey || e.metaKey) enviarPost(); }
    });
    _renderPosts();
}
function enviarPost() {
    const ta   = document.getElementById('post-input');
    const text = ta?.value.trim();
    if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;
    socket.send(JSON.stringify({ type: 'post', text }));
    ta.value = '';
    document.getElementById('post-char-count').textContent = '0/' + MAX_POST_CHARS;
}
function pushPost(entry) {
    posts.unshift(entry);
    if (posts.length > MAX_POSTS) posts.pop();
    _renderPosts();
    const btn = document.getElementById('fab-posts');
    if (btn && !document.getElementById('panel-posts')?.classList.contains('visible')) {
        btn.textContent = '📢 Posts ●';
    }
}
function _renderPosts() {
    const feed = document.getElementById('post-feed');
    if (!feed) return;
    if (!posts.length) { feed.innerHTML = '<p style="color:#222;font-size:0.82em">No hay publicaciones aún.</p>'; return; }
    feed.innerHTML = posts.map(p => {
        const isSelf = p.from === myVname;
        return `<div class="post-item">
            <div class="post-header">
                <span class="post-from ${isSelf?'self':''}">${escH(p.from)}</span>
                <span class="post-ts">${fmtTime(p.ts)}</span>
            </div>
            <div class="post-text">${escH(p.text)}</div>
        </div>`;
    }).join('');
}

/* ═══════════════════════════════════════════════════════════════════════
   TV EMBED
═══════════════════════════════════════════════════════════════════════ */
let tvMode   = 'embed';
let tvHeight = 0;

function setTvMode(mode, btn) {
    tvMode = mode;
    document.querySelectorAll('.tv-mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}
function abrirCanal(url, nombre) {
    const fullUrl = `https://osiris000.duckdns.org/app/mitv/tv/player2.php?chn=${encodeURIComponent(url)}`;
    if (tvMode === 'window') { window.open(fullUrl, '_blank'); return; }
    const bar   = document.getElementById('tv-embed-bar');
    const frame = document.getElementById('tv-embed-frame');
    document.getElementById('tv-embed-title').textContent = nombre;
    frame.src = fullUrl;
    bar.classList.add('visible');
    _recalcLayout();
}
function cerrarTvEmbed() {
    const bar   = document.getElementById('tv-embed-bar');
    const frame = document.getElementById('tv-embed-frame');
    frame.src   = '';
    bar.classList.remove('visible');
    tvHeight = 0;
    _recalcLayout();
}

(function _initTVResize() {
    let dragging = false, startY = 0, startH = 0;
    const MIN_H = 80, MAX_FRAC = 0.55;
    function onStart(e) {
        dragging = true;
        startY   = e.touches ? e.touches[0].clientY : e.clientY;
        startH   = document.getElementById('tv-embed-frame').offsetHeight;
        e.preventDefault();
    }
    function onMove(e) {
        if (!dragging) return;
        const y    = e.touches ? e.touches[0].clientY : e.clientY;
        const newH = Math.max(MIN_H, Math.min(window.innerHeight * MAX_FRAC, startH + (y - startY)));
        tvHeight   = newH;
        document.getElementById('tv-embed-frame').style.height = newH + 'px';
        _recalcLayout();
        e.preventDefault();
    }
    function onEnd() { dragging = false; }
    document.addEventListener('DOMContentLoaded', () => {
        const handle = document.getElementById('tv-embed-resize');
        if (!handle) return;
        handle.addEventListener('mousedown', onStart);
        handle.addEventListener('touchstart', onStart, { passive: false });
        document.addEventListener('mousemove', onMove);
        document.addEventListener('touchmove', onMove, { passive: false });
        document.addEventListener('mouseup', onEnd);
        document.addEventListener('touchend', onEnd);
    });
})();

/* ═══════════════════════════════════════════════════════════════════════
   LAYOUT MANAGER
═══════════════════════════════════════════════════════════════════════ */
function _recalcLayout() {
    const fabBar  = document.getElementById('widget-fab');
    const tvBar   = document.getElementById('tv-embed-bar');
    const frame   = document.getElementById('tv-embed-frame');
    const fabH    = fabBar.classList.contains('has-items') ? (fabBar.offsetHeight || 28) : 0;
    const tvOpen  = tvBar.classList.contains('visible');
    if (tvOpen) {
        if (!tvHeight) tvHeight = Math.floor(window.innerHeight * 0.32);
        frame.style.height = tvHeight + 'px';
        tvBar.style.top    = fabH + 'px';
    }
    const tvBarH   = tvOpen ? (tvBar.offsetHeight || 0) : 0;
    const panelTop = fabH + tvBarH;
    const BOTTOM_MARGIN = 80;
    const panelMaxH = Math.max(60, window.innerHeight - panelTop - BOTTOM_MARGIN);
    document.querySelectorAll('.widget-panel').forEach(p => {
        p.style.top       = panelTop + 'px';
        p.style.maxHeight = panelMaxH + 'px';
    });
    const wrapper = document.getElementById('wrapper');
    if (wrapper) {
        if (fabH > 0) {
            wrapper.style.marginTop = fabH + 'px';
            wrapper.style.height    = `calc(100vh - ${fabH}px)`;
        } else {
            wrapper.style.marginTop = '';
            wrapper.style.height    = '100vh';
        }
    }
}
window.addEventListener('resize', () => { _recalcLayout(); _reapilaPM(); });

/* ═══════════════════════════════════════════════════════════════════════
   VENTANAS PM
═══════════════════════════════════════════════════════════════════════ */
const pmWindows = {};
let   pmZTop    = 500;
const PM_W = 270, PM_H = 300, PM_GAP = 6, PM_BOTTOM = 20;
const PM_CASCADE_X = 18, PM_CASCADE_Y = 18;

function _pmSlots() { return Math.max(1, Math.floor((window.innerWidth - PM_GAP) / (PM_W + PM_GAP))); }

function _reapilaPM() {
    const ids   = Object.keys(pmWindows);
    const slots = _pmSlots();
    ids.forEach((id, i) => {
        const win = pmWindows[id];
        if (win.maximized || win._dragged) return;
        if (i < slots) {
            win.el.style.right  = (PM_GAP + i * (PM_W + PM_GAP)) + 'px';
            win.el.style.bottom = PM_BOTTOM + 'px';
            win.el.style.left   = 'auto';
            win.el.style.top    = 'auto';
        } else {
            const overflow    = i - slots + 1;
            const anchorRight = PM_GAP + (slots - 1) * (PM_W + PM_GAP);
            const anchorLeft  = window.innerWidth - anchorRight - PM_W;
            win.el.style.left   = Math.max(0, anchorLeft - overflow * PM_CASCADE_X) + 'px';
            win.el.style.top    = Math.max(0, window.innerHeight - PM_BOTTOM - PM_H - overflow * PM_CASCADE_Y) + 'px';
            win.el.style.right  = 'auto';
            win.el.style.bottom = 'auto';
        }
    });
}

function abrirPM(peerId, peerVname) {
    if (pmWindows[peerId]) {
        const win = pmWindows[peerId];
        win.el.classList.remove('minimized', 'notify', 'maximized');
        win.el.classList.add('focused');
        win.unread = 0; win.maximized = false;
        _actualizarPMtitle(peerId); _limpiarNotifPM(peerId); _pmFocus(peerId);
        win.el.querySelector('.pm-win-input')?.focus();
        return;
    }
    const win = { msgs: [], minimized: false, maximized: false, unread: 0, peerVname };
    pmWindows[peerId] = win;
    const el = document.createElement('div');
    el.className = 'pm-window focused';
    el.id        = `pm-win-${peerId}`;
    el.style.width  = PM_W + 'px';
    el.style.height = PM_H + 'px';
    el.style.right  = PM_GAP + 'px';
    el.style.bottom = PM_BOTTOM + 'px';
    el.style.zIndex = ++pmZTop;
    el.innerHTML = `
        <div class="pm-win-header" id="pm-hdr-${escH(peerId)}">
            <span class="pm-notif-dot" id="pm-dot-${escH(peerId)}"></span>
            <span class="pm-win-title" id="pm-title-${escH(peerId)}">✉ ${escH(peerVname)}</span>
            <div class="pm-win-actions">
                <span class="pm-win-btn" title="Minimizar"  onclick="event.stopPropagation();toggleMinPM('${escH(peerId)}')">─</span>
                <span class="pm-win-btn" title="Maximizar"  onclick="event.stopPropagation();toggleMaxPM('${escH(peerId)}')">□</span>
                <span class="pm-win-btn close" title="Cerrar" onclick="event.stopPropagation();cerrarPM('${escH(peerId)}')">✕</span>
            </div>
        </div>
        <div class="pm-win-msgs" id="pm-msgs-${escH(peerId)}"></div>
        <div class="pm-win-form">
            <input class="pm-win-input" type="text" placeholder="Mensaje privado…" autocomplete="off" id="pm-inp-${escH(peerId)}">
            <button class="pm-win-send" onclick="enviarPM('${escH(peerId)}')">↩</button>
        </div>
        <div class="pm-resize-handle" id="pm-rsz-${escH(peerId)}"></div>`;
    el.querySelector('.pm-win-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); enviarPM(peerId); }
    });
    el.addEventListener('mousedown',  () => _pmFocus(peerId));
    el.addEventListener('touchstart', () => _pmFocus(peerId), { passive: true });
    win.el = el;
    document.getElementById('pm-windows-container').appendChild(el);
    _initPMDrag(peerId); _initPMResize(peerId); _reapilaPM();
    el.querySelector('.pm-win-input')?.focus();
}

function _pmFocus(peerId) {
    pmZTop++;
    const win = pmWindows[peerId]; if (!win) return;
    win.el.style.zIndex = pmZTop;
    win.unread = 0;
    win.el.classList.remove('notify'); win.el.classList.add('focused');
    _actualizarPMtitle(peerId); _limpiarNotifPM(peerId);
}
function toggleMinPM(peerId) {
    const win = pmWindows[peerId]; if (!win) return;
    win.minimized = !win.minimized;
    win.el.classList.toggle('minimized', win.minimized);
    if (!win.minimized) { _pmFocus(peerId); win.el.querySelector('.pm-win-input')?.focus(); }
}
function toggleMaxPM(peerId) {
    const win = pmWindows[peerId]; if (!win) return;
    win.maximized = !win.maximized;
    win.el.classList.toggle('maximized', win.maximized);
    if (!win.maximized) _reapilaPM();
}
function cerrarPM(peerId) {
    pmWindows[peerId]?.el.remove();
    delete pmWindows[peerId];
    _reapilaPM();
}
function enviarPM(peerId) {
    const inp  = document.getElementById(`pm-inp-${peerId}`);
    const text = inp?.value.trim();
    if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;
    const win = pmWindows[peerId]; if (!win) return;
    const toId = peerId.replace('@','');
    socket.send(JSON.stringify({ type: 'chat', text: `/pm ${toId} ${text}` }));
    win.msgs.push({ from: myVname || 'yo', text, ts: Date.now(), self: true });
    _renderPMmsgs(peerId);
    if (inp) inp.value = '';
}
function recibirPM(obj) {
    const isSelf = obj.self;
    const peerId = isSelf ? obj.to.replace('@','').replace('@server','')
                          : obj.from.replace('@','').replace('@server','');
    const peerVname = isSelf ? (obj.to) : (obj.from);
    abrirPM(peerId, peerVname);
    const win = pmWindows[peerId]; if (!win) return;
    win.msgs.push({ from: isSelf ? (myVname || 'yo') : obj.from, text: obj.text, ts: Date.now(), self: isSelf });
    _renderPMmsgs(peerId);
    if (!isSelf) {
        win.unread++;
        win.el.classList.add('notify');
        _actualizarPMtitle(peerId);
        const dot = document.getElementById(`pm-dot-${peerId}`); if (dot) dot.classList.add('on');
        const whoDot = document.getElementById(`who-dot-${peerId}`); if (whoDot) whoDot.classList.add('on');
    }
}
function _renderPMmsgs(peerId) {
    const box  = document.getElementById(`pm-msgs-${peerId}`);
    const msgs = pmWindows[peerId]?.msgs || [];
    if (!box) return;
    box.innerHTML = msgs.map(m => {
        const cls  = m.self ? 'me' : 'them';
        const from = m.self ? (myVname || 'yo') : m.from;
        return `<div class="pm-msg">
            <span class="pm-msg-from ${cls}">${escH(from)}</span>
            <span class="pm-msg-text">${escH(m.text)}</span>
            <span class="pm-msg-ts">${fmtTime(m.ts)}</span>
        </div>`;
    }).join('');
    box.scrollTop = box.scrollHeight;
}
function _actualizarPMtitle(peerId) {
    const win  = pmWindows[peerId]; if (!win) return;
    const el   = document.getElementById(`pm-title-${peerId}`);
    const base = `✉ ${win.peerVname}`;
    if (el) el.textContent = win.unread > 0 ? `${base} (${win.unread})` : base;
    el?.classList.toggle('notify-t', win.unread > 0);
}
function _limpiarNotifPM(peerId) {
    document.getElementById(`who-dot-${peerId}`)?.classList.remove('on');
    document.getElementById(`pm-win-${peerId}`)?.classList.remove('notify');
}

function _initPMDrag(peerId) {
    const win = pmWindows[peerId];
    const hdr = document.getElementById(`pm-hdr-${peerId}`);
    if (!hdr) return;
    let ox = 0, oy = 0, sx = 0, sy = 0, dragging = false;
    function getXY(e) { return e.touches ? { x: e.touches[0].clientX, y: e.touches[0].clientY } : { x: e.clientX, y: e.clientY }; }
    function onStart(e) {
        if (win.maximized || e.target.closest('.pm-win-btn')) return;
        dragging = true;
        const r = win.el.getBoundingClientRect();
        sx = getXY(e).x; sy = getXY(e).y; ox = r.left; oy = r.top;
        win.el.style.right = 'auto'; win.el.style.bottom = 'auto';
        win.el.style.left  = ox + 'px'; win.el.style.top = oy + 'px';
        _pmFocus(peerId); e.preventDefault();
    }
    function onMove(e) {
        if (!dragging) return;
        const { x, y } = getXY(e);
        win.el.style.left = Math.max(0, Math.min(window.innerWidth  - win.el.offsetWidth,  ox + (x - sx))) + 'px';
        win.el.style.top  = Math.max(0, Math.min(window.innerHeight - win.el.offsetHeight, oy + (y - sy))) + 'px';
        e.preventDefault();
    }
    function onEnd() { if (dragging) win._dragged = true; dragging = false; }
    hdr.addEventListener('mousedown', onStart);
    hdr.addEventListener('touchstart', onStart, { passive: false });
    document.addEventListener('mousemove', onMove);
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('mouseup', onEnd);
    document.addEventListener('touchend', onEnd);
}
function _initPMResize(peerId) {
    const win    = pmWindows[peerId];
    const handle = document.getElementById(`pm-rsz-${peerId}`);
    if (!handle) return;
    let dragging = false, sx = 0, sy = 0, sw = 0, sh = 0;
    const MIN_W = 200, MIN_H = 160;
    function getXY(e) { return e.touches ? { x: e.touches[0].clientX, y: e.touches[0].clientY } : { x: e.clientX, y: e.clientY }; }
    function onStart(e) {
        if (win.maximized || win.minimized) return;
        dragging = true; sx = getXY(e).x; sy = getXY(e).y;
        sw = win.el.offsetWidth; sh = win.el.offsetHeight;
        e.preventDefault(); e.stopPropagation();
    }
    function onMove(e) {
        if (!dragging) return;
        const { x, y } = getXY(e);
        win.el.style.width  = Math.max(MIN_W, sw + (x - sx)) + 'px';
        win.el.style.height = Math.max(MIN_H, sh + (y - sy)) + 'px';
        e.preventDefault();
    }
    function onEnd() { dragging = false; }
    handle.addEventListener('mousedown', onStart);
    handle.addEventListener('touchstart', onStart, { passive: false });
    document.addEventListener('mousemove', onMove);
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('mouseup', onEnd);
    document.addEventListener('touchend', onEnd);
}

/* ═══════════════════════════════════════════════════════════════════════
   SISTEMA DE WIDGETS
═══════════════════════════════════════════════════════════════════════ */
const widgetStore   = {};
const WIDGET_TTL    = 5 * 60 * 1000;
const WIDGET_LABELS = {
    tv_channels: '📺 TV',
    servers:     '🌐 Nodos',
    info:        '📊 Info',
    models:      '🤖 Modelos',
    welcome:     '👋 Sesión',
    who:         '👥 Usuarios',
    social_chat: '💬 Chat',
    posts:       '📢 Posts',
    salas:       '🏠 Salas',
};

function procesarWidget(obj) {
    const id    = obj.widget;
    const label = WIDGET_LABELS[id] || id;
    const isNew = !widgetStore[id];
    widgetStore[id] = { data: obj.data, timestamp: Date.now() };
    if (id === 'salas') { _renderWidgetSalasData(obj.data); return; }
    if (isNew) { _crearFab(id, label); _crearPanel(id); }
    _renderPanel(id, label, obj.data);
    _actualizarFab(id, label);
    mostrarPanel(id);
}

function _asegurarPanel(id) {
    if (!document.getElementById('panel-' + id)) {
        const label = WIDGET_LABELS[id] || id;
        _crearFab(id, label); _crearPanel(id);
        _renderPanel(id, label, null); _actualizarFab(id, label);
    }
}
function _crearFab(id, label) {
    const fab = document.getElementById('widget-fab');
    if (document.getElementById('fab-' + id)) return;
    const btn = document.createElement('button');
    btn.className = 'widget-fab-btn';
    btn.id        = 'fab-' + id;
    btn.onclick   = (e) => { e.stopPropagation(); togglePanel(id); };
    fab.appendChild(btn);
    fab.classList.add('has-items');
    requestAnimationFrame(_recalcLayout);
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
    if (id === 'salas') {
        const n = Object.keys(misRooms).length;
        btn.textContent = label + (n > 0 ? ` (${n})` : '');
        btn.classList.remove('notif');
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
    document.getElementById('widget-panels').appendChild(div);
    _recalcLayout();
}
function mostrarPanel(id) {
    document.querySelectorAll('.widget-panel').forEach(p => p.classList.remove('visible'));
    document.querySelectorAll('.widget-fab-btn').forEach(b => b.classList.remove('active'));
    const p   = document.getElementById('panel-' + id);
    const btn = document.getElementById('fab-' + id);
    if (p)   p.classList.add('visible');
    if (btn) btn.classList.add('active');
    _recalcLayout();
    if (btn && !btn.classList.contains('stale')) {
        if (id === 'posts')       btn.textContent = WIDGET_LABELS.posts + ' ●';
        if (id === 'social_chat') _actualizarFab(id, WIDGET_LABELS[id]);
    }
}
function togglePanel(id) {
    if (id === 'social_chat' || id === 'posts') _asegurarPanel(id);
    const p = document.getElementById('panel-' + id);
    if (!p) return;
    const wasVisible = p.classList.contains('visible');
    document.querySelectorAll('.widget-panel').forEach(el => el.classList.remove('visible'));
    document.querySelectorAll('.widget-fab-btn').forEach(b => b.classList.remove('active'));
    if (!wasVisible) {
        p.classList.add('visible');
        document.getElementById('fab-' + id)?.classList.add('active');
        _recalcLayout();
        if (id === 'social_chat') setTimeout(() => document.getElementById('chat-social-input')?.focus(), 50);
        if (id === 'posts')       setTimeout(() => document.getElementById('post-input')?.focus(), 50);
        if (id === 'salas')       _renderWidgetSalas();
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
        const right = document.createElement('span'); right.appendChild(ts_el); right.appendChild(close_el);
        const left  = document.createElement('span'); left.textContent = label;
        const title = document.createElement('div'); title.className = 'widget-panel-title';
        title.appendChild(left); title.appendChild(right);
        const body = document.createElement('div'); body.className = 'widget-body';
        p.appendChild(title); p.appendChild(body);
    }
    const ts_el = p.querySelector('.widget-ts');
    if (ts_el && id !== 'social_chat' && id !== 'posts' && id !== 'salas') ts_el.textContent = new Date().toLocaleTimeString();
    const body = p.querySelector('.widget-body');
    if (!body) return;
    if (id === 'social_chat') { _renderSocialChat(body); return; }
    if (id === 'posts')       { _initPostPublisher(body); return; }
    if (id === 'salas')       { _renderWidgetSalas(); return; }
    let html = '';
    if      (id === 'tv_channels') html = _renderTV(data);
    else if (id === 'servers')     html = _renderServers(data);
    else if (id === 'info')        html = _renderInfo(data);
    else if (id === 'models')      html = _renderModels(data);
    else if (id === 'welcome')     html = _renderWelcome(data);
    else if (id === 'who')         html = _renderWho(data);
    body.innerHTML = html;
}

/* ─── RENDERS ─── */
function _renderTV(data) {
    if (!data?.channels?.length) return '<p style="color:#555">No hay canales.</p>';
    const modeBar = `<div class="tv-mode-bar">
        <span class="tv-mode-lbl">Visor:</span>
        <button class="tv-mode-btn ${tvMode==='embed'?'active':''}" onclick="setTvMode('embed',this)">📺 Embebido</button>
        <button class="tv-mode-btn ${tvMode==='window'?'active':''}" onclick="setTvMode('window',this)">🔲 Ventana nueva</button>
    </div>`;
    return modeBar + data.channels.map(ch =>
        `<div class="tv-item"><span class="tv-name">${escH(ch.canal)}</span>
        <button class="tv-btn" onclick="abrirCanal('${escH(ch.url)}','${escH(ch.canal)}')">▶ VER</button></div>`
    ).join('');
}
function _renderServers(data) {
    if (!data?.servers?.length) return '<p style="color:#555">No hay servidores.</p>';
    const origin = window.location.hostname;
    return data.servers.map(s => {
        const h = s.host;
        const isCurrent = h === activeHost, isOrigin = h === origin;
        const label = isCurrent ? '[ACTIVO]' : (isOrigin ? '[ORIGEN]' : '[REMOTO]');
        return `<div class="server-line" style="${isCurrent?'border-left-color:#ff0;background:#111;':''}">
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
    const sv = data?.server || {}, r = data?.ram || {}, sess = data?.session || {};
    const pct = r.used_pct || 0, cls = pct > 85 ? 'danger' : pct > 65 ? 'warn' : '';
    const inRam = (data?.models_in_ram || []).join(', ') || 'ninguno';
    return `
    <div class="info-section" style="text-align:center;color:#0f0;font-size:1.05em;padding:4px 0 6px">${escH(data?.datetime||'')}</div>
    <div class="info-section"><h4>🖥️ Servidor</h4>
        <div class="info-row"><span class="info-label">Uptime</span><span class="info-value">${escH(sv.uptime||'')}</span></div>
        <div class="info-row"><span class="info-label">Uptime OS</span><span class="info-value">${escH(sv.uptime_os||'')}</span></div>
        <div class="info-row"><span class="info-label">Clientes</span><span class="info-value">${sv.clients||0}</span></div>
        <div class="info-row"><span class="info-label">IA activas</span><span class="info-value">${sv.ai_active||0}/${sv.ai_max||0}</span></div>
    </div>
    <div class="info-section"><h4>💾 RAM</h4>
        <div class="info-row"><span class="info-label">Usada</span><span class="info-value">${r.used_mb||0}MB/${r.total_mb||0}MB (${pct}%)</span></div>
        <div class="info-row"><span class="info-label">Libre</span><span class="info-value">${r.available_mb||0}MB</span></div>
        <div class="ram-bar"><div class="ram-bar-fill ${cls}" style="width:${pct}%"></div></div>
        <div class="info-row" style="margin-top:4px"><span class="info-label">En RAM</span><span class="info-value" style="font-size:0.82em">${escH(inRam)}</span></div>
    </div>
    <div class="info-section"><h4>👤 Tu sesión</h4>
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
    return header + data.models.map(m => {
        const nc  = m.active ? 'model-name active' : 'model-name';
        const ram = m.in_ram ? '<span class="mbadge mb-ram">RAM</span>' : (!m.fits_ram ? '<span class="mbadge mb-nofit">⚠RAM</span>' : '');
        const act = m.active ? '<span class="mbadge mb-active">✓</span>' : '';
        return `<div class="model-item" onclick="cmdRapido('/model ${m.index}');togglePanel('models')">
            <span class="model-idx">${m.index}</span><span class="${nc}">${escH(m.name)}</span>${ram}${act}</div>`;
    }).join('') + `<div style="color:#333;font-size:0.72em;margin-top:6px">Pulsa para cambiar de modelo</div>`;
}
function _renderWelcome(data) {
    if (!data) return '';
    myShortId = data.id    || '';
    myVname   = data.vname || (data.id + '@server');
    // Si vname empieza por @ es usuario registrado
    if (myVname.startsWith('@')) {
        myUsername = myVname.slice(1);
    }
    const badge = myUsername
        ? `<div style="color:#ff0;font-size:0.8em;margin:2px 0">✅ Cuenta registrada</div>`
        : `<div style="color:#555;font-size:0.8em;margin:2px 0">👻 Sesión anónima — <a href="#" onclick="abrirWidgetCuenta();return false" style="color:#0a0">Registrarse</a></div>`;
    return `<div style="padding:4px">
        <div style="color:#0f0;font-size:1.1em;font-weight:bold">${escH(myVname)}</div>
        ${badge}
        <div style="margin:4px 0">Modelo: <span style="color:#0f0;font-weight:bold">${escH(data.model||'')}</span></div>
        <div style="color:#444;font-size:0.85em">${escH(data.message||'')}</div>
        <div style="margin-top:8px;display:flex;gap:6px;flex-wrap:wrap">
            <button class="sala-btn" onclick="abrirWidgetCuenta()">👤 Cuenta</button>
            <button class="sala-btn" onclick="abrirWidgetPerfil()">✏️ Perfil</button>
            <button class="sala-btn" onclick="abrirWidgetSalas()">🏠 Salas</button>
            <button class="sala-btn" onclick="abrirWidgetAyuda()">📖 Ayuda</button>
        </div>
    </div>`;
}
function _renderWho(data) {
    if (!data?.users?.length) return '<p style="color:#555">Nadie conectado.</p>';
    return data.users.map(u => {
        const isSelf = u.id === myShortId || u.vname === myVname;
        const nc     = isSelf ? 'who-vname self' : 'who-vname';
        const busy   = u.busy ? '<span class="who-busy">IA</span>' : '';
        const reg    = u.registrado ? '<span class="who-reg">✓</span>' : '';
        const pmPart = !isSelf
            ? `<button class="who-pm-btn" onclick="abrirPM('${escH(u.id)}','${escH(u.vname)}');cerrarPanel('who')">
                   <span class="notif-dot" id="who-dot-${escH(u.id)}"></span>💬 PM
               </button>`
            : '<span style="color:#333;font-size:0.7em">tú</span>';
        return `<div class="who-item">
            <span class="${nc}">${escH(u.vname)}</span>
            ${reg}<span class="who-meta">${escH(u.since)} · ${u.msgs}msg</span>
            ${busy}${pmPart}
        </div>`;
    }).join('') + `<div style="color:#333;font-size:0.7em;margin-top:6px;text-align:right">${data.users.length} conectado(s)</div>`;
}
function _renderSocialChat(body) {
    if (body.querySelector('#chat-social-msgs')) { _renderSocialMsgs(); _updateOnlineBar(); return; }
    body.innerHTML = `
        <div class="chat-online-bar">
            <span>Canal común</span>
            <span class="chat-online-count" id="chat-online-count-el">${onlineCount} en línea</span>
        </div>
        <div id="chat-social-msgs"></div>
        <div id="chat-social-form">
            <input id="chat-social-input" type="text" placeholder="Escribe para todos…" autocomplete="off">
            <button id="chat-social-send" onclick="enviarChatSocial()">↩</button>
            <button id="chat-social-clear" title="Limpiar" onclick="limpiarChatSocial()">🗑</button>
        </div>
        <div style="color:#2a2a2a;font-size:0.68em;margin-top:4px">Para privados usa 👥 Usuarios → 💬 PM</div>`;
    document.getElementById('chat-social-input').addEventListener('keydown', e => {
        if (e.key === 'Enter') { e.preventDefault(); enviarChatSocial(); }
    });
    _renderSocialMsgs(); _updateOnlineBar();
}

setInterval(() => {
    Object.keys(widgetStore).forEach(id => _actualizarFab(id, WIDGET_LABELS[id] || id));
    _actualizarFab('social_chat', WIDGET_LABELS.social_chat);
}, 60000);

/* ═══════════════════════════════════════════════════════════════════════
   CHAT IA
═══════════════════════════════════════════════════════════════════════ */
marked.use({ renderer: { link(href, title, text) { return `<a target="_blank" href="${href}">${text}</a>`; } } });

function escaparHTML(str) { return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function toggleDrawer() { document.getElementById('quick-commands').classList.toggle('show'); }
function cmdRapido(cmd) { messageInput.value = cmd; enviarMensaje(); }
function setMode(mode, btn) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    refreshChat();
}
function refreshChat() { chatBox.innerHTML = ""; history.forEach(m => renderToDOM(m.text, m.type)); }

function pingServer(url) {
    if (url !== activeHost) { render(`>>> AVISO: conectado a ${activeHost}.`, "sys"); return; }
    render(`>>> PING A ${activeHost}…`, "sys");
    socket.send('/info'); socket.send('/way');
}
function connectToServer(url) {
    if (url === activeHost && socket?.readyState === WebSocket.OPEN) { render(">>> YA CONECTADO A ESTE NODO", "sys"); return; }
    activeHost = url;
    render(`>>> CAMBIANDO NODO A: ${activeHost}`, "sys");
    if (socket) { socket.onclose = null; socket.close(); }
    conectar(activeHost);
}

function render(text, type = 'server') {
    if (type !== 'server' || text.includes("📺") || text.includes(">>>")) {
        lastServerMsgDiv = null; history.push({ text, type }); renderToDOM(text, type); return;
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
    if (type === 'server_html')  div.innerHTML = text;
    else if (type === 'server')  { if (currentMode === 'md') div.innerHTML = marked.parse(escaparHTML(text)); else div.textContent = text; }
    else                         div.textContent = text;
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
        _asegurarPanel('social_chat');
        _asegurarPanel('posts');
    };

    socket.onmessage = (e) => {
        if (!e.data) return;
        try {
            const obj = JSON.parse(e.data);

            if (obj.type === 'widget') {
                if (obj.widget === 'welcome' && obj.data?.clients !== undefined) {
                    onlineCount = obj.data.clients;
                    _actualizarFab('social_chat', WIDGET_LABELS.social_chat);
                    _updateOnlineBar();
                    // Detectar si la sesión es registrada por el vname
                    if (obj.data?.vname?.startsWith('@')) {
                        myUsername = obj.data.vname.slice(1);
                    }
                }
                procesarWidget(obj);
                return;
            }

            if (obj.type === 'presence') {
                if (obj.clients !== undefined) onlineCount = obj.clients;
                _actualizarFab('social_chat', WIDGET_LABELS.social_chat);
                _updateOnlineBar();
                if (obj.event === 'join')  mostrarTicker(`⬤ ${obj.id} conectado  ·  ${onlineCount} en línea`, 'join');
                if (obj.event === 'leave') mostrarTicker(`○ ${obj.id} desconectado  ·  ${onlineCount} en línea`, 'leave');
                return;
            }

            if (obj.type === 'chat') {
                pushSocialMsg({ from: obj.from, text: obj.text, ts: Date.now() });
                const panel = document.getElementById('panel-social_chat');
                if (!panel?.classList.contains('visible')) {
                    const btn = document.getElementById('fab-social_chat');
                    if (btn) btn.textContent = '💬 Chat ●';
                }
                return;
            }

            if (obj.type === 'pm')   { recibirPM(obj); return; }

            if (obj.type === 'post') { pushPost({ from: obj.from, text: obj.text, ts: Date.now() }); return; }

            if (obj.type === 'chat_error') {
                pushSocialMsg({ from: '⚠', text: obj.text, ts: Date.now() });
                return;
            }

            // ── NUEVOS TIPOS ──
            if (obj.type === 'room_msg')    { recibirRoomMsg(obj);    return; }
            if (obj.type === 'room_invite') { recibirRoomInvite(obj); return; }

        } catch (_) {}

        render(e.data, "server");
    };

    socket.onclose = () => {
        render(`>>> CONEXIÓN PERDIDA EN ${activeHost} - REINTENTANDO…`, "sys");
        lastServerMsgDiv = null;
        reconnectTimer = setTimeout(() => conectar(activeHost), reconnectInterval);
    };

    socket.onerror = () => render(">>> ERROR DE NODO EN " + activeHost, "sys");
}

function enviarMensaje(e) {
    if (e) e.preventDefault();
    const msg = messageInput.value.trim();
    if (msg && socket?.readyState === WebSocket.OPEN) {
        lastCommandSent  = msg;
        lastServerMsgDiv = null;
        // Comandos de auth/sala se mandan directo como texto
        socket.send(msg);
        render("TÚ: " + msg, "user");
        messageInput.value = "";
    }
    return false;
}

/* ─── ARRANQUE ─── */
document.addEventListener('DOMContentLoaded', () => {
    render(">>> ESCRIBIR /help Para Ayuda", "sys");
    conectar(activeHost);
});

/* ═══════════════════════════════════════════════════════════════════════
   SISTEMA DE CAPAS (LAYERS)
═══════════════════════════════════════════════════════════════════════ */
const layerStore  = {};
let   layerZTop   = 1000;
const LAYER_W_DEF = 460;
const LAYER_H_DEF = 340;

function abrirLayer(id, title, content, opts = {}) {
    if (layerStore[id]) {
        const l = layerStore[id];
        // Refrescar contenido si viene html:
        if (content.startsWith('html:')) {
            const bodyEl = l.el.querySelector('.layer-html-body');
            if (bodyEl) bodyEl.innerHTML = content.slice(5);
        }
        l.el.style.zIndex = ++layerZTop;
        l.el.classList.remove('layer-minimized');
        l.minimized = false;
        return;
    }
    const w = opts.w || LAYER_W_DEF;
    const h = opts.h || LAYER_H_DEF;
    const x = opts.x !== undefined ? opts.x : Math.round(window.innerWidth  / 2 - w / 2);
    const y = opts.y !== undefined ? opts.y : Math.round(window.innerHeight / 2 - h / 2);
    const el = document.createElement('div');
    el.className   = 'layer-win';
    el.id          = 'layer-' + id;
    el.style.cssText = `width:${w}px;height:${h}px;left:${x}px;top:${y}px;z-index:${++layerZTop}`;
    let bodyHTML;
    if (/^https?:\/\//i.test(content)) {
        bodyHTML = `<iframe class="layer-iframe" src="${escH(content)}" allowfullscreen allow="autoplay; fullscreen"></iframe>`;
    } else if (content.startsWith('html:')) {
        bodyHTML = `<div class="layer-html-body">${content.slice(5)}</div>`;
    } else {
        bodyHTML = `<div class="layer-html-body">${escH(content)}</div>`;
    }
    el.innerHTML = `
        <div class="layer-header" id="layer-hdr-${escH(id)}">
            <span class="layer-title">${escH(title)}</span>
            <div class="layer-actions">
                <span class="layer-btn" title="Minimizar" onclick="event.stopPropagation();toggleMinLayer('${escH(id)}')">─</span>
                <span class="layer-btn" title="Maximizar" onclick="event.stopPropagation();toggleMaxLayer('${escH(id)}')">□</span>
                <span class="layer-btn close" title="Cerrar" onclick="event.stopPropagation();cerrarLayer('${escH(id)}')">✕</span>
            </div>
        </div>
        <div class="layer-body">${bodyHTML}</div>
        <div class="layer-resize-handle" id="layer-rsz-${escH(id)}"></div>`;
    el.addEventListener('mousedown',  () => { el.style.zIndex = ++layerZTop; });
    el.addEventListener('touchstart', () => { el.style.zIndex = ++layerZTop; }, { passive: true });
    document.getElementById('pm-windows-container').appendChild(el);
    layerStore[id] = { el, url: content, title, minimized: false, maximized: false };
    _initLayerDrag(id); _initLayerResize(id);
}
function cerrarLayer(id) { layerStore[id]?.el.remove(); delete layerStore[id]; }
function toggleMinLayer(id) {
    const l = layerStore[id]; if (!l) return;
    l.minimized = !l.minimized;
    l.el.classList.toggle('layer-minimized', l.minimized);
}
function toggleMaxLayer(id) {
    const l = layerStore[id]; if (!l) return;
    l.maximized = !l.maximized;
    if (l.maximized) {
        l._prev = { w: l.el.style.width, h: l.el.style.height, x: l.el.style.left, y: l.el.style.top };
        l.el.style.cssText += ';width:100vw;height:100vh;left:0;top:0';
    } else {
        l.el.style.width = l._prev.w; l.el.style.height = l._prev.h;
        l.el.style.left  = l._prev.x; l.el.style.top    = l._prev.y;
    }
    l.el.classList.toggle('layer-maximized', l.maximized);
}
function _initLayerDrag(id) {
    const l   = layerStore[id];
    const hdr = document.getElementById('layer-hdr-' + id);
    if (!hdr) return;
    let dragging = false, sx = 0, sy = 0, ox = 0, oy = 0;
    function xy(e) { return e.touches ? { x: e.touches[0].clientX, y: e.touches[0].clientY } : { x: e.clientX, y: e.clientY }; }
    function onStart(e) {
        if (l.maximized || e.target.closest('.layer-btn')) return;
        dragging = true;
        const r = l.el.getBoundingClientRect(); ox = r.left; oy = r.top;
        sx = xy(e).x; sy = xy(e).y; e.preventDefault();
    }
    function onMove(e) {
        if (!dragging) return;
        const p = xy(e);
        l.el.style.left = Math.max(0, Math.min(window.innerWidth  - l.el.offsetWidth,  ox + p.x - sx)) + 'px';
        l.el.style.top  = Math.max(0, Math.min(window.innerHeight - l.el.offsetHeight, oy + p.y - sy)) + 'px';
        e.preventDefault();
    }
    function onEnd() { dragging = false; }
    hdr.addEventListener('mousedown', onStart);
    hdr.addEventListener('touchstart', onStart, { passive: false });
    document.addEventListener('mousemove', onMove);
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('mouseup', onEnd);
    document.addEventListener('touchend', onEnd);
}
function _initLayerResize(id) {
    const l      = layerStore[id];
    const handle = document.getElementById('layer-rsz-' + id);
    if (!handle) return;
    let dragging = false, sx = 0, sy = 0, sw = 0, sh = 0;
    const MIN = 200;
    function xy(e) { return e.touches ? { x: e.touches[0].clientX, y: e.touches[0].clientY } : { x: e.clientX, y: e.clientY }; }
    function onStart(e) {
        if (l.maximized) return;
        dragging = true; sx = xy(e).x; sy = xy(e).y;
        sw = l.el.offsetWidth; sh = l.el.offsetHeight;
        e.preventDefault(); e.stopPropagation();
    }
    function onMove(e) {
        if (!dragging) return;
        const p = xy(e);
        l.el.style.width  = Math.max(MIN, sw + p.x - sx) + 'px';
        l.el.style.height = Math.max(MIN, sh + p.y - sy) + 'px';
        e.preventDefault();
    }
    function onEnd() { dragging = false; }
    handle.addEventListener('mousedown', onStart);
    handle.addEventListener('touchstart', onStart, { passive: false });
    document.addEventListener('mousemove', onMove);
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('mouseup', onEnd);
    document.addEventListener('touchend', onEnd);
}

/* ═══════════════════════════════════════════════════════════════════════
   SISTEMA DE SKINS
═══════════════════════════════════════════════════════════════════════ */
const SKINS = ['default', 'matrix', 'light', 'retro', 'neon'];
function setSkin(name) {
    document.documentElement.setAttribute('data-skin', name);
    localStorage.setItem('goyim_skin', name);
}
function _crearSkinLink() {
    const link = document.createElement('link');
    link.rel = 'stylesheet'; link.id = 'skin-css';
    document.head.appendChild(link);
    return link;
}
(function _loadSkin() {
    const saved = localStorage.getItem('goyim_skin');
    if (saved && SKINS.includes(saved)) setSkin(saved);
})();
