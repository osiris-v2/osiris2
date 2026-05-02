#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          OSIRIS · SSH/SFTP Module  (sftp.py)                    ║
║          Cargado via: core.dynmodule("lib.gemini.sftp", "SSHC") ║
╠══════════════════════════════════════════════════════════════════╣
║  COMANDOS desde mistral2.py (--sshc):                           ║
║                                                                  ║
║  --sshc                → conectar + mostrar estado              ║
║  --sshc <cmd>          → ejecutar comando remoto                ║
║  --sshc --gui          → aplique SFTP completo                  ║
║  --sshc --tunnel       → aplique gestor de túneles              ║
║  --sshc --monitor      → aplique monitoreo en vivo              ║
║  --sshc --editor       → aplique editor de archivos remotos     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import getpass
import json
import logging
import os
import stat
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

import paramiko

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_FILE = ".sftp_config.json"

# ══════════════════════════════════════════════════════════════════
#  TEMA OSIRIS
# ══════════════════════════════════════════════════════════════════
THEME = {
    "bg":        "#0d0f14",
    "bg2":       "#151820",
    "bg3":       "#1c2030",
    "accent":    "#00d4ff",
    "accent2":   "#7c3aed",
    "green":     "#00ff9d",
    "red":       "#ff4060",
    "yellow":    "#ffd700",
    "fg":        "#c8d0e0",
    "fg2":       "#6b7a99",
    "border":    "#2a3050",
    "font_mono": ("Courier", 10),
    "font_ui":   ("Segoe UI", 10),
    "font_head": ("Segoe UI", 12, "bold"),
}


def _apply_theme():
    s = ttk.Style()
    try:
        s.theme_use("clam")
    except Exception:
        pass
    bg, bg2, bg3 = THEME["bg"], THEME["bg2"], THEME["bg3"]
    fg, acc, bdr = THEME["fg"], THEME["accent"], THEME["border"]
    s.configure(".", background=bg, foreground=fg, fieldbackground=bg2,
                 bordercolor=bdr, troughcolor=bg3, selectbackground=acc,
                 selectforeground=bg, font=THEME["font_ui"], relief="flat")
    s.configure("TFrame",      background=bg)
    s.configure("TLabel",      background=bg, foreground=fg)
    s.configure("TEntry",      fieldbackground=bg2, foreground=fg,
                               insertcolor=acc, bordercolor=bdr)
    s.configure("TButton",     background=bg3, foreground=acc,
                               bordercolor=acc, padding=(10, 5))
    s.map("TButton",
          background=[("active", bg2)], foreground=[("active", THEME["green"])])
    s.configure("TNotebook",   background=bg, bordercolor=bdr, tabmargins=0)
    s.configure("TNotebook.Tab", background=bg3, foreground=THEME["fg2"],
                 padding=(14, 6))
    s.map("TNotebook.Tab",
          background=[("selected", bg2)], foreground=[("selected", acc)])
    s.configure("Treeview",    background=bg2, foreground=fg,
                               fieldbackground=bg2, rowheight=22)
    s.configure("Treeview.Heading", background=bg3, foreground=acc,
                font=(THEME["font_ui"][0], 9, "bold"))
    s.map("Treeview", background=[("selected", THEME["accent2"])])
    s.configure("TLabelframe", background=bg, bordercolor=bdr)
    s.configure("TLabelframe.Label", background=bg, foreground=acc,
                font=(THEME["font_ui"][0], 9, "bold"))
    s.configure("TProgressbar", background=acc, troughcolor=bg3)


# ══════════════════════════════════════════════════════════════════
#  ASYNC WORKER THREAD  (singleton global)
# ══════════════════════════════════════════════════════════════════
class _AsyncWorker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True, name="sftp-async")
        self._loop = None
        self._ready = threading.Event()

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        self._loop.run_forever()

    def submit(self, coro, callback=None):
        self._ready.wait()

        async def _wrap():
            try:
                result = await coro
            except Exception as e:
                result = e
            if callback:
                callback(result)

        asyncio.run_coroutine_threadsafe(_wrap(), self._loop)


_WORKER = _AsyncWorker()
_WORKER.start()


