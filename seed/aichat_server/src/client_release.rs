// ╔══════════════════════════════════════════════════════════╗
// ║         GoyCorpAI — Terminal Client v0.6                 ║
// ║         ODyN / Goyim United Corp — WebSocket TUI         ║
// ╚══════════════════════════════════════════════════════════╝
//
// DISEÑO v0.6 — scroll region limpio:
//   • SetScrollingRegion(0, rows-4) → solo esa zona hace scroll
//   • Las filas rows-3, rows-2, rows-1 son FIJAS (statusbar + separador + prompt)
//   • Todo el contenido se escribe en rows-4 dentro de la región
//   • SIN alternate screen → historial scrollable con el terminal
//   • keyboard_task (EventStream) + network_task → mpsc::UiEvent

use crossterm::{
    cursor,
    event::{Event, EventStream, KeyCode, KeyEvent, KeyModifiers},
    execute, queue,
    style::{Color, Print, ResetColor, SetForegroundColor},
    terminal::{self, ClearType},
};
use futures_util::{SinkExt, StreamExt};
use serde_json::Value;
use std::{
    io::{self, Write},
    sync::Arc,
    time::Duration,
};
use tokio::sync::{mpsc, Mutex};
use tokio_tungstenite::{connect_async, tungstenite::Message};

// ─── Colores ──────────────────────────────────────────────────────────────────
const C_TITLE:  Color = Color::Rgb { r: 0,   g: 255, b: 180 };
const C_PROMPT: Color = Color::Rgb { r: 220, g: 80,  b: 255 };
const C_SERVER: Color = Color::Rgb { r: 80,  g: 200, b: 255 };
const C_WARN:   Color = Color::Rgb { r: 255, g: 200, b: 50  };
const C_ERROR:  Color = Color::Rgb { r: 255, g: 70,  b: 70  };
const C_OK:     Color = Color::Rgb { r: 80,  g: 255, b: 130 };
const C_DIM:    Color = Color::Rgb { r: 100, g: 100, b: 130 };
const C_MENU:   Color = Color::Rgb { r: 180, g: 130, b: 255 };

// Número de filas fijas al fondo (separador + statusbar + prompt)
const FIXED_ROWS: u16 = 3;

// ─── Estado ───────────────────────────────────────────────────────────────────
struct AppState {
    host:         String,
    port:         u16,
    input_line:   String,
    is_receiving: bool,
}
impl Default for AppState {
    fn default() -> Self {
        Self { host: "127.0.0.1".into(), port: 8081,
               input_line: String::new(), is_receiving: false }
    }
}

// ─── Eventos unificados ───────────────────────────────────────────────────────
enum UiEvent {
    Key(KeyEvent),
    Resize,
    Token(String),
    StreamEnd,
    ConnError(String),
    Connected,
    Disconnected,
    Quit,
}

// ─── Dimensiones ─────────────────────────────────────────────────────────────
fn dims() -> (u16, u16) { terminal::size().unwrap_or((80, 24)) }

// ─── Zona de scroll ───────────────────────────────────────────────────────────
//
// Layout (filas, de arriba abajo):
//   0 .. rows-4  → área de scroll (contenido)   ← scroll region
//   rows-3       → línea de separación (─────)
//   rows-2       → statusbar
//   rows-1       → prompt GoyCorp ❯
//
// La "última fila de contenido" es rows-4.
// Al hacer print de contenido: movemos cursor a rows-4, \n hace scroll automático.

fn content_row(rows: u16) -> u16 { rows.saturating_sub(FIXED_ROWS + 1) }

/// Instala la scroll region. Llamar siempre que cambie el tamaño del terminal.
fn setup_scroll_region(out: &mut impl Write) {
    let (_, rows) = dims();
    // ESC [ top ; bottom r  — filas 0-based en la secuencia son 1-based
    let top    = 1u16;
    let bottom = rows.saturating_sub(FIXED_ROWS); // última fila del área de scroll (1-based)
    // Usamos la secuencia raw directamente porque crossterm no expone SetScrollingRegion
    write!(out, "\x1b[{};{}r", top, bottom).ok();
    out.flush().ok();
}

