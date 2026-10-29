import sys
import json
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QLabel, QPushButton, QFileDialog,
    QLineEdit, QRadioButton, QButtonGroup, QComboBox, QMessageBox,
    QListWidget, QListWidgetItem, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QPalette

# ─── PATHS ────────────────────────────────────────────────────────────────────
PATH_MONITOR   = "/tmp/osiris_input"
PATH_JSON      = "../bin/com/datas/ffmpeg/activos.json"
PATH_INJECT_SH = "./videourl.sh"
PATH_FAVORITES = os.path.expanduser("~/.osiris_favorites.json")

# ─── PALETA NOCHE ESTRELLADA ──────────────────────────────────────────────────
BG      = "#0d0f1a"
BG2     = "#111320"
SURF    = "#161829"
CARD    = "#1a1d30"
BORDER  = "#252840"
BORDER2 = "#2e3250"
ACCENT  = "#7c9eff"
ACCENT2 = "#a78bfa"
STAR    = "#e8eaff"
DIM     = "#4a5080"
MUTED   = "#6b74a0"
TEXT    = "#d4d8f0"
TEXT2   = "#9098c0"
SUCCESS = "#5dd8a0"
DANGER  = "#f06080"
GOLD    = "#f0c060"

APP_SS = f"""
QMainWindow, QWidget#Root {{ background: {BG}; }}
QWidget {{ background: transparent; color: {TEXT}; }}
QScrollArea {{ border: none; background: {BG}; }}
QScrollArea > QWidget > QWidget {{ background: {BG}; }}
QScrollBar:vertical {{
    background: {BG2}; width: 5px; margin: 0; border-radius: 3px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER2}; border-radius: 3px; min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {DIM}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QLineEdit {{
    background: {SURF}; color: {TEXT};
    border: 1px solid {BORDER2}; border-radius: 5px;
    padding: 5px 9px; font-size: 11px;
    selection-background-color: {ACCENT}; selection-color: {BG};
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QComboBox {{
    background: {SURF}; color: {TEXT};
    border: 1px solid {BORDER2}; border-radius: 5px;
    padding: 4px 8px; font-size: 10px; min-height: 24px;
}}
QComboBox:focus {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 14px; }}
QComboBox QAbstractItemView {{
    background: {SURF}; color: {TEXT};
    border: 1px solid {BORDER2};
    selection-background-color: {ACCENT}; selection-color: {BG};
    outline: none;
}}
QPushButton {{
    background: {SURF}; color: {TEXT2};
    border: 1px solid {BORDER2}; border-radius: 5px;
    padding: 3px 9px; font-size: 10px;
}}
QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton:pressed {{ background: {CARD}; }}
QPushButton:disabled {{ color: {DIM}; border-color: {BORDER}; }}
QRadioButton {{
    color: {MUTED}; font-size: 10px; spacing: 3px;
}}
QRadioButton:checked {{ color: {ACCENT}; }}
QRadioButton::indicator {{
    width: 10px; height: 10px; border-radius: 5px;
    border: 1px solid {DIM}; background: {BG2};
}}
QRadioButton::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QStatusBar {{
    color: {MUTED}; background: {SURF};
    border-top: 1px solid {BORDER}; font-size: 10px; padding: 2px 6px;
}}
QListWidget {{
    background: {BG2}; border: 1px solid {BORDER};
    border-radius: 5px; outline: none; padding: 2px;
}}
QListWidget::item {{
    color: {TEXT2}; padding: 5px 8px; border-radius: 4px; font-size: 10px;
}}
QListWidget::item:selected {{
    background: {CARD}; color: {ACCENT};
}}
QListWidget::item:hover:!selected {{ background: {SURF}; }}
"""