# ══════════════════════════════════════════════════════════════════
#  SSH CONNECTOR  (singleton)
# ══════════════════════════════════════════════════════════════════
class SSHConnector:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized    = True
        self.client          = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sftp_client     = None
        self.connected       = False
        self._session_id     = None
        self._tunnels        = {}
        self._command_history = []
        self._connection_details = {}
        self._connect_time   = None
        self._load_config()

    # ── Config ────────────────────────────────────────────────────

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    self._connection_details = json.load(f)
            except Exception as e:
                logger.warning("Config load: %s", e)

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self._connection_details, f, indent=2)
        except Exception as e:
            logger.warning("Config save: %s", e)

    def update_credentials(self, hostname, port, username, password, initial_dir=None):
        self._connection_details.update(
            hostname=hostname, port=int(port), username=username,
            password=password, initial_dir=initial_dir or None)
        self._save_config()

    # ── Sync helper ───────────────────────────────────────────────

    def _run(self, coro):
        try:
            loop = asyncio.get_running_loop()
            return asyncio.run_coroutine_threadsafe(coro, loop).result(30)
        except RuntimeError:
            pass
        return asyncio.run(coro)

    # ── Conexión ──────────────────────────────────────────────────

    async def connect(self) -> bool:
        if self.connected and self._transport_alive():
            print("✅ Ya conectado a", self._connection_details.get("hostname"))
            return True

        d = self._connection_details
        if not (d.get("hostname") and d.get("username") and d.get("password")):
            print("─── Datos de conexión SSH ───")
            d["hostname"]    = input("IP / Hostname : ").strip()
            d["port"]        = int(input("Puerto [22]   : ").strip() or "22")
            d["username"]    = input("Usuario       : ").strip()
            d["password"]    = getpass.getpass("Contraseña    : ")
            idir             = input("Dir. inicial  : ").strip()
            d["initial_dir"] = idir or None
            self._save_config()

        try:
            print(f"🔗 Conectando a {d['hostname']}:{d.get('port',22)} como {d['username']}…")
            self.client.connect(
                hostname=d["hostname"], port=d.get("port", 22),
                username=d["username"], password=d["password"],
                timeout=15, look_for_keys=False, allow_agent=False)
            self.sftp_client   = self.client.open_sftp()
            self.connected     = True
            self._session_id   = os.urandom(6).hex()
            self._connect_time = time.time()
            self._save_config()
            print(f"✅ Conexión establecida · sesión: {self._session_id}")
            idir = d.get("initial_dir")
            if idir:
                try:
                    self.sftp_client.chdir(idir)
                except Exception:
                    pass
            return True
        except paramiko.AuthenticationException:
            print("❌ Error de autenticación.")
        except paramiko.SSHException as e:
            print(f"❌ SSH: {e}")
        except OSError as e:
            print(f"❌ Red: {e}")
        except Exception as e:
            print(f"❌ {e}")
        self.connected = False
        return False

    def sync_connect(self) -> bool:
        return self._run(self.connect())

    def _transport_alive(self) -> bool:
        t = self.client.get_transport()
        return bool(t and t.is_active())

    async def disconnect(self):
        if not self.connected:
            return
        try:
            if self.sftp_client:
                self.sftp_client.close()
                self.sftp_client = None
            self.client.close()
        except Exception:
            pass
        finally:
            self.connected     = False
            self._session_id   = None
            self._connect_time = None
            print("👋 Desconectado.")

    async def reconnect_if_broken(self) -> bool:
        if self.connected and self._transport_alive():
            return True
        self.connected = False
        return await self.connect()

    async def _sftp(self):
        if not await self.reconnect_if_broken():
            return None
        return self.sftp_client

    # ── Comandos ──────────────────────────────────────────────────

    async def execute_command(self, command: str):
        if not await self.reconnect_if_broken():
            return "", "Sin conexión", -1
        try:
            _, stdout, stderr = self.client.exec_command(command, timeout=30)
            out  = stdout.read().decode(errors="replace").strip()
            err  = stderr.read().decode(errors="replace").strip()
            code = stdout.channel.recv_exit_status()
            self._command_history.append(
                dict(cmd=command, out=out, err=err, code=code, ts=time.time()))
            return out, err, code
        except paramiko.SSHException as e:
            self.connected = False
            return "", str(e), -1
        except Exception as e:
            return "", str(e), -1

    def sync_execute(self, command: str):
        return self._run(self.execute_command(command))

    # ── SFTP ops ──────────────────────────────────────────────────

    async def list_files(self, path="."):
        sftp = await self._sftp()
        if not sftp:
            return []
        try:
            return sftp.listdir_attr(path)
        except Exception as e:
            logger.error("listdir: %s", e)
            return []

    async def upload_file(self, local_path, remote_path) -> bool:
        sftp = await self._sftp()
        if not sftp:
            return False
        try:
            sftp.put(local_path, remote_path)
            return True
        except Exception as e:
            logger.error("upload: %s", e)
            return False

    async def download_file(self, remote_path, local_path) -> bool:
        sftp = await self._sftp()
        if not sftp:
            return False
        try:
            sftp.get(remote_path, local_path)
            return True
        except Exception as e:
            logger.error("download: %s", e)
            return False

    async def remove_file(self, remote_path) -> bool:
        sftp = await self._sftp()
        if not sftp:
            return False
        try:
            sftp.remove(remote_path)
            return True
        except Exception as e:
            logger.error("remove: %s", e)
            return False

    async def rename_file(self, old, new) -> bool:
        sftp = await self._sftp()
        if not sftp:
            return False
        try:
            sftp.rename(old, new)
            return True
        except Exception as e:
            logger.error("rename: %s", e)
            return False

    async def mkdir(self, path) -> bool:
        sftp = await self._sftp()
        if not sftp:
            return False
        try:
            sftp.mkdir(path)
            return True
        except Exception as e:
            logger.error("mkdir: %s", e)
            return False

    async def read_remote_file(self, remote_path):
        sftp = await self._sftp()
        if not sftp:
            return None
        try:
            with sftp.open(remote_path, "r") as f:
                return f.read().decode(errors="replace")
        except Exception as e:
            logger.error("read: %s", e)
            return None

    async def write_remote_file(self, remote_path, content: str) -> bool:
        sftp = await self._sftp()
        if not sftp:
            return False
        try:
            with sftp.open(remote_path, "w") as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error("write: %s", e)
            return False

    async def chmod(self, remote_path, mode: int) -> bool:
        sftp = await self._sftp()
        if not sftp:
            return False
        try:
            sftp.chmod(remote_path, mode)
            return True
        except Exception as e:
            logger.error("chmod: %s", e)
            return False

    # ── Túneles ───────────────────────────────────────────────────

    async def create_tunnel(self, local_port, remote_host, remote_port) -> bool:
        if not self.connected:
            return False
        try:
            transport = self.client.get_transport()
            ch = transport.open_channel(
                "direct-tcpip",
                (remote_host, remote_port),
                ("localhost", local_port))
            self._tunnels[local_port] = {
                "channel": ch, "rhost": remote_host,
                "rport": remote_port, "ts": time.time()}
            return True
        except Exception as e:
            logger.error("tunnel: %s", e)
            return False

    async def close_tunnel(self, local_port) -> bool:
        if local_port not in self._tunnels:
            return False
        try:
            self._tunnels[local_port]["channel"].close()
            del self._tunnels[local_port]
            return True
        except Exception as e:
            logger.error("close_tunnel: %s", e)
            return False

    # ── Status ────────────────────────────────────────────────────

    def status_line(self) -> str:
        if not self.connected:
            return "⚪ Desconectado"
        d  = self._connection_details
        up = ""
        if self._connect_time:
            secs = int(time.time() - self._connect_time)
            h, r = divmod(secs, 3600); m, s = divmod(r, 60)
            up = f"  ·  up {h:02d}:{m:02d}:{s:02d}"
        return (f"🟢  {d.get('username')}@{d.get('hostname')}:{d.get('port',22)}"
                f"  ·  sesión {self._session_id}{up}"
                f"  ·  túneles: {len(self._tunnels)}")

    def print_status(self):
        print(self.status_line())
        for lp, t in self._tunnels.items():
            print(f"   🚇  :{lp} → {t['rhost']}:{t['rport']}")