/// Resetea la scroll region a toda la pantalla (antes de menús, al salir).
fn reset_scroll_region(out: &mut impl Write) {
    write!(out, "\x1b[r").ok();
    out.flush().ok();
}

// ─── Render del área fija (statusbar + prompt) ───────────────────────────────
//
// IMPORTANTE: siempre guardamos/restauramos cursor con \x1b[s / \x1b[u
// para no interferir con la posición de escritura inline del stream.

fn redraw_fixed(out: &mut impl Write, state: &AppState) {
    let (cols, rows) = dims();

    // Guardar cursor
    write!(out, "\x1b[s").ok();

    // ── Separador rows-3 ──
    queue!(out,
        cursor::MoveTo(0, rows.saturating_sub(3)),
        terminal::Clear(ClearType::CurrentLine),
        SetForegroundColor(C_DIM),
        Print("─".repeat(cols as usize)),
        ResetColor
    ).ok();

    // ── Statusbar rows-2 ──
    let rx  = if state.is_receiving { "● RX " } else { "     " };
    let bar = format!(
        " {}:{}  {} │ F9:Ayuda  F2:Conexión  F3:Modelos  F4:Info  F5:LimpiarCtx  F6:Limit  F7:TV  F10:Salir  ^C:Stop",
        state.host, state.port, rx
    );
    let bar = if bar.len() > cols as usize { &bar[..cols as usize] } else { &bar };
    queue!(out,
        cursor::MoveTo(0, rows.saturating_sub(2)),
        terminal::Clear(ClearType::CurrentLine),
        SetForegroundColor(C_MENU), Print(bar), ResetColor
    ).ok();

    // ── Prompt rows-1 ──
    let max_input = cols.saturating_sub(11) as usize;
    let visible_input = if state.input_line.len() > max_input {
        &state.input_line[state.input_line.len() - max_input..]
    } else {
        &state.input_line
    };
    queue!(out,
        cursor::MoveTo(0, rows.saturating_sub(1)),
        terminal::Clear(ClearType::CurrentLine),
        SetForegroundColor(C_PROMPT), Print("GoyCorp ❯ "),
        SetForegroundColor(Color::White), Print(visible_input), ResetColor
    ).ok();

    // Restaurar cursor
    write!(out, "\x1b[u").ok();
    out.flush().ok();
}

// ─── Escritura de contenido ───────────────────────────────────────────────────
//
// Para añadir una línea completa al área de scroll:
//   1. Mover a content_row (última fila del área)
//   2. \n → la scroll region hace avanzar el contenido
//   3. Escribir en content_row
//   4. Redibujar fixed (no mueve el cursor gracias a save/restore)

fn content_line(out: &mut impl Write, color: Color, prefix: &str, text: &str) {
    let (cols, rows) = dims();
    let cr = content_row(rows);

    // Mover a la última fila del área de contenido y hacer avanzar
    queue!(out,
        cursor::MoveTo(0, cr),
        Print("\n"),                         // scroll dentro de la región
        terminal::Clear(ClearType::CurrentLine),
        SetForegroundColor(color), Print(prefix),
        SetForegroundColor(Color::White)
    ).ok();

    // Escribir texto con word-wrap manual si supera el ancho
    let prefix_len = prefix.chars().count();
    let avail = (cols as usize).saturating_sub(prefix_len);
    write_wrapped(out, text, avail, prefix_len);

    queue!(out, ResetColor).ok();
    out.flush().ok();
}

