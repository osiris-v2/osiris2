use tokio::net::TcpListener;
use tokio::io::{AsyncWriteExt, AsyncReadExt};
use tokio::process::Command;
use std::error::Error;
use std::process::Stdio;
use std::time::Duration;
use std::sync::Arc;
use tokio::sync::Mutex;
use std::sync::atomic::{AtomicUsize, Ordering}; // Para medir MB
use console::Term;
use nix::sys::signal::{self, Signal};
use nix::unistd::Pid;
use indicatif::{ProgressBar, ProgressStyle};



struct VideoState {
    current_seconds: i32,
    total_seconds: i32, // Duración estimada o total
    is_paused: bool,
    child_pid: Option<Pid>,
}

// Contador global de bytes transferidos
static BYTES_SENT: AtomicUsize = AtomicUsize::new(0);

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = std::env::args().collect();
    if args.len() < 2 {
        println!("Uso: ./cerebro_semilla <URL_DE_VIDEO>");
        return Ok(());
    }
    let video_url = args[1].clone();

    let listener_data = TcpListener::bind("0.0.0.0:2000").await?;
    let listener_ctrl = TcpListener::bind("0.0.0.0:2001").await?;
    
    println!("\x1b[36m[OSIRIS] Esperando Nodo en 2000/2001...\x1b[0m");
    
    let (stream_data, _) = listener_data.accept().await?;
    let (stream_ctrl, _) = listener_ctrl.accept().await?;
    
    let s_data = Arc::new(Mutex::new(stream_data));
    let s_ctrl = Arc::new(Mutex::new(stream_ctrl));
    
    // Supongamos 2h de duración por defecto si no se conoce, 
    // FFmpeg podría dárnoslo pero para el ejemplo fijamos 7200s
    let state = Arc::new(Mutex::new(VideoState {
        current_seconds: 0,
        total_seconds: 7200, 
        is_paused: false,
        child_pid: None,
    }));

    // --- INTERFAZ ---
    println!("\n\x1b[1mNODO CONECTADO - CONTROLES ACTIVOS\x1b[0m");
    println!("------------------------------------------");
    println!(" [p] Pausa/Play | [l] +30s | [h] -30s | [q] Salir");
    println!("------------------------------------------\n");

    let pb = ProgressBar::new(7200); // El total a la derecha
    pb.set_style(ProgressStyle::default_bar()
        .template("{spinner:.green} {wide_msg} \n{elapsed_precise} [{bar:40.cyan/blue}] {pos}/{len}s ({bytes_sent} MB)")?
        .progress_chars("#>-"));

    // --- HILO DE ACTUALIZACIÓN DE TELEMETRÍA ---
    let state_time = Arc::clone(&state);
    let pb_clone = pb.clone();
    tokio::spawn(async move {
        loop {
            tokio::time::sleep(Duration::from_secs(1)).await;
            let mut st = state_time.lock().await;
            if !st.is_paused {
                st.current_seconds += 1;
            }
            
            let mb = BYTES_SENT.load(Ordering::Relaxed) / (1024 * 1024);
            let mins = st.current_seconds / 60;
            let secs = st.current_seconds % 60;
            
            pb_clone.set_position(st.current_seconds as u64);
            pb_clone.set_message(format!("Streaming: {:02}:{:02} | Transmitido: {} MB", mins, secs, mb));
        }
    });

    // --- HILO DE TRANSMISIÓN (EL MOTOR) ---
    let s_data_clone = Arc::clone(&s_data);
    let state_clone = Arc::clone(&state);
    let url_clone = video_url.clone();

    tokio::spawn(async move {
        loop {
            let start_time = state_clone.lock().await.current_seconds;
            
            let mut child = Command::new("ffmpeg")
                .args([
                    "-ss", &start_time.to_string(),
                    "-re", "-loglevel", "panic",
                    "-i", &url_clone,
                    "-c:v", "mpeg1video", "-b:v", "4000k", "-preset", "ultrafast",
                    "-f", "mpegts", "-fflags", "+genpts", "pipe:1"
                ])
                .stdout(Stdio::piped())
                .stdin(Stdio::null())
                .spawn().expect("FFmpeg Fail");

            state_clone.lock().await.child_pid = child.id().map(|id| Pid::from_raw(id as i32));

            let mut ffmpeg_out = child.stdout.take().unwrap();
            let mut chunk = [0u8; 16384];

            loop {
                let n = match ffmpeg_out.read(&mut chunk).await {
                    Ok(0) | Err(_) => break,
                    Ok(n) => n,
                };
                
                // Actualizar contador de MB
                BYTES_SENT.fetch_add(n, Ordering::Relaxed);

                let mut packet = Vec::with_capacity(16 + n);
                packet.extend_from_slice(&[7u8; 12]);
                packet.extend_from_slice(&(n as u32).to_le_bytes());
                packet.extend_from_slice(&chunk[..n]);

                let mut sd = s_data_clone.lock().await;
                if sd.write_all(&packet).await.is_err() { return; }
            }
            tokio::time::sleep(Duration::from_millis(200)).await;
        }
    });