# ══════════════════════════════════════════════════════════════════
#  ROOT TKINTER  (oculto, compartido)
# ══════════════════════════════════════════════════════════════════
_root_lock = threading.Lock()
_root_ref  = None


def _get_root() -> tk.Tk:
    global _root_ref
    with _root_lock:
        try:
            if _root_ref is not None and _root_ref.winfo_exists():
                return _root_ref
        except Exception:
            pass
        _root_ref = tk.Tk()
        _root_ref.withdraw()
        _apply_theme()
        return _root_ref


# ══════════════════════════════════════════════════════════════════
#  BASE APLIQUE
# ══════════════════════════════════════════════════════════════════
class _BaseApp(tk.Toplevel):
    def __init__(self, connector: SSHConnector, title: str, geo: str):
        super().__init__(_get_root())
        self.connector = connector
        self.configure(bg=THEME["bg"])
        self.title(f"OSIRIS · {title}")
        self.geometry(geo)
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        # Status bar
        self._sv = tk.StringVar(value=connector.status_line())
        tk.Label(self, textvariable=self._sv, bg=THEME["bg3"],
                 fg=THEME["fg2"], font=("Courier", 8),
                 anchor="w", pady=3, padx=6).pack(side=tk.BOTTOM, fill=tk.X)
        self._tick()

    def _tick(self):
        try:
            self._sv.set(self.connector.status_line())
            self.after(1500, self._tick)
        except Exception:
            pass

    # ── Widgets helper ────────────────────────────────────────────

    def _run(self, coro, done=None):
        def _cb(r):
            if done:
                self.after(0, lambda: done(r))
        _WORKER.submit(coro, _cb)

    def _btn(self, parent, text, cmd, color=None):
        c = color or THEME["accent"]
        return tk.Button(parent, text=text, command=cmd,
                         bg=THEME["bg3"], fg=c, activebackground=THEME["bg2"],
                         activeforeground=THEME["green"], relief="flat",
                         font=(THEME["font_ui"][0], 9, "bold"),
                         padx=10, pady=4, cursor="hand2",
                         highlightthickness=1, highlightcolor=c,
                         highlightbackground=THEME["border"])

    def _entry(self, parent, width=30, show=""):
        e = tk.Entry(parent, bg=THEME["bg2"], fg=THEME["fg"],
                     insertbackground=THEME["accent"], relief="flat",
                     font=THEME["font_mono"], width=width, show=show)
        e.configure(highlightthickness=1, highlightcolor=THEME["accent"],
                    highlightbackground=THEME["border"])
        return e

    def _text(self, parent, height=10):
        t = scrolledtext.ScrolledText(
            parent, bg=THEME["bg2"], fg=THEME["fg"],
            insertbackground=THEME["accent"], relief="flat",
            font=THEME["font_mono"], height=height,
            selectbackground=THEME["accent2"])
        t.configure(highlightthickness=1, highlightbackground=THEME["border"])
        return t

    def _tag_colors(self, widget):
        widget.tag_configure("ok",   foreground=THEME["green"])
        widget.tag_configure("err",  foreground=THEME["red"])
        widget.tag_configure("info", foreground=THEME["accent"])
        widget.tag_configure("warn", foreground=THEME["yellow"])
        widget.tag_configure("dim",  foreground=THEME["fg2"])

    def _append(self, widget, text, tag=""):
        widget.configure(state="normal")
        widget.insert(tk.END, text + "\n", tag)
        widget.see(tk.END)


