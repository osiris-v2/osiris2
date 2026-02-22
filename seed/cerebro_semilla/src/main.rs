use tokio::net::TcpListener;
use tokio::io::{AsyncWriteExt, AsyncReadExt};
use tokio::process::Command;
use std::error::Error;
use std::process::Stdio;
use std::time::Duration;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::sync::atomic::{AtomicUsize, Ordering};
use console::Term;
use nix::sys::signal::{self, Signal};
use nix::unistd::Pid;
use indicatif::{ProgressBar, ProgressStyle};

// --- RECONEXION DE MODULOS OSIRIS ---
mod ai;
mod security;
mod network;
mod video;
use video::maniobra::GestorManiobra;
// Importamos el monitor y su estado atómico
use video::monitor::{self, MONITOR_F_ACTIVO};

struct VideoState {
    current_seconds: i32,
    total_seconds: i32,
    is_paused: bool,
    child_pid: Option<Pid>,
    gestor: GestorManiobra, 
    reset_time_pending: bool, // <-- Nueva bandera para el Monitor F
}

#[repr(C, packed)]
pub struct PaqueteSoberano {
    pub magic: u16,
    pub hash_verif: u32,
    pub longitud: u64,
    pub data: [u8; 4096],
}

static BYTES_SENT: AtomicUsize = AtomicUsize::new(0);
static IA_ACTIVA: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);