/// Word-wrap: escribe `text` en líneas de `width` caracteres.
/// Las líneas de continuación se indentan `indent` espacios.
fn write_wrapped(out: &mut impl Write, text: &str, width: usize, indent: usize) {
    if width == 0 { queue!(out, Print(text)).ok(); return; }
    let (_cols, rows) = dims();
    let cr = content_row(rows);
    let mut remaining = text;
    let mut first = true;
    while !remaining.is_empty() {
        if !first {
            // Nueva línea dentro del área de scroll
            queue!(out,
                cursor::MoveTo(0, cr), Print("\n"),
                terminal::Clear(ClearType::CurrentLine),
                Print(" ".repeat(indent))
            ).ok();
        }
        // Corte seguro en límite de char para evitar panic con UTF-8
        let safe_end = remaining.char_indices()
            .map(|(i, _)| i)
            .filter(|&i| i <= width)
            .last()
            .unwrap_or(0);
        let safe_end = safe_end.min(remaining.len());
        let take = if remaining.len() <= width {
            remaining.len()
        } else if safe_end == 0 {
            1
        } else {
            remaining[..safe_end].rfind(' ').unwrap_or(safe_end).max(1)
        };
        let take = take.min(remaining.len());
        let (chunk, rest) = remaining.split_at(take);
        queue!(out, Print(chunk.trim_end())).ok();
        remaining = rest.trim_start_matches(' ');
        first = false;
    }
}

/// Inicia una nueva línea de stream (cabecera con icono).
/// Devuelve la columna donde debe continuar el texto.
fn stream_start(out: &mut impl Write) -> u16 {
    let (_, rows) = dims();
    let cr = content_row(rows);
    queue!(out,
        cursor::MoveTo(0, cr),
        Print("\n"),
        terminal::Clear(ClearType::CurrentLine),
//        SetForegroundColor(C_SERVER), Print("  📩  "), ResetColor
    ).ok();
    out.flush().ok();
    7 // columna de inicio (emoji ocupa 2 cols de display)
}

/// Continúa un stream inline en la posición actual.
fn stream_token(out: &mut impl Write, token: &str, col: &mut u16) {
    let (cols, rows) = dims();
    let cr = content_row(rows);

    for ch in token.chars() {
        if ch == '\n' {
            // Salto de línea explícito dentro del stream
            queue!(out,
                cursor::MoveTo(0, cr), Print("\n"),
                terminal::Clear(ClearType::CurrentLine),
                SetForegroundColor(C_SERVER), Print("     "), ResetColor
            ).ok();
            *col = 5;
        } else {
            if *col >= cols.saturating_sub(1) {
                // Wrap automático al llegar al borde
                queue!(out,
                    cursor::MoveTo(0, cr), Print("\n"),
                    terminal::Clear(ClearType::CurrentLine),
                    SetForegroundColor(C_SERVER), Print("     "), ResetColor
                ).ok();
                *col = 5;
            }
            queue!(out, SetForegroundColor(C_SERVER), Print(ch), ResetColor).ok();
            *col += 1;
        }
    }
    out.flush().ok();
}

// ─── Banner ───────────────────────────────────────────────────────────────────

fn print_banner(out: &mut impl Write) {
    let (_, rows) = dims();
    let cr = content_row(rows);
    // Imprimir banner en las primeras filas del área de scroll
    queue!(out, cursor::MoveTo(0, 0), SetForegroundColor(C_TITLE),
        Print("  ╔══════════════════════════════════════════════════════╗\r\n"),
        Print("  ║         GoyCorpAI  ·  Terminal Client v0.6           ║\r\n"),
        Print("  ║              ODyN · Goyim United Corp                ║\r\n"),
        Print("  ╚══════════════════════════════════════════════════════╝\r\n"),
        ResetColor
    ).ok();
    // Colocar cursor al final del área de scroll para que los print_line vayan bien
    queue!(out, cursor::MoveTo(0, cr)).ok();
    out.flush().ok();
}

// ─── Menús síncronos ──────────────────────────────────────────────────────────
// Siempre: reset_scroll_region → disable_raw → show cursor → menú
//          → enable_raw → hide cursor → setup_scroll_region → redraw