# ══════════════════════════════════════════════════════════════════
#  APLIQUE 1: --gui  (SFTP Manager)
# ══════════════════════════════════════════════════════════════════
class GUIApp(_BaseApp):
    def __init__(self, connector: SSHConnector):
        super().__init__(connector, "SFTP Manager", "1020x700")
        self._cwd = connector._connection_details.get("initial_dir") or "."
        self._build()
        self._refresh()

    def _build(self):
        # ── Header ────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=THEME["bg3"], pady=7, padx=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="📂  SFTP MANAGER", bg=THEME["bg3"],
                 fg=THEME["accent"], font=(THEME["font_ui"][0], 13, "bold")).pack(side=tk.LEFT)

        # ── Path bar ──────────────────────────────────────────────
        pb = tk.Frame(self, bg=THEME["bg2"], pady=4, padx=8)
        pb.pack(fill=tk.X)
        tk.Label(pb, text="Ruta:", bg=THEME["bg2"],
                 fg=THEME["fg2"], font=THEME["font_ui"]).pack(side=tk.LEFT)
        self._path_var = tk.StringVar(value=self._cwd)
        pe = tk.Entry(pb, textvariable=self._path_var, bg=THEME["bg"],
                      fg=THEME["accent"], font=THEME["font_mono"],
                      relief="flat", insertbackground=THEME["accent"])
        pe.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        pe.bind("<Return>", lambda _: self._go_path())
        for lbl, cmd in [("▶ Ir", self._go_path),
                          ("⬆ Up", self._go_up),
                          ("🔄", self._refresh)]:
            self._btn(pb, lbl, cmd).pack(side=tk.LEFT, padx=2)

        # ── Body: tree + actions ──────────────────────────────────
        body = tk.Frame(self, bg=THEME["bg"])
        body.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        cols = ("icon", "name", "size", "perms", "modified")
        self._tree = ttk.Treeview(body, columns=cols, show="headings",
                                   selectmode="browse")
        widths = {"icon": 28, "name": 320, "size": 90, "perms": 90, "modified": 140}
        heads  = {"icon": "", "name": "Nombre", "size": "Tamaño",
                  "perms": "Permisos", "modified": "Modificado"}
        for c in cols:
            self._tree.heading(c, text=heads[c])
            self._tree.column(c, width=widths[c],
                              anchor="e" if c == "size" else "w",
                              stretch=(c == "name"))
        vsb = ttk.Scrollbar(body, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.LEFT, fill=tk.Y)
        self._tree.bind("<Double-Button-1>", self._on_double)
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # Panel lateral
        panel = tk.Frame(body, bg=THEME["bg2"], width=168, padx=8, pady=10)
        panel.pack(side=tk.LEFT, fill=tk.Y, padx=(6, 0))
        panel.pack_propagate(False)
        tk.Label(panel, text="ACCIONES", bg=THEME["bg2"],
                 fg=THEME["accent"], font=(THEME["font_ui"][0], 9, "bold")).pack(pady=(0, 8))
        for lbl, cmd, col in [
            ("⬆️  Subir archivo",   self._upload,   THEME["accent"]),
            ("⬇️  Descargar",        self._download, THEME["accent"]),
            ("✏️  Renombrar",        self._rename,   THEME["yellow"]),
            ("🗑  Eliminar",         self._delete,   THEME["red"]),
            ("📁  Nueva carpeta",    self._mkdir,    THEME["green"]),
            ("🔐  Chmod",            self._chmod,    THEME["fg2"]),
        ]:
            self._btn(panel, lbl, cmd, col).pack(fill=tk.X, pady=2)

        tk.Label(panel, text="Sel:", bg=THEME["bg2"],
                 fg=THEME["fg2"], font=(THEME["font_ui"][0], 8)).pack(pady=(14, 2), anchor="w")
        self._sel_var = tk.StringVar(value="—")
        tk.Label(panel, textvariable=self._sel_var, bg=THEME["bg2"],
                 fg=THEME["green"], font=("Courier", 8),
                 wraplength=150, justify="left").pack(anchor="w")

        # Log inferior
        self._log = self._text(self, height=4)
        self._tag_colors(self._log)
        self._log.pack(fill=tk.X, padx=6, pady=(0, 4))

    # ── Navegación ────────────────────────────────────────────────

    def _refresh(self):
        self._append(self._log, f"Listando {self._cwd}…", "info")

        def _done(entries):
            self._tree.delete(*self._tree.get_children())
            if not entries or isinstance(entries, Exception):
                return
            dirs  = [e for e in entries if stat.S_ISDIR(e.st_mode)]
            files = [e for e in entries if not stat.S_ISDIR(e.st_mode)]
            for e in sorted(dirs,  key=lambda x: x.filename):
                self._tree.insert("", tk.END, values=self._row(e, True))
            for e in sorted(files, key=lambda x: x.filename):
                self._tree.insert("", tk.END, values=self._row(e, False))
            self._path_var.set(self._cwd)
            self._append(self._log, f"✅  {len(dirs)} dirs · {len(files)} archivos", "ok")

        self._run(self.connector.list_files(self._cwd), _done)

    def _row(self, e, is_dir):
        icon = "📁" if is_dir else "📄"
        try:
            mode = stat.filemode(e.st_mode)
        except Exception:
            mode = "?"
        size = "—" if is_dir else self._human(e.st_size)
        mtime = ""
        try:
            import datetime
            mtime = datetime.datetime.fromtimestamp(e.st_mtime).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass
        return (icon, e.filename, size, mode, mtime)

    @staticmethod
    def _human(n):
        for u in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {u}"
            n /= 1024
        return f"{n:.1f} TB"

    def _on_double(self, _):
        sel = self._tree.selection()
        if not sel:
            return
        vals = self._tree.item(sel[0])["values"]
        if vals[0] == "📁":
            self._cwd = self._cwd.rstrip("/") + "/" + vals[1]
            self._refresh()

    def _on_select(self, _):
        sel = self._tree.selection()
        if sel:
            self._sel_var.set(self._tree.item(sel[0])["values"][1])

    def _go_path(self):
        self._cwd = self._path_var.get().strip()
        self._refresh()

    def _go_up(self):
        p = self._cwd.rstrip("/").rsplit("/", 1)
        self._cwd = p[0] if len(p) > 1 and p[0] else "/"
        self._refresh()

    def _sel_remote(self):
        sel = self._tree.selection()
        if not sel:
            return None
        return self._cwd.rstrip("/") + "/" + self._tree.item(sel[0])["values"][1]

    # ── Acciones ──────────────────────────────────────────────────

    def _upload(self):
        local = filedialog.askopenfilename(title="Archivo local")
        if not local:
            return
        remote = self._cwd.rstrip("/") + "/" + os.path.basename(local)
        self._append(self._log, f"Subiendo {os.path.basename(local)}…", "info")

        def _done(ok):
            if ok and not isinstance(ok, Exception):
                self._append(self._log, f"✅ Subido → {remote}", "ok")
                self._refresh()
            else:
                self._append(self._log, f"❌ {ok}", "err")

        self._run(self.connector.upload_file(local, remote), _done)

    def _download(self):
        remote = self._sel_remote()
        if not remote:
            messagebox.showwarning("", "Selecciona un archivo primero.")
            return
        local = filedialog.asksaveasfilename(initialfile=os.path.basename(remote))
        if not local:
            return
        self._append(self._log, f"Descargando {os.path.basename(remote)}…", "info")

        def _done(ok):
            if ok and not isinstance(ok, Exception):
                self._append(self._log, f"✅ Guardado en {local}", "ok")
            else:
                self._append(self._log, f"❌ {ok}", "err")

        self._run(self.connector.download_file(remote, local), _done)

    def _rename(self):
        remote = self._sel_remote()
        if not remote:
            messagebox.showwarning("", "Selecciona un archivo primero.")
            return
        dlg = _InputDialog(self, "Renombrar", "Nuevo nombre:",
                           default=os.path.basename(remote))
        if not dlg.result:
            return
        new = self._cwd.rstrip("/") + "/" + dlg.result

        def _done(ok):
            if ok:
                self._append(self._log, f"✅ Renombrado → {dlg.result}", "ok")
                self._refresh()
            else:
                self._append(self._log, "❌ Error renombrando", "err")

        self._run(self.connector.rename_file(remote, new), _done)

    def _delete(self):
        remote = self._sel_remote()
        if not remote:
            messagebox.showwarning("", "Selecciona un archivo primero.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Eliminar?\n{remote}", icon="warning"):
            return

        def _done(ok):
            if ok:
                self._append(self._log, f"✅ Eliminado", "warn")
                self._refresh()
            else:
                self._append(self._log, "❌ Error eliminando", "err")

        self._run(self.connector.remove_file(remote), _done)

    def _mkdir(self):
        dlg = _InputDialog(self, "Nueva carpeta", "Nombre:")
        if not dlg.result:
            return
        path = self._cwd.rstrip("/") + "/" + dlg.result

        def _done(ok):
            if ok:
                self._append(self._log, f"✅ Carpeta: {dlg.result}", "ok")
                self._refresh()
            else:
                self._append(self._log, "❌ Error", "err")

        self._run(self.connector.mkdir(path), _done)

    def _chmod(self):
        remote = self._sel_remote()
        if not remote:
            messagebox.showwarning("", "Selecciona un archivo primero.")
            return
        dlg = _InputDialog(self, "Chmod", "Permisos octal (ej: 755):", default="755")
        if not dlg.result:
            return
        try:
            mode = int(dlg.result, 8)
        except ValueError:
            messagebox.showerror("Error", "Usa formato octal: 755, 644…")
            return

        def _done(ok):
            self._append(self._log,
                f"✅ chmod {dlg.result}" if ok else "❌ Error chmod",
                "ok" if ok else "err")

        self._run(self.connector.chmod(remote, mode), _done)