CARD_BASE = f"""
#CanalCard {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-left: 3px solid LEFTCOLOR;
    border-radius: 7px;
}}
QLabel {{ color: {TEXT}; background: transparent; }}
QRadioButton {{ color: {MUTED}; font-size: 10px; spacing: 3px; padding: 1px 4px; }}
QRadioButton:checked {{ color: {ACCENT}; }}
QRadioButton::indicator {{
    width: 10px; height: 10px; border-radius: 5px;
    border: 1px solid {DIM}; background: {BG2};
}}
QRadioButton::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}
QPushButton#InjectBtn {{
    background: transparent; color: {ACCENT};
    border: 1px solid {ACCENT}; padding: 2px 7px;
    border-radius: 4px; font-size: 10px; font-weight: 600;
}}
QPushButton#InjectBtn:hover {{ background: {ACCENT}; color: {BG}; }}
QPushButton#InjectBtn:disabled {{ color: {DIM}; border-color: {DIM}; }}
QPushButton#InfoBtn {{
    background: transparent; color: {MUTED};
    border: 1px solid {BORDER}; border-radius: 4px;
    font-size: 9px; padding: 2px 5px;
}}
QPushButton#InfoBtn:checked {{ color: {ACCENT}; border-color: {ACCENT}; }}
"""

INFO_SS = f"""
QFrame#InfoPanel {{
    background: {BG2}; border-radius: 5px; border: 1px solid {BORDER};
}}
"""

COPY_SS = f"""
QPushButton {{
    background: transparent; color: {DIM};
    border: none; font-size: 9px; padding: 0; margin: 0;
}}
QPushButton:hover {{ color: {ACCENT}; }}
"""

FIELD_SS = f"""
QLineEdit {{
    background: transparent; color: {TEXT2};
    border: none; border-bottom: 1px solid {BORDER};
    border-radius: 0; padding: 1px 2px;
    font-size: 9px; font-family: 'Courier New';
    selection-background-color: {ACCENT}; selection-color: {BG};
}}
QLineEdit:focus {{ border-bottom-color: {ACCENT}; }}
"""


# ─── WORKER ──────────────────────────────────────────────────────────────────
class InyectorWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            res = subprocess.check_output(
                [PATH_INJECT_SH, self.url], stderr=subprocess.STDOUT
            )
            self.finished.emit(res.decode("utf-8").strip())
        except Exception as e:
            self.finished.emit(f"ERROR: {e}")