fn show_help_sync(out: &mut impl Write) {
    execute!(out, terminal::Clear(ClearType::All), cursor::MoveTo(0, 0)).ok();
    for line in &[
        "",
        "  ╔══════════════════════════════════════════════════╗",
        "  ║           AYUDA — GoyCorpAI Client v0.6          ║",
        "  ╠══════════════════════════════════════════════════╣",
        "  ║  F9   → Ayuda           F2  → Conexión           ║",
        "  ║  F3   → /models         F4  → /info              ║",
        "  ║  F5   → /clearcontext   F6  → /limit             ║",
        "  ║  F7   → /listtv         F10 → Salir              ║",
        "  ║  ^C   → /stop (abortar generación actual)        ║",
        "  ║  ↑/↓  → Historial de comandos                    ║",
        "  ║  ^U   → Borrar línea de input                    ║",
        "  ║                                                  ║",
        "  ║  COMANDOS: /help /stop /clearcontext /models     ║",
        "  ║  /model N /limit /info /listtv /servers /hello   ║",
        "  ║                                                  ║",
        "  ║  El historial es scrollable con el terminal.     ║",
        "  ║                                                  ║",
        "  ║  Pulsa cualquier tecla para volver...            ║",
        "  ╚══════════════════════════════════════════════════╝",
    ] {
        execute!(out, SetForegroundColor(C_MENU), Print(line), Print("\r\n"), ResetColor).ok();
    }
    out.flush().ok();
    loop { if crossterm::event::read().is_ok() { break; } }
}

fn show_connection_menu_sync(out: &mut impl Write, s: &mut AppState) -> bool {
    execute!(out, terminal::Clear(ClearType::All), cursor::MoveTo(0, 0),
        SetForegroundColor(C_TITLE),
        Print("  ╔═══════════════════════════════╗\r\n"),
        Print("  ║     CONFIGURAR CONEXIÓN       ║\r\n"),
        Print("  ╚═══════════════════════════════╝\r\n\r\n"),
        SetForegroundColor(C_DIM),
        Print(format!("  Actual: {}:{}\r\n\r\n", s.host, s.port)),
        SetForegroundColor(C_MENU),
        Print("  [1] Localhost    (127.0.0.1:8081)\r\n"),
        Print("  [2] vtwitt.com   (vtwitt.com:8081)\r\n"),
        Print("  [3] Introducir host\r\n"),
        Print("  [4] Introducir IP:puerto\r\n"),
        SetForegroundColor(C_DIM), Print("  [Esc] Cancelar\r\n\r\n"),
        SetForegroundColor(Color::Rgb{r:255,g:160,b:50}), Print("  Opción: "),
        ResetColor
    ).ok();
    out.flush().ok();

    loop {
        if let Ok(Event::Key(KeyEvent { code, .. })) = crossterm::event::read() {
            match code {
                KeyCode::Char('1') => { s.host="127.0.0.1".into(); s.port=8081; return true; }
                KeyCode::Char('2') => { s.host="vtwitt.com".into(); s.port=8081; return true; }
                KeyCode::Char('3') => {
                    execute!(out, Print("\r\n"),
                        SetForegroundColor(Color::Rgb{r:255,g:160,b:50}),
                        Print("  Host: "), ResetColor).ok();
                    out.flush().ok();
                    let h = read_line_raw_sync(out, 8);
                    if !h.is_empty() { s.host = h; }
                    return true;
                }
                KeyCode::Char('4') => {
                    execute!(out, Print("\r\n"),
                        SetForegroundColor(Color::Rgb{r:255,g:160,b:50}),
                        Print("  IP:Puerto: "), ResetColor).ok();
                    out.flush().ok();
                    let raw = read_line_raw_sync(out, 13);
                    if let Some((h, p)) = raw.rsplit_once(':') {
                        if let Ok(port) = p.trim().parse::<u16>() {
                            s.host = h.trim().to_string();
                            s.port = port;
                        }
                    }
                    return true;
                }
                KeyCode::Esc => return false,
                _ => {}
            }
        }
    }
}

fn read_line_raw_sync(out: &mut impl Write, col: u16) -> String {
    let mut buf = String::new();
    loop {
        match crossterm::event::read() {
            Ok(Event::Key(KeyEvent { code, .. })) => {
                match code {
                    KeyCode::Enter     => { write!(out, "\r\n").ok(); out.flush().ok(); break; }
                    KeyCode::Backspace => { buf.pop(); }
                    KeyCode::Char(c)   => buf.push(c),
                    KeyCode::Esc       => { buf.clear(); break; }
                    _                  => continue,
                }
                queue!(out,
                    cursor::MoveToColumn(col),
                    terminal::Clear(ClearType::UntilNewLine),
                    SetForegroundColor(Color::White),
                    Print(&buf),
                    ResetColor
                ).ok();
                out.flush().ok();
            }
            _ => {}
        }
    }
    buf.trim().to_string()
}
// ─── Conexión WebSocket ───────────────────────────────────────────────────────