# ══════════════════════════════════════════════════════════════════
#  APLIQUE 2: --tunnel  (Tunnel Manager)
# ══════════════════════════════════════════════════════════════════
class TunnelApp(_BaseApp):
    def __init__(self, connector: SSHConnector):
        super().__init__(connector, "Tunnel Manager", "660x480")
        self._build()
        self._refresh_list()

    def _build(self):
        hdr = tk.Frame(self, bg=THEME["bg3"], pady=8, padx=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🚇  TUNNEL MANAGER", bg=THEME["bg3"],
                 fg=THEME["accent"], font=(THEME["font_ui"][0], 13, "bold")).pack(side=tk.LEFT)

        form = ttk.LabelFrame(self, text="  Nuevo Túnel  ", padding=10)
        form.pack(fill=tk.X, padx=10, pady=8)

        labels = [("Puerto local", "_lport", 8, "8080"),
                  ("Host remoto",  "_rhost", 22, "127.0.0.1"),
                  ("Puerto remoto","_rport", 8, "80")]
        for i, (lbl, attr, w, ph) in enumerate(labels):
            tk.Label(form, text=lbl + ":", bg=THEME["bg"],
                     fg=THEME["fg2"], font=THEME["font_ui"]).grid(
                row=0, column=i * 2, sticky="w", padx=(0, 4))
            e = self._entry(form, width=w)
            e.insert(0, ph)
            e.grid(row=0, column=i * 2 + 1, padx=(0, 10))
            setattr(self, attr, e)

        self._btn(form, "🚇 Crear", self._create, THEME["green"]).grid(
            row=0, column=6, padx=(10, 0))

        lf = ttk.LabelFrame(self, text="  Túneles Activos  ", padding=6)
        lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 8))

        cols = ("lport", "rhost", "rport", "desde")
        self._tun_tree = ttk.Treeview(lf, columns=cols, show="headings", height=7)
        for c, h, w in [("lport","Local",80),("rhost","Host Remoto",240),
                         ("rport","Remoto",80),("desde","Activo desde",150)]:
            self._tun_tree.heading(c, text=h)
            self._tun_tree.column(c, width=w)
        self._tun_tree.pack(fill=tk.BOTH, expand=True)

        bf = tk.Frame(lf, bg=THEME["bg"])
        bf.pack(fill=tk.X, pady=(6, 0))
        self._btn(bf, "✂️  Cerrar seleccionado", self._close_sel, THEME["red"]).pack(side=tk.LEFT)
        self._btn(bf, "🔄 Actualizar", self._refresh_list).pack(side=tk.LEFT, padx=6)

        self._log = self._text(self, height=4)
        self._tag_colors(self._log)
        self._log.pack(fill=tk.X, padx=10, pady=(0, 4))

    def _create(self):
        try:
            lp = int(self._lport.get())
            rh = self._rhost.get().strip()
            rp = int(self._rport.get())
        except ValueError:
            messagebox.showerror("Error", "Los puertos deben ser números enteros.")
            return

        def _done(ok):
            if ok and not isinstance(ok, Exception):
                self._append(self._log,
                    f"✅ Túnel: localhost:{lp} → {rh}:{rp}", "ok")
                self._refresh_list()
            else:
                self._append(self._log, f"❌ Error: {ok}", "err")

        self._run(self.connector.create_tunnel(lp, rh, rp), _done)

    def _close_sel(self):
        sel = self._tun_tree.selection()
        if not sel:
            return
        lp = int(self._tun_tree.item(sel[0])["values"][0])

        def _done(ok):
            if ok:
                self._append(self._log, f"✅ Túnel :{lp} cerrado.", "warn")
                self._refresh_list()

        self._run(self.connector.close_tunnel(lp), _done)

    def _refresh_list(self):
        self._tun_tree.delete(*self._tun_tree.get_children())
        for lp, t in self.connector._tunnels.items():
            import datetime
            since = datetime.datetime.fromtimestamp(t["ts"]).strftime("%H:%M:%S")
            self._tun_tree.insert("", tk.END,
                values=(lp, t["rhost"], t["rport"], since))