#[repr(C, packed)]
pub struct PaqueteSoberano {
    pub magic: u16,        // 0x256F
    pub hash_verif: u32,
    pub longitud: u64,
    pub data: [u8; 4096],
}



// --- HILO DE ENLACE CON NODO MUSCULO (C) ---
    let state_osiris = Arc::clone(&state);
    let s_ctrl_osiris = Arc::clone(&s_ctrl);

    tokio::spawn(async move {
        let listener = TcpListener::bind("127.0.0.1:8080").await.unwrap();
        
        loop {
            if let Ok((mut socket, _)) = listener.accept().await {
                let mut buffer = [0u8; std::mem::size_of::<PaqueteSoberano>()];
                
                if socket.read_exact(&mut buffer).await.is_ok() {
                    let pkg: PaqueteSoberano = unsafe { std::mem::transmute(buffer) };
                    
                    if pkg.magic == 0x256F {
                        let orden = String::from_utf8_lossy(&pkg.data[..pkg.longitud as usize]);
                        let mut st = state_osiris.lock().await;
                        let mut sc = s_ctrl_osiris.lock().await;

                        match orden.trim() {
                            "PAUSE" => {
                                st.is_paused = !st.is_paused;
                                if let Some(pid) = st.child_pid {
                                    let _ = signal::kill(pid, if st.is_paused { Signal::SIGSTOP } else { Signal::SIGCONT });
                                    let _ = sc.write_all(&[10u8; 12]).await;
                                }
                            },
                            "SKIP" => {
                                st.current_seconds += 30;
                                let _ = sc.write_all(&[15u8; 12]).await;
                                if let Some(pid) = st.child_pid { let _ = signal::kill(pid, Signal::SIGKILL); }
                            },
                            _ => println!("\x1b[33m[OSIRIS] Rafaga no mapeada: {}\x1b[0m", orden),
                        }
                    }
                }
            }
        }
    });


    // --- BUCLE DE TECLADO ---
    let term = Term::stdout();
    loop {
        if let Ok(key) = term.read_char() {
            let mut st = state.lock().await;
            let mut sc = s_ctrl.lock().await;

            match key {
                'p' => {
                    st.is_paused = !st.is_paused;
                    if let Some(pid) = st.child_pid {
                        let _ = signal::kill(pid, if st.is_paused { Signal::SIGSTOP } else { Signal::SIGCONT });
                        let _ = sc.write_all(&[10u8; 12]).await;
                    }
                },
                'l' => {
                    st.current_seconds += 30; // El marcador saltará en la siguiente actualización del hilo
                    let _ = sc.write_all(&[15u8; 12]).await;
                    if let Some(pid) = st.child_pid { let _ = signal::kill(pid, Signal::SIGKILL); }
                },
                'h' => {
                    st.current_seconds = (st.current_seconds - 30).max(0);
                    let _ = sc.write_all(&[15u8; 12]).await;
                    if let Some(pid) = st.child_pid { let _ = signal::kill(pid, Signal::SIGKILL); }
                },
                'q' => {
                    if let Some(pid) = st.child_pid { let _ = signal::kill(pid, Signal::SIGKILL); }
                    break;
                },
                _ => {}
            }
        }
    }

    Ok(())
}