async fn try_connect(host: &str, port: u16)
    -> Option<tokio_tungstenite::WebSocketStream<
        tokio_tungstenite::MaybeTlsStream<tokio::net::TcpStream>>>
{
    let url = format!("ws://{}:{}", host, port);
    tokio::time::timeout(Duration::from_secs(5), connect_async(&url))
        .await.ok()?.ok().map(|(ws, _)| ws)
}

// ─── Tarea de red ─────────────────────────────────────────────────────────────

async fn network_task(
    ws: tokio_tungstenite::WebSocketStream<
        tokio_tungstenite::MaybeTlsStream<tokio::net::TcpStream>>,
    ui_tx: mpsc::UnboundedSender<UiEvent>,
    mut cmd_rx: mpsc::UnboundedReceiver<String>,
) {
    let (write_half, mut read_half) = ws.split();
    let write_arc = Arc::new(Mutex::new(write_half));
    let _ = ui_tx.send(UiEvent::Connected);

    let wc  = Arc::clone(&write_arc);
    let tx2 = ui_tx.clone();
    tokio::spawn(async move {
        while let Some(msg) = cmd_rx.recv().await {
            if wc.lock().await.send(Message::Text(msg)).await.is_err() {
                let _ = tx2.send(UiEvent::ConnError("Error al enviar.".into()));
                break;
            }
        }
    });

    while let Some(item) = read_half.next().await {
        match item {
            Ok(Message::Text(text)) => {
                // Widget JSON
                if text.trim_start().starts_with('{') {
                    if let Ok(v) = serde_json::from_str::<Value>(&text) {
                        for line in render_widget(&v) {
                            let _ = ui_tx.send(UiEvent::Token(format!("{}\n", line)));
                        }
                        let _ = ui_tx.send(UiEvent::StreamEnd);
                        continue;
                    }
                }
                let ends = text.ends_with('\n') || text == "\n";
                let _ = ui_tx.send(UiEvent::Token(text));
                if ends { let _ = ui_tx.send(UiEvent::StreamEnd); }
            }
            Ok(Message::Close(_)) | Err(_) => {
                let _ = ui_tx.send(UiEvent::Disconnected);
                break;
            }
            _ => {}
        }
    }
}

// ─── Tarea de teclado ─────────────────────────────────────────────────────────

async fn keyboard_task(ui_tx: mpsc::UnboundedSender<UiEvent>) {
    let mut reader = EventStream::new();
    loop {
        match reader.next().await {
            Some(Ok(Event::Key(k)))     => { if ui_tx.send(UiEvent::Key(k)).is_err() { break; } }
            Some(Ok(Event::Resize(..))) => { let _ = ui_tx.send(UiEvent::Resize); }
            Some(Err(_)) | None         => { let _ = ui_tx.send(UiEvent::Quit); break; }
            _                           => {}
        }
    }
}

// ─── Widgets JSON ─────────────────────────────────────────────────────────────