# ══════════════════════════════════════════════════════════════════
#  APLIQUE 3: --monitor  (Live Monitor)
# ══════════════════════════════════════════════════════════════════
class MonitorApp(_BaseApp):
    def __init__(self, connector: SSHConnector):
        super().__init__(connector, "Monitor", "800x580")
        self._running = True
        self._paused  = False
        self._interval = 3
        self._build()
        self._poll()

    def _build(self):
        hdr = tk.Frame(self, bg=THEME["bg3"], pady=8, padx=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="📊  LIVE MONITOR", bg=THEME["bg3"],
                 fg=THEME["accent"], font=(THEME["font_ui"][0], 13, "bold")).pack(side=tk.LEFT)
        ctrl = tk.Frame(hdr, bg=THEME["bg3"])
        ctrl.pack(side=tk.RIGHT)
        tk.Label(ctrl, text="Intervalo (s):", bg=THEME["bg3"],
                 fg=THEME["fg2"], font=THEME["font_ui"]).pack(side=tk.LEFT)
        self._int_var = tk.StringVar(value="3")
        iv = tk.Entry(ctrl, textvariable=self._int_var, width=4,
                      bg=THEME["bg2"], fg=THEME["accent"],
                      font=THEME["font_mono"], relief="flat")
        iv.pack(side=tk.LEFT, padx=4)
        self._btn(ctrl, "⏸ Pausar", self._toggle).pack(side=tk.LEFT, padx=4)

        # Tarjetas métricas
        cards_frame = tk.Frame(self, bg=THEME["bg"])
        cards_frame.pack(fill=tk.X, padx=8, pady=6)
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1)
        self._cards = {}
        for i, (key, label, color) in enumerate([
            ("cpu",  "CPU",   THEME["accent"]),
            ("ram",  "RAM",   THEME["green"]),
            ("disk", "DISCO", THEME["yellow"]),
            ("load", "LOAD",  THEME["accent2"]),
        ]):
            card = tk.Frame(cards_frame, bg=THEME["bg3"],
                            highlightthickness=1, highlightbackground=color)
            card.grid(row=0, column=i, sticky="nsew", padx=4, pady=2)
            tk.Label(card, text=label, bg=THEME["bg3"],
                     fg=color, font=(THEME["font_ui"][0], 9, "bold")).pack(pady=(6, 0))
            val = tk.Label(card, text="—", bg=THEME["bg3"],
                           fg=THEME["fg"], font=("Courier", 18, "bold"))
            val.pack(pady=(0, 6))
            self._cards[key] = val

        # Barras
        pb_frame = tk.Frame(self, bg=THEME["bg"])
        pb_frame.pack(fill=tk.X, padx=8)
        self._bars = {}
        for key, label in [("cpu", "CPU %"), ("ram", "RAM %")]:
            row = tk.Frame(pb_frame, bg=THEME["bg"])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=f"{label:<8}", bg=THEME["bg"],
                     fg=THEME["fg2"], font=("Courier", 9), width=8).pack(side=tk.LEFT)
            pb = ttk.Progressbar(row, length=200, mode="determinate")
            pb.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self._bars[key] = pb

        # Output
        lf = ttk.LabelFrame(self, text="  Salida completa  ", padding=4)
        lf.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)
        self._out = self._text(lf, height=14)
        self._tag_colors(self._out)
        self._out.pack(fill=tk.BOTH, expand=True)

    def _toggle(self):
        self._paused = not self._paused

    def _poll(self):
        if not self._running:
            return
        if self._paused:
            self.after(1000, self._poll)
            return
        try:
            self._interval = max(1, int(self._int_var.get()))
        except ValueError:
            self._interval = 3

        script = (
            "echo '=CPU='; top -bn1 | grep 'Cpu(s)' | awk '{print $2}'; "
            "echo '=RAM='; free -m | awk 'NR==2{printf \"%s %s\\n\",$3,$2}'; "
            "echo '=DISK='; df -h / | awk 'NR==2{print $5\" \"$3\"/\"$2}'; "
            "echo '=LOAD='; uptime | awk -F'load average:' '{print $2}'; "
            "echo '=PROCS='; ps aux --sort=-%cpu | head -6"
        )

        def _done(result):
            if isinstance(result, Exception):
                return
            out, err, code = result
            if code != 0:
                self._append(self._out, f"⚠️  {err}", "err")
            else:
                self._parse(out)
                self._append(self._out, f"── {time.strftime('%H:%M:%S')} ──", "dim")
                self._append(self._out, out)
            if self._running:
                self.after(self._interval * 1000, self._poll)

        self._run(self.connector.execute_command(script), _done)

    def _parse(self, text):
        section = ""
        for line in text.split("\n"):
            if line.startswith("=") and line.endswith("="):
                section = line.strip("=")
                continue
            line = line.strip()
            if not line:
                continue
            try:
                if section == "CPU":
                    pct = float(line.split()[0].replace(",", "."))
                    self._cards["cpu"].config(text=f"{pct:.1f}%")
                    self._bars["cpu"]["value"] = min(pct, 100)
                elif section == "RAM":
                    used, total = map(float, line.split())
                    pct = used / total * 100 if total else 0
                    self._cards["ram"].config(text=f"{pct:.1f}%")
                    self._bars["ram"]["value"] = min(pct, 100)
                elif section == "DISK":
                    self._cards["disk"].config(text=line.split()[0])
                elif section == "LOAD":
                    self._cards["load"].config(text=line.strip().split(",")[0])
            except Exception:
                pass

    def destroy(self):
        self._running = False
        super().destroy()