async fn reiniciar_flujo(st: &mut VideoState, sc: &mut tokio::net::TcpStream) {
    if let Some(pid) = st.child_pid {
        let _ = signal::kill(pid, Signal::SIGKILL);
        st.child_pid = None;
    }
    // Enviar opcode SKIP (15) con cabecera Osiris correcta
    // NOTA: los paquetes de control no llevan HMAC — session_key no disponible aqui.
    // En Fase 2C se refactorizara reiniciar_flujo para recibir la session_key.
    let skip_pkt = network::protocol::OsirisPacket::new_control_packet(
        network::protocol::opcodes::OP_SKIP
    );
    let _ = sc.write_all(skip_pkt.as_bytes()).await;
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let (tx_ai, mut rx_ai) = tokio::sync::mpsc::channel::<Vec<u8>>(10);

    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        println!("Uso: ./cerebro_semilla <URL_DE_VIDEO>");
        return Ok(());
    }
    let video_url = args[1].clone();

    // 2. RED: BINDING
    let listener_data = TcpListener::bind("0.0.0.0:2000").await?;
    let listener_ctrl = TcpListener::bind("0.0.0.0:2001").await?;
    println!("\x1b[36m[OSIRIS] Esperando Nodo en 2000/2001...\x1b[0m");
    
    let (stream_data, mut stream_ctrl) = (
        listener_data.accept().await?.0,
        listener_ctrl.accept().await?.0
    );

    stream_data.set_nodelay(true)?;
    stream_ctrl.set_nodelay(true)?;

    // ── FASE 2B: HANDSHAKE DE SESSION KEY ───────────────────────────────────
    // Generar clave de sesion unica de 32 bytes (CSPRNG del kernel)
    // Vive SOLO en RAM — nunca se escribe en disco ni en logs
    let session_key_raw = security::signer::generar_session_key();
    let session_key: Arc<[u8; 32]> = Arc::new(session_key_raw);

    // Enviar la clave al Nodo por canal CONTROL antes de cualquier video
    // Formato: 4 bytes magic "OSKY" (0x4F534B59) + 32 bytes de clave = 36 bytes
    {
        let handshake = security::signer::serializar_handshake(&session_key_raw);
        stream_ctrl.write_all(&handshake).await?;
        println!("\x1b[32m[HMAC] Session key enviada al Nodo (36 bytes, canal CONTROL)\x1b[0m");
    }
    // ────────────────────────────────────────────────────────────────────────

    let s_data = Arc::new(Mutex::new(stream_data));
    let s_ctrl = Arc::new(Mutex::new(stream_ctrl));
    
    let state = Arc::new(Mutex::new(VideoState {
        current_seconds: 0,
        total_seconds: 7200, 
        is_paused: false,
        child_pid: None,
        gestor: GestorManiobra::new(),
        reset_time_pending: false,
    }));

    // --- MONITOR EXTERNO (NUEVO) ---
    let config_monitor = Arc::new(Mutex::new(monitor::MonitorConfig::new(video_url.clone())));
    let state_for_mon = Arc::clone(&state);
    let cfg_for_mon = Arc::clone(&config_monitor);
    monitor::spawn_vigilante(cfg_for_mon, state_for_mon);

    // 3. INTERFAZ
    let pb = ProgressBar::new(7200);
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} {wide_msg} \n{elapsed_precise} [{bar:40.cyan/blue}] {pos}/{len}s ({bytes_sent} MB)")?
        .progress_chars("#>-"));

    // 4. HILO: TELEMETRIA
    let state_time = Arc::clone(&state);
    let pb_clone = pb.clone();
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(Duration::from_secs(1)).await;
            let st = state_time.lock().await;
            let mb = BYTES_SENT.load(Ordering::Relaxed) / (1024 * 1024);
            let info_filtros = if st.gestor.filtros_activos.is_empty() { "BASE" } else { "MOD" };
            pb_clone.set_position(st.current_seconds as u64);
            pb_clone.set_message(format!("V: {}k | F: {} | {:02}:{:02} | {} MB", 
                st.gestor.bitrate, info_filtros, st.current_seconds / 60, st.current_seconds % 60, mb));
        }
    });

    // 5. HILO: TRANSMISION (Motor Dinámico + IA)
    let s_data_clone = Arc::clone(&s_data);
    let state_clone = Arc::clone(&state);
    let config_monitor_clone = Arc::clone(&config_monitor);
    let tx_ai_video = tx_ai.clone();
    let session_key_tx = Arc::clone(&session_key); // clave de sesion para HMAC

    tokio::spawn(async move {
        loop {
            let (start_time_base, br, vf, input_path) = {
                let mut st = state_clone.lock().await;
                let mut cfg = config_monitor_clone.lock().await;
                cfg.requiere_reinicio = false; 

                let time_to_use = if st.reset_time_pending {
                    st.current_seconds = 0; 
                    st.reset_time_pending = false; 
                    0
                } else {
                    st.current_seconds
                };
                (time_to_use, format!("{}k", st.gestor.bitrate), st.gestor.obtener_vf(), cfg.input_actual.clone())
            };

            let mut child = Command::new("/var/osiris2/bin/com/osiris_env/ffmpeg/bin/ffmpeg")
.args([
    "-re",
    "-loglevel","panic",
    "-stream_loop","-1",
    "-ss", &start_time_base.to_string(), 
    "-i", &input_path, 
    "-af", "aresample=async=1000,compand=attacks=0.01:decays=0.1:points=-90/-30|-30/-15|0/-7", 
    "-vf", &vf, 
    "-c:v", "mpeg2video", "-b:v", &br, "-pix_fmt", "yuv420p",
    "-bf", "0",          // <--- Importante para latencia
    "-threads", "0", 
    "-fflags", "+genpts+igndts+discardcorrupt", // <--- Limpieza de stream
    "-f", "mpegts", 
    "pipe:1"
])
                .stdout(Stdio::piped()).spawn().expect("FFmpeg Fail");

            state_clone.lock().await.child_pid = child.id().map(|id| Pid::from_raw(id as i32));
            let mut ffmpeg_out = child.stdout.take().unwrap();
            let mut chunk = [0u8; 16384];
            let instante_arranque = std::time::Instant::now();

            loop {
                if let Ok(cfg) = config_monitor_clone.try_lock() {
                    if cfg.requiere_reinicio { break; }
                }

                
                // --- DENTRO DEL LOOP DE TRANSMISION ---
let n = match ffmpeg_out.read(&mut chunk).await {
    Ok(0) | Err(_) => break,
    Ok(n) => n,
};

// PROTOCOLO OSIRIS + HMAC-SHA256
                let mut pkg_osiris = network::protocol::OsirisPacket::new_video_packet(n as u32);
                // Firmar con HMAC-SHA256(session_key, header_parcial + payload)
                // signature = primeros 4 bytes del HMAC → en header.signature
                pkg_osiris.signature = security::signer::generate_signature(
                    &pkg_osiris,
                    &chunk[..n],
                    &session_key_tx,
                );

                let transcurrido = instante_arranque.elapsed().as_secs() as i32;
                if let Ok(mut st) = state_clone.try_lock() {
                    st.current_seconds = start_time_base + transcurrido;
                }

                if IA_ACTIVA.load(Ordering::Relaxed) {
                    let _ = tx_ai_video.try_send(chunk[..n].to_vec());
                }

                // 16 bytes OsirisHeader (version=2, opcode=7, HMAC en signature) + chunk
                let mut packet = Vec::with_capacity(16 + n);
                packet.extend_from_slice(pkg_osiris.as_bytes());
                packet.extend_from_slice(&chunk[..n]);

                let mut sd = s_data_clone.lock().await;
                if sd.write_all(&packet).await.is_err() { break; }
                BYTES_SENT.fetch_add(n, Ordering::Relaxed);
            }
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    });

    // 6. HILO: PROCESADOR IA
    let s_ctrl_ai = Arc::clone(&s_ctrl);
    tokio::spawn(async move {
        while let Some(data) = rx_ai.recv().await {
            let res = ai::trainer::ejecutar_entrenamiento_temporal(&data).await; 
            if res.requiere_colapso { 
                let mut sc = s_ctrl_ai.lock().await;
                let skip_pkt = network::protocol::OsirisPacket::new_control_packet(
                    network::protocol::opcodes::OP_SKIP
                );
                let _ = sc.write_all(skip_pkt.as_bytes()).await;
            }
        }
    });

    // 8. HILO: RECEPTOR DE COMANDOS ODS (Consola)
    let s_ctrl_ods = Arc::clone(&s_ctrl);
    let state_ods = Arc::clone(&state);
    tokio::spawn(async move {
        let listener_ods = TcpListener::bind("127.0.0.1:8087").await.expect("Error Bind 8087");
        loop {
            if let Ok((mut socket, _)) = listener_ods.accept().await {
                let mut buffer = [0u8; std::mem::size_of::<PaqueteSoberano>()];
                if socket.read_exact(&mut buffer).await.is_ok() {
                    let pkg: PaqueteSoberano = unsafe { std::mem::transmute(buffer) };
                    if pkg.magic == 0x256F {
                        let len = pkg.longitud as usize;
                        let orden = String::from_utf8_lossy(&pkg.data[..len]).trim().to_uppercase();
                        let mut st = state_ods.lock().await;
                        let mut sc = s_ctrl_ods.lock().await;
                        let partes: Vec<&str> = orden.split_whitespace().collect();
                        if partes.is_empty() { continue; }
                        match partes[0] {
                            "BITRATE" => { if partes.len() > 1 { if let Ok(nb) = partes[1].parse::<u32>() { st.gestor.bitrate = nb; reiniciar_flujo(&mut st, &mut sc).await; }}}
                            "FILTER" => { if partes.len() > 1 { if let Ok(id) = partes[1].parse::<usize>() { st.gestor.backup(); st.gestor.filtros_activos.push(id); reiniciar_flujo(&mut st, &mut sc).await; }}}
                            "PAUSE" => { st.is_paused = !st.is_paused; if let Some(pid) = st.child_pid { let _ = signal::kill(pid, if st.is_paused { Signal::SIGSTOP } else { Signal::SIGCONT }); }}
                            "SKIP" => { st.current_seconds += 30; reiniciar_flujo(&mut st, &mut sc).await; }
                            "BACK" => { st.current_seconds = (st.current_seconds - 30).max(0); reiniciar_flujo(&mut st, &mut sc).await; }
                            "CLEAR" => { st.gestor.filtros_activos.clear(); reiniciar_flujo(&mut st, &mut sc).await; }
                            "RESET" => { st.current_seconds = 0; st.gestor.filtros_activos.clear(); reiniciar_flujo(&mut st, &mut sc).await; }
                            _ => {}
                        }
                    }
                }
            }
        }
    });

    // 7. BUCLE DE TECLADO
    let term = Term::stdout();
    loop {
        if let Ok(key) = term.read_char() {
            let mut st = state.lock().await;
            let mut sc = s_ctrl.lock().await;
            match key {
                'f' => {
                    let estado = !MONITOR_F_ACTIVO.load(Ordering::Relaxed);
                    MONITOR_F_ACTIVO.store(estado, Ordering::Relaxed);
                    println!("\n\x1b[35m[SISTEMA] Modo Monitor F: {}\x1b[0m", if estado { "ON" } else { "OFF" });
                },
                'p' => {
                    st.is_paused = !st.is_paused;
                    if let Some(pid) = st.child_pid {
                        let _ = signal::kill(pid, if st.is_paused { Signal::SIGSTOP } else { Signal::SIGCONT });
                        let pause_pkt = network::protocol::OsirisPacket::new_control_packet(
                            network::protocol::opcodes::OP_PAUSE
                        );
                        let _ = sc.write_all(pause_pkt.as_bytes()).await;
                    }
                },
                'l' => { st.current_seconds += 30; reiniciar_flujo(&mut st, &mut sc).await; },
                'h' => { st.current_seconds = (st.current_seconds - 30).max(0); reiniciar_flujo(&mut st, &mut sc).await; },
                '+' => { st.gestor.bitrate += 500; reiniciar_flujo(&mut st, &mut sc).await; },
                '-' => { st.gestor.bitrate = (st.gestor.bitrate - 500).max(500); reiniciar_flujo(&mut st, &mut sc).await; },
                'a' => {
                    println!("\nID de filtro:");
                    let t_ini = std::time::Instant::now();
                    if let Ok(linea) = term.read_line() {
                        if let Ok(id) = linea.trim().parse::<usize>() {
                            st.current_seconds += t_ini.elapsed().as_secs() as i32;
                            st.gestor.backup(); st.gestor.filtros_activos.push(id);
                            reiniciar_flujo(&mut st, &mut sc).await;
                        }
                    }
                },
                'b' => { 
                    println!("\n\x1b[35m[SISTEMA] Modo FILTRO UNICO. Ingrese ID y pulse Enter:\x1b[0m");
                    let t_antes_de_leer = std::time::Instant::now();

                    if let Ok(linea) = term.read_line() {
                        if let Ok(id) = linea.trim().parse::<usize>() {
                            // Sincroniza el tiempo tras el Enter
                            st.current_seconds += t_antes_de_leer.elapsed().as_secs() as i32;

                            st.gestor.backup(); 
                            // Elimina los filtros anteriores y añade solo el nuevo
                            st.gestor.filtros_activos.clear(); 
                            st.gestor.filtros_activos.push(id);

                            reiniciar_flujo(&mut st, &mut sc).await;
                            println!("\x1b[32m[OK] Filtros limpiados. Solo ID {} activo en seg {}\x1b[0m", id, st.current_seconds);
                        }
                    }
                },
                'c' => { st.gestor.filtros_activos.clear(); reiniciar_flujo(&mut st, &mut sc).await; },
                'q' => { if let Some(pid) = st.child_pid { let _ = signal::kill(pid, Signal::SIGKILL); } break; },
                'i' => {
                    let s_ctrl_clone = Arc::clone(&s_ctrl);
                    tokio::spawn(async move { let _ = inyectar_adn_ia(s_ctrl_clone).await; });
                },
                // v → catálogo completo de filtros con ID y estado activo
                'v' => {
                    println!("\n\x1b[1;36m=== CATALOGO DE FILTROS OSIRIS ===\x1b[0m");
                    println!("  {:>3}  {:8}  {}", "ID", "ESTADO", "NOMBRE");
                    println!("  {}", "-".repeat(30));
                    for (id, (nombre, _vf)) in st.gestor.catalogo.iter().enumerate() {
                        let marca = if st.gestor.filtros_activos.contains(&id) {
                            "\x1b[32m[ACTIVO]\x1b[0m"
                        } else {
                            "        "
                        };
                        println!("  {:>3}  {}  {}", id, marca, nombre);
                    }
                    println!("  {}", "-".repeat(30));
                    if st.gestor.filtros_activos.is_empty() {
                        println!("  Activos: BASE (sin filtros)");
                    } else {
                        let nombres: Vec<&str> = st.gestor.filtros_activos.iter()
                            .filter_map(|&id| st.gestor.catalogo.get(id).map(|(n, _)| *n))
                            .collect();
                        println!("  Activos: {:?}", nombres);
                    }
                    println!("\x1b[1;36m==================================\x1b[0m");
                },
                // s → status rápido del sistema
                's' => {
                    let mb = BYTES_SENT.load(Ordering::Relaxed) / (1024 * 1024);
                    let nombres: Vec<&str> = if st.gestor.filtros_activos.is_empty() {
                        vec!["BASE"]
                    } else {
                        st.gestor.filtros_activos.iter()
                            .filter_map(|&id| st.gestor.catalogo.get(id).map(|(n, _)| *n))
                            .collect()
                    };
                    println!("\n\x1b[1;33m=== STATUS ===\x1b[0m");
                    println!("  Bitrate  : {}k", st.gestor.bitrate);
                    println!("  Tiempo   : {:02}:{:02}", st.current_seconds / 60, st.current_seconds % 60);
                    println!("  Pausado  : {}", st.is_paused);
                    println!("  MB tx    : {}", mb);
                    println!("  Filtros  : {:?}", nombres);
                    println!("  HMAC     : ACTIVO (SHA-256, clave de sesion)");
                    println!("\x1b[1;33m==============\x1b[0m");
                },
                // u → quitar el último filtro añadido
                'u' => {
                    if st.gestor.filtros_activos.is_empty() {
                        println!("\x1b[33m[UNDO] No hay filtros activos.\x1b[0m");
                    } else {
                        let eliminado = st.gestor.filtros_activos.pop();
                        let nombre = eliminado
                            .and_then(|id| st.gestor.catalogo.get(id))
                            .map(|(n, _)| *n).unwrap_or("?");
                        reiniciar_flujo(&mut st, &mut sc).await;
                        println!("\x1b[33m[UNDO] Eliminado: {}. Activos: {:?}\x1b[0m",
                            nombre, st.gestor.filtros_activos);
                    }
                },
                // r → rollback al estado guardado con backup()
                'r' => {
                    st.gestor.rollback();
                    reiniciar_flujo(&mut st, &mut sc).await;
                    println!("\x1b[33m[ROLLBACK] Estado restaurado.\x1b[0m");
                },
                // e / w → saltos de 5 minutos
                'e' => { st.current_seconds += 300; reiniciar_flujo(&mut st, &mut sc).await; },
                'w' => { st.current_seconds = (st.current_seconds - 300).max(0); reiniciar_flujo(&mut st, &mut sc).await; },
                // ? → ayuda
                '?' => {
                    println!("\n\x1b[1;37m======== TECLAS OSIRIS ========\x1b[0m");
                    println!("  p          Pausa / Reanuda");
                    println!("  l / h      +30s  /  -30s");
                    println!("  e / w      +5min /  -5min");
                    println!("  + / -      Bitrate +500k / -500k");
                    println!("  a          Añadir filtro (acumulativo)");
                    println!("  b          Filtro unico (reemplaza todos)");
                    println!("  c          Limpiar todos los filtros");
                    println!("  u          Deshacer ultimo filtro");
                    println!("  r          Rollback al estado guardado");
                    println!("  v          Ver catalogo de filtros");
                    println!("  s          Status del sistema");
                    println!("  f          Toggle Monitor F");
                    println!("  i          Inyectar ADN IA");
                    println!("  ?          Esta ayuda");
                    println!("  q          Salir");
                    println!("\x1b[1;37m===============================\x1b[0m");
                },
                _ => {}
            }
        }
    }
    Ok(())
}

async fn inyectar_adn_ia(s_ctrl: Arc<Mutex<tokio::net::TcpStream>>) -> Result<(), Box<dyn std::error::Error>> {
    let mut buffer_adn = [0u8; 1024];
    if let Ok(mut f) = std::fs::File::open("../bin/modelo_video_test.fgn") {
        let _ = std::io::Read::read_exact(&mut f, &mut buffer_adn);
    }
    let mut pkg = PaqueteSoberano { magic: 0x256F, hash_verif: 0, longitud: 1024, data: [0u8; 4096] };
    pkg.data[..1024].copy_from_slice(&buffer_adn);
    let mut sc = s_ctrl.lock().await;
    sc.write_all(&unsafe { std::mem::transmute::<PaqueteSoberano, [u8; std::mem::size_of::<PaqueteSoberano>()]>(pkg) }).await?;
    println!("\x1b[35m[OSIRIS] ADN IA enviado.\x1b[0m");
    Ok(())
}