fn render_widget(v: &Value) -> Vec<String> {
    let widget = v["widget"].as_str().unwrap_or("unknown");
    let d = &v["data"];
    let mut o: Vec<String> = Vec::new();
    match widget {
        "welcome" => {
            o.push("\n╔── Bienvenido ───────────────────────────────────────╗".into());
            o.push(format!("║  ID     : {}", d["id"].as_str().unwrap_or("?")));
            o.push(format!("║  Modelo : {}", d["model"].as_str().unwrap_or("?")));
            o.push(format!("║  {}", d["message"].as_str().unwrap_or("")));
            o.push("╚─────────────────────────────────────────────────────╝".into());
        }
        "info" => {
            let srv = &d["server"]; let ram = &d["ram"]; let ses = &d["session"];
            let pct = ram["used_pct"].as_u64().unwrap_or(0);
            let f   = (pct as usize * 24) / 100;
            let bar = format!("{}{}", "█".repeat(f), "░".repeat(24 - f));
            o.push("\n╔── /info ─────────────────────────────────────────────╗".into());
            o.push(format!("║  {}", d["datetime"].as_str().unwrap_or("")));
            o.push(format!("║  Uptime srv: {}  OS: {}", srv["uptime"].as_str().unwrap_or("?"), srv["uptime_os"].as_str().unwrap_or("?")));
            o.push(format!("║  Clientes: {}  IA activas: {}/{}", srv["clients"].as_u64().unwrap_or(0), srv["ai_active"].as_u64().unwrap_or(0), srv["ai_max"].as_u64().unwrap_or(0)));
            o.push(format!("║  RAM {}/{}MB  [{}] {}%", ram["used_mb"].as_u64().unwrap_or(0), ram["total_mb"].as_u64().unwrap_or(0), bar, pct));
            o.push(format!("║  Sesión: {}  Modelo: {}", ses["id"].as_str().unwrap_or("?"), ses["model"].as_str().unwrap_or("?")));
            o.push(format!("║  Conectado: {}  Mensajes: {}  Turnos: {}", ses["connected_since"].as_str().unwrap_or("?"), ses["messages"].as_u64().unwrap_or(0), ses["context_turns"].as_u64().unwrap_or(0)));
            o.push("╚─────────────────────────────────────────────────────╝".into());
        }
        "models" => {
            o.push(format!("\n╔── Modelos Ollama — libre {}MB / {}MB ──╗",
                d["ram_available_mb"].as_u64().unwrap_or(0), d["ram_total_mb"].as_u64().unwrap_or(0)));
            if let Some(ms) = d["models"].as_array() {
                for m in ms {
                    let tag  = if m["in_ram"].as_bool().unwrap_or(false) { "🟢" } else if m["fits_ram"].as_bool().unwrap_or(true) { "✓ " } else { "⚠️" };
                    let mark = if m["active"].as_bool().unwrap_or(false) { "▶" } else { "  " };
                    o.push(format!("║  {:>2}. {} {}  {}", m["index"].as_u64().unwrap_or(0), mark, m["name"].as_str().unwrap_or("?"), tag));
                }
            }
            o.push("║  Cambia con: /model N".into());
            o.push("╚─────────────────────────────────────────────────────╝".into());
        }
        "tv_channels" => {
            o.push("\n╔── Canales TV ───────────────────────────────────────╗".into());
            if let Some(chs) = d["channels"].as_array() {
                for ch in chs { o.push(format!("║  📺  {}  {}", ch["canal"].as_str().unwrap_or("?"), ch["url"].as_str().unwrap_or("?"))); }
            }
            o.push("╚─────────────────────────────────────────────────────╝".into());
        }
        "servers" => {
            o.push("\n╔── Servidores remotos ───────────────────────────────╗".into());
            if let Some(ss) = d["servers"].as_array() {
                for s in ss { o.push(format!("║  🖥  {}", s["host"].as_str().unwrap_or("?"))); }
            }
            o.push("╚─────────────────────────────────────────────────────╝".into());
        }
        _ => { o.push(format!("[widget:{}] {}", widget, serde_json::to_string_pretty(d).unwrap_or_default())); }
    }
    o
}

// ─── MAIN ─────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() {
    let mut stdout = io::stdout();
    terminal::enable_raw_mode().expect("No se pudo activar raw mode");

    // Panic hook: limpiar scroll region y raw mode
    let hook = std::panic::take_hook();
    std::panic::set_hook(Box::new(move |info| {
        let mut o = io::stdout();
        write!(o, "\x1b[r").ok(); // reset scroll region
        let _ = terminal::disable_raw_mode();
        let _ = execute!(o, cursor::Show);
        hook(info);
    }));

    execute!(stdout,
        terminal::Clear(ClearType::All),
        cursor::Hide
    ).ok();

    setup_scroll_region(&mut stdout);

    if let Err(e) = run_app(&mut stdout).await {
        reset_scroll_region(&mut stdout);
        terminal::disable_raw_mode().ok();
        execute!(stdout, cursor::Show).ok();
        eprintln!("\r\nError: {}", e);
        return;
    }

    reset_scroll_region(&mut stdout);
    terminal::disable_raw_mode().ok();
    execute!(stdout, cursor::Show, cursor::MoveTo(0, dims().1 - 1)).ok();
    println!("\r\nHasta luego.\r");
}