# ══════════════════════════════════════════════════════════════════
#  APLIQUE 4: --editor  (Remote File Editor)
# ══════════════════════════════════════════════════════════════════
class EditorApp(_BaseApp):
    def __init__(self, connector: SSHConnector):
        super().__init__(connector, "Remote Editor", "920x700")
        self._remote_path = None
        self._modified    = False
        self._build()

    def _build(self):
        # Toolbar
        tb = tk.Frame(self, bg=THEME["bg3"], pady=6, padx=8)
        tb.pack(fill=tk.X)
        tk.Label(tb, text="✏️  REMOTE EDITOR", bg=THEME["bg3"],
                 fg=THEME["accent"], font=(THEME["font_ui"][0], 13, "bold")).pack(side=tk.LEFT)
        for lbl, cmd, col in [
            ("📂 Abrir",       self._open_dlg, THEME["accent"]),
            ("💾 Guardar",     self._save,     THEME["green"]),
            ("💾 Guardar como",self._save_as,  THEME["yellow"]),
            ("🗑 Limpiar",     self._clear,    THEME["fg2"]),
        ]:
            self._btn(tb, lbl, cmd, col).pack(side=tk.LEFT, padx=3)

        # Path bar
        pbar = tk.Frame(self, bg=THEME["bg2"], pady=3, padx=8)
        pbar.pack(fill=tk.X)
        tk.Label(pbar, text="Archivo:", bg=THEME["bg2"],
                 fg=THEME["fg2"], font=THEME["font_ui"]).pack(side=tk.LEFT)
        self._path_var = tk.StringVar(value="— sin archivo —")
        self._mod_var  = tk.StringVar(value="")
        tk.Label(pbar, textvariable=self._path_var, bg=THEME["bg2"],
                 fg=THEME["accent"], font=THEME["font_mono"]).pack(side=tk.LEFT, padx=6)
        tk.Label(pbar, textvariable=self._mod_var, bg=THEME["bg2"],
                 fg=THEME["yellow"], font=THEME["font_ui"]).pack(side=tk.RIGHT)

        # Quick-open bar
        qb = tk.Frame(self, bg=THEME["bg"], pady=3, padx=8)
        qb.pack(fill=tk.X)
        tk.Label(qb, text="Ruta remota:", bg=THEME["bg"],
                 fg=THEME["fg2"], font=THEME["font_ui"]).pack(side=tk.LEFT)
        self._qpath = self._entry(qb, width=55)
        self._qpath.pack(side=tk.LEFT, padx=6)
        self._qpath.bind("<Return>", lambda _: self._load_path(self._qpath.get().strip()))
        self._btn(qb, "Cargar", lambda: self._load_path(self._qpath.get().strip())).pack(side=tk.LEFT)

        # Editor area
        ef = tk.Frame(self, bg=THEME["bg"])
        ef.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self._linenos = tk.Text(ef, width=4, bg=THEME["bg3"], fg=THEME["fg2"],
                                font=THEME["font_mono"], state="disabled",
                                relief="flat", selectbackground=THEME["bg3"])
        self._linenos.pack(side=tk.LEFT, fill=tk.Y)

        self._editor = scrolledtext.ScrolledText(
            ef, bg=THEME["bg2"], fg=THEME["fg"],
            insertbackground=THEME["accent"], relief="flat",
            font=THEME["font_mono"], undo=True,
            selectbackground=THEME["accent2"], wrap=tk.NONE)
        self._editor.configure(highlightthickness=1,
                               highlightbackground=THEME["border"])
        self._editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._editor.bind("<KeyRelease>", self._on_key)
        self._editor.bind("<Control-s>", lambda _: self._save())

        # Cursor pos
        self._pos_var = tk.StringVar(value="Ln 1  Col 1")
        tk.Label(self, textvariable=self._pos_var, bg=THEME["bg3"],
                 fg=THEME["fg2"], font=("Courier", 8),
                 anchor="e", padx=8).pack(side=tk.BOTTOM, fill=tk.X)

        self._update_linenos()

    def _on_key(self, _):
        self._modified = True
        self._mod_var.set("● modificado")
        self._update_linenos()
        pos = self._editor.index(tk.INSERT)
        ln, col = pos.split(".")
        self._pos_var.set(f"Ln {ln}  Col {int(col)+1}")

    def _update_linenos(self):
        content = self._editor.get("1.0", tk.END)
        lines   = content.count("\n")
        nums    = "\n".join(str(i) for i in range(1, lines + 2))
        self._linenos.configure(state="normal")
        self._linenos.delete("1.0", tk.END)
        self._linenos.insert("1.0", nums)
        self._linenos.configure(state="disabled")

    def _open_dlg(self):
        dlg = _InputDialog(self, "Abrir archivo remoto", "Ruta completa:")
        if dlg.result:
            self._load_path(dlg.result.strip())

    def _load_path(self, path):
        if not path:
            return
        self._path_var.set(f"⏳ {path}")

        def _done(content):
            if content is None or isinstance(content, Exception):
                messagebox.showerror("Error", f"No se pudo leer:\n{path}")
                self._path_var.set("— error —")
                return
            self._remote_path = path
            self._editor.delete("1.0", tk.END)
            self._editor.insert("1.0", content)
            self._modified = False
            self._mod_var.set("")
            self._path_var.set(path)
            self._update_linenos()

        self._run(self.connector.read_remote_file(path), _done)

    def _save(self):
        if not self._remote_path:
            self._save_as()
            return
        content = self._editor.get("1.0", tk.END)

        def _done(ok):
            if ok and not isinstance(ok, Exception):
                self._modified = False
                self._mod_var.set("✅ guardado")
                self.after(2000, lambda: self._mod_var.set(""))
            else:
                messagebox.showerror("Error", f"No se pudo guardar:\n{ok}")

        self._run(self.connector.write_remote_file(self._remote_path, content), _done)

    def _save_as(self):
        dlg = _InputDialog(self, "Guardar como", "Ruta remota:",
                           default=self._remote_path or "")
        if not dlg.result:
            return
        self._remote_path = dlg.result.strip()
        self._path_var.set(self._remote_path)
        self._save()

    def _clear(self):
        if self._modified:
            if not messagebox.askyesno("Confirmar", "¿Descartar cambios?"):
                return
        self._editor.delete("1.0", tk.END)
        self._remote_path = None
        self._modified    = False
        self._mod_var.set("")
        self._path_var.set("— sin archivo —")
        self._update_linenos()