# ─── CANAL CARD ───────────────────────────────────────────────────────────────
class CanalCard(QFrame):
    def __init__(self, win):
        super().__init__()
        self.data = {}
        self.win = win
        self._build()

    def _build(self):
        self.setObjectName("CanalCard")
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 5, 8, 5)
        root.setSpacing(3)

        # Fila 1: dot · nombre · badge · score
        h1 = QHBoxLayout()
        h1.setSpacing(5)
        self.dot = QLabel("▋")
        self.dot.setFixedWidth(8)
        self.dot.setStyleSheet(f"font-size: 11px; color: {ACCENT};")
        self.lbl_name = QLabel()
        self.lbl_name.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {STAR};"
        )
        self.lbl_badge = QLabel()
        self.lbl_badge.setStyleSheet(
            f"font-size: 8px; font-weight: 700; color: {BG};"
            f"background: {ACCENT}; border-radius: 2px; padding: 1px 4px;"
        )
        self.lbl_score = QLabel()
        self.lbl_score.setStyleSheet(
            f"font-size: 9px; color: {DIM}; font-family: 'Courier New';"
        )
        h1.addWidget(self.dot)
        h1.addWidget(self.lbl_name, 1)
        h1.addWidget(self.lbl_badge)
        h1.addWidget(self.lbl_score)
        root.addLayout(h1)

        # Fila 2: radios + botones
        h2 = QHBoxLayout()
        h2.setSpacing(3)
        self.grp = QButtonGroup(self)
        for i, t in enumerate(["ARCHIVO", "AUTO", "OBTENER"]):
            rb = QRadioButton(t)
            if i == 0:
                rb.setChecked(True)
            self.grp.addButton(rb, i)
            h2.addWidget(rb)
        h2.addStretch()

        self.btn_send = QPushButton("⚡")
        self.btn_send.setObjectName("InjectBtn")
        self.btn_send.setFixedSize(28, 22)
        self.btn_send.setToolTip("Inyectar")
        self.btn_send.clicked.connect(self._despachar)

        self.btn_info = QPushButton("▾")
        self.btn_info.setObjectName("InfoBtn")
        self.btn_info.setCheckable(True)
        self.btn_info.setFixedSize(22, 22)
        self.btn_info.clicked.connect(self._toggle_info)

        h2.addWidget(self.btn_send)
        h2.addWidget(self.btn_info)
        root.addLayout(h2)

        # Panel info
        self.info_panel = QFrame()
        self.info_panel.setObjectName("InfoPanel")
        self.info_panel.setStyleSheet(INFO_SS)
        self.info_panel.setVisible(False)
        ig = QVBoxLayout(self.info_panel)
        ig.setContentsMargins(6, 4, 6, 4)
        ig.setSpacing(2)

        fields_cfg = [
            ("ESTADO", None), ("DESC", "descripcion"), ("XDATA", "xdata"),
            ("ORIGEN", "url_archivo"), ("URL", "url"), ("HIST", None),
        ]
        self._fields = []
        for key, _ in fields_cfg:
            rw = QWidget()
            rw.setStyleSheet("background: transparent;")
            rh = QHBoxLayout(rw)
            rh.setContentsMargins(0, 0, 0, 0)
            rh.setSpacing(4)
            kl = QLabel(key)
            kl.setFixedWidth(44)
            kl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            kl.setStyleSheet(
                f"color: {DIM}; font-size: 8px; font-weight: 700;"
                f"letter-spacing: 1px; font-family: 'Courier New';"
            )
            ve = QLineEdit()
            ve.setReadOnly(True)
            ve.setStyleSheet(FIELD_SS)
            bc = QPushButton("⎘")
            bc.setFixedSize(15, 15)
            bc.setStyleSheet(COPY_SS)
            bc.setToolTip("Copiar")
            bc.clicked.connect(lambda _, e=ve: self._copy(e))
            rh.addWidget(kl)
            rh.addWidget(ve, 1)
            rh.addWidget(bc)
            ig.addWidget(rw)
            self._fields.append((rw, ve))
        root.addWidget(self.info_panel)

    def rebind(self, data: dict):
        self.data = data
        active = data.get("active", 0) == 1
        score = int(float(data.get("score", 0)) * 100)
        col = ACCENT if active else DANGER

        self.setStyleSheet(CARD_BASE.replace("LEFTCOLOR", col))
        self.dot.setStyleSheet(f"font-size: 11px; color: {col};")
        self.lbl_name.setText(str(data.get("canal", "?")))
        self.lbl_badge.setText("ON" if active else "OFF")
        self.lbl_badge.setStyleSheet(
            f"font-size: 8px; font-weight: 700; color: {BG};"
            f"background: {col}; border-radius: 2px; padding: 1px 4px;"
        )
        self.lbl_score.setText(f"{score:3d}%")

        vals = [
            "ACTIVO" if active else "INACTIVO",
            data.get("descripcion"), data.get("xdata"),
            data.get("url_archivo"), data.get("url"),
            f"OK:{data.get('accesible',0)} FAIL:{data.get('inaccesible',0)}"
        ]
        for i, (rw, ve) in enumerate(self._fields):
            v = vals[i]
            ok = v and str(v).strip() and str(v).lower() != "none"
            rw.setVisible(bool(ok))
            ve.setText(str(v) if ok else "")

        self.btn_info.setChecked(False)
        self.btn_info.setText("▾")
        self.info_panel.setVisible(False)
        self.grp.button(0).setChecked(True)
        self.btn_send.setEnabled(True)

    def _toggle_info(self):
        v = self.btn_info.isChecked()
        self.info_panel.setVisible(v)
        self.btn_info.setText("▴" if v else "▾")

    def _copy(self, edit):
        t = edit.text()
        if t:
            QApplication.clipboard().setText(t)
            self.win.statusBar().showMessage(f"⎘ {t[:70]}", 1500)

    def _despachar(self):
        m = self.grp.checkedId()
        if m == 2:
            if self.win.lock_obtain:
                QMessageBox.warning(self, "Bloqueado",
                    "OBTENER está bloqueado. Desbloquéalo con el candado en el Inyector Global.")
                return
            self.btn_send.setEnabled(False)
            self._worker = InyectorWorker(self.data.get("url_archivo"))
            self._worker.finished.connect(
                lambda r: [self.btn_send.setEnabled(True), self._inyectar(r)]
            )
            self._worker.start()
        else:
            url = self.data.get("url_archivo") if m == 0 else self.data.get("url")
            self._inyectar(url)

    def _inyectar(self, url):
        if "ERROR" in str(url):
            QMessageBox.warning(self, "Error", url)
            return
        try:
            with open(PATH_MONITOR, "w") as f:
                f.write(str(url))
            self.win.statusBar().showMessage(f"▶ {str(url)[:70]}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ─── PANEL FAVORITOS ──────────────────────────────────────────────────────────
class FavoritesPanel(QWidget):
    path_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.favs: list[str] = []
        self._build()
        self._load()

    def _build(self):
        self.setStyleSheet(
            f"QWidget {{ background: {BG2}; border-radius: 6px; }}"
        )
        v = QVBoxLayout(self)
        v.setContentsMargins(6, 5, 6, 5)
        v.setSpacing(4)

        # Header
        h = QHBoxLayout()
        h.setSpacing(4)
        lbl = QLabel("★ FAVORITOS")
        lbl.setStyleSheet(
            f"color: {GOLD}; font-size: 9px; font-weight: 700;"
            f"letter-spacing: 2px; font-family: 'Courier New';"
        )
        btn_add = QPushButton("+")
        btn_add.setFixedSize(20, 20)
        btn_add.setToolTip("Añadir directorio")
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {GOLD};
                border: 1px solid {GOLD}; border-radius: 3px; font-size: 12px;
                padding: 0;
            }}
            QPushButton:hover {{ background: {GOLD}; color: {BG}; }}
        """)
        btn_add.clicked.connect(self._add)
        h.addWidget(lbl, 1)
        h.addWidget(btn_add)
        v.addLayout(h)

        self.lst = QListWidget()
        self.lst.setMaximumHeight(110)
        self.lst.itemDoubleClicked.connect(lambda _: self._open())
        v.addWidget(self.lst)

        br = QHBoxLayout()
        br.setSpacing(3)
        b_open = QPushButton("Abrir")
        b_open.setFixedHeight(21)
        b_open.setStyleSheet(
            f"background: {SURF}; color: {ACCENT}; border: 1px solid {ACCENT};"
            f"border-radius: 4px; font-size: 9px;"
        )
        b_open.clicked.connect(self._open)
        b_del = QPushButton("Quitar")
        b_del.setFixedHeight(21)
        b_del.setStyleSheet(
            f"background: {SURF}; color: {MUTED}; border: 1px solid {BORDER};"
            f"border-radius: 4px; font-size: 9px;"
        )
        b_del.clicked.connect(self._del)
        br.addWidget(b_open)
        br.addWidget(b_del)
        v.addLayout(br)

    def _load(self):
        if os.path.exists(PATH_FAVORITES):
            try:
                with open(PATH_FAVORITES) as f:
                    self.favs = json.load(f)
            except:
                self.favs = []
        self._refresh()

    def _save(self):
        try:
            with open(PATH_FAVORITES, "w") as f:
                json.dump(self.favs, f)
        except:
            pass

    def _refresh(self):
        self.lst.clear()
        for p in self.favs:
            name = os.path.basename(p) or p
            it = QListWidgetItem(f"📁  {name}")
            it.setData(Qt.ItemDataRole.UserRole, p)
            it.setToolTip(p)
            self.lst.addItem(it)

    def _add(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar directorio favorito")
        if path and path not in self.favs:
            self.favs.append(path)
            self._save()
            self._refresh()

    def _del(self):
        row = self.lst.currentRow()
        if 0 <= row < len(self.favs):
            self.favs.pop(row)
            self._save()
            self._refresh()

    def _open(self):
        it = self.lst.currentItem()
        if not it:
            return
        path = it.data(Qt.ItemDataRole.UserRole)
        if os.path.isfile(path) and path.endswith(".json"):
            self.path_selected.emit(path)
            return
        if os.path.isdir(path):
            jsons = [f for f in os.listdir(path) if f.endswith(".json")]
            if len(jsons) == 1:
                self.path_selected.emit(os.path.join(path, jsons[0]))
            elif len(jsons) > 1:
                dlg = QDialog(self)
                dlg.setWindowTitle("Elegir JSON")
                dlg.setStyleSheet(f"background: {CARD}; color: {TEXT};")
                vl = QVBoxLayout(dlg)
                lb = QListWidget()
                lb.setStyleSheet(f"background: {SURF}; color: {TEXT}; border: 1px solid {BORDER};")
                for j in jsons:
                    lb.addItem(j)
                lb.setCurrentRow(0)
                bb = QDialogButtonBox(
                    QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
                )
                bb.accepted.connect(dlg.accept)
                bb.rejected.connect(dlg.reject)
                vl.addWidget(QLabel("Selecciona el JSON:"))
                vl.addWidget(lb)
                vl.addWidget(bb)
                if dlg.exec() == QDialog.DialogCode.Accepted and lb.currentItem():
                    self.path_selected.emit(os.path.join(path, lb.currentItem().text()))
            else:
                fp, _ = QFileDialog.getOpenFileName(self, "Elegir JSON", path, "JSON (*.json)")
                if fp:
                    self.path_selected.emit(fp)


# ─── VENTANA PRINCIPAL ────────────────────────────────────────────────────────
class OsirisControlCenter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OSIRIS · IPTV CONTROL")
        self.resize(580, 800)
        self.setMinimumSize(420, 480)
        self.current_path = PATH_JSON
        self.all_data: list[dict] = []
        self._pool: list[CanalCard] = []
        self.lock_obtain = True  # OBTENER bloqueado por defecto

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(180)
        self._timer.timeout.connect(self._filtrar)

        self._build_ui()
        self._cargar(self.current_path)

    def _build_ui(self):
        self.setStyleSheet(APP_SS)
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        ml = QVBoxLayout(root)
        ml.setContentsMargins(8, 8, 8, 6)
        ml.setSpacing(5)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = QHBoxLayout()
        hdr.setSpacing(6)
        tc = QVBoxLayout()
        tc.setSpacing(1)
        tc.setContentsMargins(0, 0, 0, 0)
        t1 = QLabel("✦ OSIRIS")
        t1.setStyleSheet(
            f"color: {ACCENT}; font-size: 14px; font-weight: 800;"
            f"letter-spacing: 5px; font-family: 'Courier New';"
        )
        t2 = QLabel("IPTV CONTROL")
        t2.setStyleSheet(
            f"color: {DIM}; font-size: 8px; letter-spacing: 3px; font-family: 'Courier New';"
        )
        tc.addWidget(t1)
        tc.addWidget(t2)

        btn_open = QPushButton("📁 JSON")
        btn_open.setFixedHeight(24)
        btn_open.setToolTip("Cargar JSON")
        btn_open.clicked.connect(self._sel_archivo)

        btn_reload = QPushButton("↻")
        btn_reload.setFixedSize(24, 24)
        btn_reload.setToolTip("Recargar")
        btn_reload.clicked.connect(lambda: self._cargar(self.current_path))

        hdr.addLayout(tc)
        hdr.addStretch()
        hdr.addWidget(btn_open)
        hdr.addWidget(btn_reload)
        ml.addLayout(hdr)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {BORDER}; max-height: 1px;")
        ml.addWidget(sep)

        # ── Favoritos (colapsable) ────────────────────────────────────────
        self.fav_panel = FavoritesPanel()
        self.fav_panel.path_selected.connect(self._cargar)
        self.fav_panel.setVisible(False)

        self.btn_favs = QPushButton("★  Favoritos  ▾")
        self.btn_favs.setCheckable(True)
        self.btn_favs.setFixedHeight(22)
        self.btn_favs.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {GOLD};
                border: 1px solid {BORDER}; border-radius: 4px;
                font-size: 9px; font-weight: 600; text-align: left; padding: 2px 8px;
            }}
            QPushButton:checked {{
                border-color: {GOLD}; background: rgba(240,192,96,0.07);
            }}
            QPushButton:hover {{ border-color: {GOLD}; }}
        """)
        self.btn_favs.clicked.connect(
            lambda c: [
                self.fav_panel.setVisible(c),
                self.btn_favs.setText("★  Favoritos  ▴" if c else "★  Favoritos  ▾")
            ]
        )
        ml.addWidget(self.btn_favs)
        ml.addWidget(self.fav_panel)

        # ── Inyector global ───────────────────────────────────────────────
        gbox = QFrame()
        gbox.setStyleSheet(
            f"QFrame {{ background: {SURF}; border: 1px solid {BORDER}; border-radius: 7px; }}"
        )
        gi = QVBoxLayout(gbox)
        gi.setContentsMargins(8, 6, 8, 6)
        gi.setSpacing(5)

        # Sub-header
        gh = QHBoxLayout()
        gh.setSpacing(4)
        gtl = QLabel("INYECTOR GLOBAL")
        gtl.setStyleSheet(
            f"color: {DIM}; font-size: 8px; font-weight: 700;"
            f"letter-spacing: 2px; font-family: 'Courier New';"
        )
        self.btn_lock = QPushButton("🔒")
        self.btn_lock.setCheckable(True)
        self.btn_lock.setChecked(True)
        self.btn_lock.setFixedSize(22, 22)
        self.btn_lock.setToolTip("Desbloquear OBTENER")
        self.btn_lock.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {BORDER}; border-radius: 4px; font-size: 11px; padding: 0;
            }}
            QPushButton:checked {{ color: {DANGER}; border-color: {DANGER}; }}
            QPushButton:!checked {{ color: {SUCCESS}; border-color: {SUCCESS}; }}
        """)
        self.btn_lock.clicked.connect(self._toggle_lock)
        gh.addWidget(gtl, 1)
        gh.addWidget(self.btn_lock)
        gi.addLayout(gh)

        # Fila URL
        gu = QHBoxLayout()
        gu.setSpacing(4)
        self.g_input = QLineEdit()
        self.g_input.setPlaceholderText("URL directa…")
        self.g_input.setFixedHeight(26)
        self.g_input.returnPressed.connect(self._g_inyectar)

        btn_video = QPushButton("📽")
        btn_video.setFixedSize(26, 26)
        btn_video.setToolTip("Seleccionar archivo de video")
        btn_video.setStyleSheet(f"""
            QPushButton {{
                background: {SURF}; color: {ACCENT2};
                border: 1px solid {ACCENT2}; border-radius: 5px; font-size: 13px; padding: 0;
            }}
            QPushButton:hover {{ background: {ACCENT2}; color: {BG}; }}
        """)
        btn_video.clicked.connect(self._sel_video)

        self.btn_obtener = QPushButton("OBTENER")
        self.btn_obtener.setFixedHeight(26)
        self.btn_obtener.setEnabled(False)
        self.btn_obtener.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT2}; color: {BG};
                border: none; border-radius: 4px; font-size: 9px; font-weight: 700;
                padding: 2px 8px; letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: #c4b5fd; }}
            QPushButton:disabled {{ background: {BORDER}; color: {DIM}; }}
        """)
        self.btn_obtener.clicked.connect(self._g_obtener)

        btn_ginject = QPushButton("⚡ INYECTAR")
        btn_ginject.setFixedHeight(26)
        btn_ginject.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: {BG};
                border: none; border-radius: 4px; font-size: 9px; font-weight: 700;
                padding: 2px 10px; letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: #a5b4fc; }}
        """)
        btn_ginject.clicked.connect(self._g_inyectar)

        gu.addWidget(self.g_input, 1)
        gu.addWidget(btn_video)
        gu.addWidget(self.btn_obtener)
        gu.addWidget(btn_ginject)
        gi.addLayout(gu)
        ml.addWidget(gbox)

        # ── Filtros ───────────────────────────────────────────────────────
        fr = QHBoxLayout()
        fr.setSpacing(4)
        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍  Buscar canal, desc, xdata…")
        self.search.setFixedHeight(26)
        self.search.textChanged.connect(self._timer.start)
        self.search.setClearButtonEnabled(True)

        self.cmb_e = QComboBox()
        self.cmb_e.addItems(["TODOS", "ON", "OFF"])
        self.cmb_e.setFixedHeight(26)
        self.cmb_e.setFixedWidth(70)
        self.cmb_e.currentIndexChanged.connect(self._filtrar)

        self.cmb_o = QComboBox()
        self.cmb_o.addItems(["SCORE", "A-Z"])
        self.cmb_o.setFixedHeight(26)
        self.cmb_o.setFixedWidth(65)
        self.cmb_o.currentIndexChanged.connect(self._filtrar)

        fr.addWidget(self.search, 1)
        fr.addWidget(self.cmb_e)
        fr.addWidget(self.cmb_o)
        ml.addLayout(fr)

        self.lbl_count = QLabel("— canales")
        self.lbl_count.setStyleSheet(
            f"color: {DIM}; font-size: 9px; font-family: 'Courier New';"
        )
        ml.addWidget(self.lbl_count)

        # ── Lista ─────────────────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self._sc = QWidget()
        self._sc.setStyleSheet(f"background: {BG};")
        self._ll = QVBoxLayout(self._sc)
        self._ll.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._ll.setContentsMargins(0, 0, 3, 0)
        self._ll.setSpacing(3)
        self.scroll.setWidget(self._sc)
        ml.addWidget(self.scroll, 1)

        self.statusBar().showMessage("OSIRIS listo", 2000)

    # ─── Lógica ───────────────────────────────────────────────────────────────
    def _toggle_lock(self):
        self.lock_obtain = self.btn_lock.isChecked()
        self.btn_obtener.setEnabled(not self.lock_obtain)
        msg = "🔒 OBTENER bloqueado" if self.lock_obtain else "🔓 OBTENER desbloqueado"
        self.btn_lock.setToolTip(msg)
        self.statusBar().showMessage(msg, 2000)

    def _sel_video(self):
        p, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo de video", "",
            "Video (*.mp4 *.mkv *.avi *.ts *.m3u8 *.mpg *.mpeg *.mov *.flv *.webm);;Todos (*)"
        )
        if p:
            self.g_input.setText(p)
            self.statusBar().showMessage(f"📽 {os.path.basename(p)}", 2000)

    def _sel_archivo(self):
        p, _ = QFileDialog.getOpenFileName(self, "Cargar JSON", "", "JSON (*.json)")
        if p:
            self.current_path = p
            self._cargar(p)

    def _cargar(self, path):
        if not os.path.exists(path):
            self.statusBar().showMessage(f"No encontrado: {path}", 3000)
            return
        try:
            with open(path) as f:
                self.all_data = json.load(f)
            self.current_path = path
            n = len(self.all_data)
            deficit = n - len(self._pool)
            if deficit > 0:
                for _ in range(deficit):
                    c = CanalCard(self)
                    c.setVisible(False)
                    self._ll.addWidget(c)
                    self._pool.append(c)
            self._filtrar()
            self.statusBar().showMessage(
                f"✓ {n} canales · {os.path.basename(path)}", 3000
            )
        except Exception as e:
            QMessageBox.critical(self, "Error JSON", str(e))

    def _filtrar(self):
        txt = self.search.text().lower()
        ie = self.cmb_e.currentIndex()

        if txt:
            words = txt.split()
            data = [
                c for c in self.all_data
                if all(
                    w in str(c.get("canal","")).lower() or
                    w in str(c.get("descripcion","")).lower() or
                    w in str(c.get("xdata","")).lower()
                    for w in words
                )
            ]
        else:
            data = list(self.all_data)

        if ie == 1:
            data = [c for c in data if c.get("active", 0) == 1]
        elif ie == 2:
            data = [c for c in data if c.get("active", 0) != 1]

        if self.cmb_o.currentIndex() == 0:
            data.sort(key=lambda x: x.get("score", 0), reverse=True)
        else:
            data.sort(key=lambda x: str(x.get("canal", "")).lower())

        n = len(data)
        total = len(self.all_data)
        suffix = f" / {total}" if (txt or ie) else ""
        self.lbl_count.setText(f"{n}{suffix} canal{'es' if n != 1 else ''}")

        self._sc.setUpdatesEnabled(False)
        try:
            for i, card in enumerate(self._pool):
                if i < len(data):
                    card.rebind(data[i])
                    card.setVisible(True)
                else:
                    card.setVisible(False)
        finally:
            self._sc.setUpdatesEnabled(True)

    def _g_inyectar(self):
        url = self.g_input.text().strip()
        if not url:
            self.statusBar().showMessage("Introduce una URL o archivo primero.", 2000)
            return
        try:
            with open(PATH_MONITOR, "w") as f:
                f.write(url)
            self.statusBar().showMessage(f"▶ GLOBAL → {url[:70]}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _g_obtener(self):
        url = self.g_input.text().strip()
        if not url:
            self.statusBar().showMessage("Introduce una URL base.", 2000)
            return
        self.btn_obtener.setEnabled(False)
        self.btn_obtener.setText("…")
        self._gworker = InyectorWorker(url)
        self._gworker.finished.connect(self._on_g_done)
        self._gworker.start()

    def _on_g_done(self, result: str):
        self.btn_obtener.setEnabled(not self.lock_obtain)
        self.btn_obtener.setText("OBTENER")
        if "ERROR" in result:
            QMessageBox.warning(self, "Error OBTENER", result)
            return
        try:
            with open(PATH_MONITOR, "w") as f:
                f.write(result)
            self.g_input.setText(result)
            self.statusBar().showMessage(f"▶ OBTENIDO → {result[:70]}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


# ─── ENTRY ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    c = [
        (QPalette.ColorRole.Window,          BG),
        (QPalette.ColorRole.WindowText,      TEXT),
        (QPalette.ColorRole.Base,            SURF),
        (QPalette.ColorRole.AlternateBase,   BG2),
        (QPalette.ColorRole.Text,            TEXT),
        (QPalette.ColorRole.Button,          CARD),
        (QPalette.ColorRole.ButtonText,      TEXT),
        (QPalette.ColorRole.Highlight,       ACCENT),
        (QPalette.ColorRole.HighlightedText, BG),
        (QPalette.ColorRole.ToolTipBase,     SURF),
        (QPalette.ColorRole.ToolTipText,     TEXT),
    ]
    for role, color in c:
        pal.setColor(role, QColor(color))
    app.setPalette(pal)

    w = OsirisControlCenter()
    w.show()
    sys.exit(app.exec())