// ─── Loop principal ───────────────────────────────────────────────────────────

async fn run_app(stdout: &mut io::Stdout) -> Result<(), Box<dyn std::error::Error>> {
    let mut state = AppState::default();

    print_banner(stdout);
    redraw_fixed(stdout, &state);

    let (ui_tx, mut ui_rx) = mpsc::unbounded_channel::<UiEvent>();
    tokio::spawn(keyboard_task(ui_tx.clone()));

    let (cmd_tx_init, cmd_rx_init) = mpsc::unbounded_channel::<String>();
    let mut active_cmd_tx = cmd_tx_init;

    // Conexión inicial
    content_line(stdout, C_WARN, "  ⟳  ", &format!("Conectando a {}:{}…", state.host, state.port));
    redraw_fixed(stdout, &state);

    if let Some(ws) = try_connect(&state.host, state.port).await {
        tokio::spawn(network_task(ws, ui_tx.clone(), cmd_rx_init));
    } else {
        content_line(stdout, C_ERROR, "  ✗  ", "Sin conexión. Usa F2 para configurar el servidor.");
        redraw_fixed(stdout, &state);
    }

    let mut inline_active = false;
    let mut stream_col: u16 = 0;
    let mut cmd_history: Vec<String> = Vec::new();
    let mut history_idx: Option<usize> = None;

    while let Some(ev) = ui_rx.recv().await {
        match ev {

            // ── TECLADO ──────────────────────────────────────────────────────
            UiEvent::Key(KeyEvent { code, modifiers, .. }) => match code {

                KeyCode::F(10) => break,

                KeyCode::Char('c') if modifiers.contains(KeyModifiers::CONTROL) => {
                    let _ = active_cmd_tx.send("/stop".into());
                    if inline_active { inline_active = false; state.is_receiving = false; }
                    content_line(stdout, C_WARN, "  ⏹  ", "Enviando /stop…");
                    redraw_fixed(stdout, &state);
                }

                KeyCode::F(9) => {
                    reset_scroll_region(stdout);
                    terminal::disable_raw_mode().ok();
                    execute!(stdout, cursor::Show).ok();
                    show_help_sync(stdout);
                    terminal::enable_raw_mode().ok();
                    execute!(stdout, cursor::Hide, terminal::Clear(ClearType::All)).ok();
                    setup_scroll_region(stdout);
                    print_banner(stdout);
                    redraw_fixed(stdout, &state);
                }

                KeyCode::F(2) => {
                    reset_scroll_region(stdout);
                    terminal::disable_raw_mode().ok();
                    execute!(stdout, cursor::Show).ok();
                    let changed = show_connection_menu_sync(stdout, &mut state);
                    terminal::enable_raw_mode().ok();
                    execute!(stdout, cursor::Hide, terminal::Clear(ClearType::All)).ok();
                    setup_scroll_region(stdout);
                    print_banner(stdout);
                    if changed {
                        let (new_tx, new_rx) = mpsc::unbounded_channel::<String>();
                        active_cmd_tx = new_tx;
                        content_line(stdout, C_WARN, "  ⟳  ", &format!("Reconectando a {}:{}…", state.host, state.port));
                        redraw_fixed(stdout, &state);
                        match try_connect(&state.host, state.port).await {
                            Some(ws) => {
                                tokio::spawn(network_task(ws, ui_tx.clone(), new_rx));
                                content_line(stdout, C_OK, "  ✓  ", "Reconectado correctamente.");
                            }
                            None => content_line(stdout, C_ERROR, "  ✗  ", "Falló la reconexión."),
                        }
                    }
                    redraw_fixed(stdout, &state);
                }

                KeyCode::F(3) => { let _ = active_cmd_tx.send("/models".into());      redraw_fixed(stdout, &state); }
                KeyCode::F(4) => { let _ = active_cmd_tx.send("/info".into());         redraw_fixed(stdout, &state); }
                KeyCode::F(5) => {
                    let _ = active_cmd_tx.send("/clearcontext".into());
                    content_line(stdout, C_WARN, "  🧹  ", "Contexto e historial borrados.");
                    redraw_fixed(stdout, &state);
                }
                KeyCode::F(6) => { let _ = active_cmd_tx.send("/limit".into());        redraw_fixed(stdout, &state); }
                KeyCode::F(7) => { let _ = active_cmd_tx.send("/listtv".into());       redraw_fixed(stdout, &state); }

                KeyCode::Enter => {
                    let text = state.input_line.trim().to_string();
                    if !text.is_empty() {
                        content_line(stdout, C_PROMPT, "  ❯  ", &text);
                        cmd_history.push(text.clone());
                        history_idx = None;
                        let _ = active_cmd_tx.send(text);
                        state.input_line.clear();
                        redraw_fixed(stdout, &state);
                    }
                }

                KeyCode::Backspace => {
                    state.input_line.pop();
                    redraw_fixed(stdout, &state);
                }

                KeyCode::Up => {
                    if !cmd_history.is_empty() {
                        let i = history_idx.map(|i| i.saturating_sub(1)).unwrap_or(cmd_history.len()-1);
                        history_idx = Some(i);
                        state.input_line = cmd_history[i].clone();
                        redraw_fixed(stdout, &state);
                    }
                }

                KeyCode::Down => {
                    if let Some(i) = history_idx {
                        if i+1 < cmd_history.len() {
                            history_idx = Some(i+1);
                            state.input_line = cmd_history[i+1].clone();
                        } else {
                            history_idx = None;
                            state.input_line.clear();
                        }
                        redraw_fixed(stdout, &state);
                    }
                }

                KeyCode::Char('u') if modifiers.contains(KeyModifiers::CONTROL) => {
                    state.input_line.clear();
                    redraw_fixed(stdout, &state);
                }

                KeyCode::Char(c) => {
                    state.input_line.push(c);
                    redraw_fixed(stdout, &state);
                }

                _ => {}
            },

            UiEvent::Resize => {
                // Al redimensionar reinstalamos la scroll region y redibujamos todo
                execute!(stdout, terminal::Clear(ClearType::All)).ok();
                setup_scroll_region(stdout);
                print_banner(stdout);
                redraw_fixed(stdout, &state);
            }

            UiEvent::Quit => break,

            // ── RED ──────────────────────────────────────────────────────────
            UiEvent::Connected => {
                content_line(stdout, C_OK, "  ✓  ", "Conectado. Escribe /help para ver los comandos.");
                redraw_fixed(stdout, &state);
            }

            UiEvent::Token(tok) => {
                if !inline_active {
                    inline_active = true;
                    state.is_receiving = true;
                    stream_col = stream_start(stdout);
                    redraw_fixed(stdout, &state);
                    // Reposicionar cursor en la línea de contenido para tokens inline
                    let (_, rows) = dims();
                    queue!(stdout, cursor::MoveTo(stream_col, content_row(rows))).ok();
                    stdout.flush().ok();
                }
                stream_token(stdout, &tok, &mut stream_col);
            }

            UiEvent::StreamEnd => {
                inline_active = false;
                state.is_receiving = false;
                // Terminar la línea de stream y volver a estado limpio
                let (_, rows) = dims();
                queue!(stdout, cursor::MoveTo(0, content_row(rows))).ok();
                stdout.flush().ok();
                redraw_fixed(stdout, &state);
            }

            UiEvent::ConnError(e) => {
                inline_active = false;
                state.is_receiving = false;
                content_line(stdout, C_ERROR, "  ✗  ", &e);
                redraw_fixed(stdout, &state);
            }

            UiEvent::Disconnected => {
                inline_active = false;
                state.is_receiving = false;
                content_line(stdout, C_WARN, "  ⚠  ", "Desconectado. Usa F2 para reconectar.");
                redraw_fixed(stdout, &state);
            }
        }
    }

    Ok(())
}