# ══════════════════════════════════════════════════════════════════
#  DIÁLOGO DE INPUT GENÉRICO
# ══════════════════════════════════════════════════════════════════
class _InputDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt, default=""):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg=THEME["bg"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        tk.Label(self, text=prompt, bg=THEME["bg"], fg=THEME["fg"],
                 font=THEME["font_ui"], pady=10, padx=16).pack()
        self._e = tk.Entry(self, bg=THEME["bg2"], fg=THEME["fg"],
                           insertbackground=THEME["accent"],
                           font=THEME["font_mono"], width=42, relief="flat")
        self._e.pack(padx=16, pady=(0, 10))
        self._e.insert(0, default)
        self._e.select_range(0, tk.END)
        self._e.bind("<Return>", lambda _: self._ok())
        self._e.bind("<Escape>", lambda _: self.destroy())

        bf = tk.Frame(self, bg=THEME["bg"])
        bf.pack(pady=(0, 10))
        tk.Button(bf, text="OK", command=self._ok,
                  bg=THEME["accent"], fg=THEME["bg"],
                  font=(THEME["font_ui"][0], 9, "bold"),
                  relief="flat", padx=14, pady=4).pack(side=tk.LEFT, padx=6)
        tk.Button(bf, text="Cancelar", command=self.destroy,
                  bg=THEME["bg3"], fg=THEME["fg2"],
                  font=THEME["font_ui"], relief="flat", padx=10).pack(side=tk.LEFT)
        self._e.focus_set()
        self.wait_window()

    def _ok(self):
        self.result = self._e.get()
        self.destroy()


# ══════════════════════════════════════════════════════════════════
#  DISPATCH  ←  llamado desde mistral2.py vía --sshc
# ══════════════════════════════════════════════════════════════════
_APP_MAP = {
    "--gui":     GUIApp,
    "--tunnel":  TunnelApp,
    "--monitor": MonitorApp,
    "--editor":  EditorApp,
}


def _launch(AppClass, connector):
    """Abre un aplique en hilo daemon sin bloquear OSIRIS."""
    def _run():
        root = _get_root()
        app  = AppClass(connector)
        app.focus_set()
        app.lift()
        root.mainloop()
    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


def dispatch(args: list, connector: "SSHConnector | None" = None) -> str:
    """
    Punto de entrada para mistral2.py.

    El bloque --sshc de mistral2.py llama:
        result = SSHC.dispatch(args[1:], sftp_global_connector)
        conversation_context += result + "\\n"

    args  : lista de tokens después de '--sshc'
    """
    if connector is None:
        connector = SSHConnector()

    # Sin args → conectar y mostrar estado
    if not args:
        if not connector.connected:
            connector.sync_connect()
        connector.print_status()
        return connector.status_line()

    subcmd = args[0].lower()

    # ── Apliques gráficos ─────────────────────────────────────────
    if subcmd in _APP_MAP:
        if not connector.connected:
            print("⚠️  Sin conexión activa. Conecta primero con --sshc")
            return "Sin conexión activa"
        _launch(_APP_MAP[subcmd], connector)
        labels = {
            "--gui":     "GUI SFTP Manager abierto",
            "--tunnel":  "Tunnel Manager abierto",
            "--monitor": "Monitor en vivo abierto",
            "--editor":  "Editor remoto abierto",
        }
        msg = labels[subcmd]
        print(f"✅ {msg}")
        return msg

    # ── Comando remoto directo ─────────────────────────────────────
    cmd = " ".join(args)
    if not connector.connected:
        connector.sync_connect()
    out, err, code = connector.sync_execute(cmd)
    if out:
        print(out)
    if err:
        print(f"[stderr] {err}")
    print(f"[exit: {code}]")
    return out or err or f"exit: {code}"


# ══════════════════════════════════════════════════════════════════
#  STANDALONE  (python3 sftp.py [--gui|--tunnel|--monitor|--editor])
# ══════════════════════════════════════════════════════════════════
def main():
    import sys
    connector = SSHConnector()
    args = sys.argv[1:]

    if not args:
        # Sin args: conectar y abrir SFTP Manager completo
        connector.sync_connect()
        root = _get_root()
        GUIApp(connector)
        root.mainloop()
    else:
        result = dispatch(args, connector)
        print(result)
        if args[0] in _APP_MAP:
            _get_root().mainloop()


if __name__ == "__main__":
    main()
