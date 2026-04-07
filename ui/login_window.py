"""
SRK Boost - Login / Register Window  v2.0
Premium dark glassmorphism design.
"""

import os
import sys
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QApplication, QGraphicsDropShadowEffect,
    QCheckBox
)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QPixmap, QRadialGradient, QBrush, QPen
)

logger = logging.getLogger(__name__)


# ── Worker (runs in thread, no blocking UI) ───────────────────────────────────

class AuthWorker(QObject):
    finished = pyqtSignal(bool, str, dict)

    def __init__(self, mode: str, email: str, password: str):
        super().__init__()
        self.mode     = mode
        self.email    = email
        self.password = password

    def run(self):
        try:
            from core.auth import sign_in, sign_up
            if self.mode == "login":
                ok, msg, data = sign_in(self.email, self.password)
            else:
                ok, msg, data = sign_up(self.email, self.password)
            self.finished.emit(ok, msg, data if data else {})
        except Exception as e:
            self.finished.emit(False, f"Bağlantı hatası: {e}", {})


# ── Fancy input ───────────────────────────────────────────────────────────────

class FancyInput(QFrame):
    def __init__(self, placeholder: str, icon: str = "", password: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(52)
        self.setObjectName("fancy_input")
        self._focused = False
        self._error   = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 14, 0)
        layout.setSpacing(8)

        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size:15px;background:transparent;color:#3a3560;")
            icon_lbl.setFixedWidth(20)
            layout.addWidget(icon_lbl)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        if password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setStyleSheet(
            "QLineEdit{background:transparent;border:none;color:#e0dcff;"
            "font-size:13px;font-family:'Segoe UI';}"
            "QLineEdit::placeholder{color:#3a3560;}"
        )
        # safe focus overrides
        orig_in  = self.input.focusInEvent
        orig_out = self.input.focusOutEvent
        def _fi(e): self._set_focus(True);  orig_in(e)
        def _fo(e): self._set_focus(False); orig_out(e)
        self.input.focusInEvent  = _fi
        self.input.focusOutEvent = _fo
        layout.addWidget(self.input, 1)

        if password:
            self._eye = QPushButton("👁")
            self._eye.setFixedSize(26, 26)
            self._eye.setStyleSheet(
                "background:transparent;border:none;font-size:13px;color:#3a3560;"
            )
            self._eye.clicked.connect(self._toggle_vis)
            layout.addWidget(self._eye)
            self._vis = False

        self._update_style()

    def _set_focus(self, v):
        self._focused = v
        self._update_style()

    def set_error(self, v):
        self._error = v
        self._update_style()

    def _update_style(self):
        if self._error:
            b, bg = "rgba(239,68,68,0.7)", "rgba(239,68,68,0.06)"
        elif self._focused:
            b, bg = "rgba(108,99,255,0.8)", "rgba(108,99,255,0.08)"
        else:
            b, bg = "rgba(108,99,255,0.2)", "rgba(10,8,22,0.6)"
        self.setStyleSheet(
            f"QFrame#fancy_input{{background:{bg};"
            f"border:1.5px solid {b};border-radius:13px;}}"
        )

    def _toggle_vis(self):
        self._vis = not self._vis
        self.input.setEchoMode(
            QLineEdit.EchoMode.Normal if self._vis else QLineEdit.EchoMode.Password
        )
        self._eye.setText("🙈" if self._vis else "👁")

    def text(self):  return self.input.text()
    def clear(self): self.input.clear()


# ── Login Window ──────────────────────────────────────────────────────────────

class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRK Boost")
        self.setFixedSize(440, 600)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._drag_pos  = None
        self._thread    = None
        self._worker    = None
        self._build_ui()
        self._center()

    def _center(self):
        sg = QApplication.primaryScreen().geometry()
        self.move((sg.width()-self.width())//2, (sg.height()-self.height())//2)

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        card = QFrame()
        card.setObjectName("login_card")
        card.setStyleSheet("""
            QFrame#login_card {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 rgba(14,12,30,0.97), stop:1 rgba(8,7,18,0.99));
                border: 1px solid rgba(108,99,255,0.25);
                border-radius: 26px;
            }
        """)
        sh = QGraphicsDropShadowEffect()
        sh.setBlurRadius(55); sh.setOffset(0,18); sh.setColor(QColor(0,0,0,170))
        card.setGraphicsEffect(sh)
        root.addWidget(card)

        vl = QVBoxLayout(card)
        vl.setContentsMargins(44, 36, 44, 36)
        vl.setSpacing(0)

        # Logo row
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_row.setSpacing(12)
        logo_lbl = QLabel()
        logo_lbl.setFixedSize(48, 48)
        lp = self._find_logo()
        if lp:
            px = QPixmap(lp).scaled(48,48,Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                     Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(px)
            logo_lbl.setStyleSheet("border-radius:12px;border:2px solid rgba(108,99,255,0.4);background:#0a0914;")
        else:
            logo_lbl.setText("⚡"); logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_lbl.setStyleSheet("background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #6c63ff,stop:1 #00d4ff);border-radius:12px;font-size:22px;")
        tc = QVBoxLayout(); tc.setSpacing(1)
        an = QLabel("SRK Boost"); an.setStyleSheet("color:#c0b8ff;font-size:20px;font-weight:900;background:transparent;")
        as_ = QLabel("PC Performance Suite"); as_.setStyleSheet("color:#2a2850;font-size:9px;letter-spacing:1px;background:transparent;")
        tc.addWidget(an); tc.addWidget(as_)
        logo_row.addWidget(logo_lbl); logo_row.addLayout(tc)
        vl.addLayout(logo_row)
        vl.addSpacing(28)

        # Tab switcher
        tab_f = QFrame()
        tab_f.setStyleSheet("background:rgba(108,99,255,0.06);border-radius:12px;border:1px solid rgba(108,99,255,0.1);")
        tab_r = QHBoxLayout(tab_f); tab_r.setContentsMargins(4,4,4,4); tab_r.setSpacing(4)
        self._login_tab = QPushButton("Giriş Yap")
        self._reg_tab   = QPushButton("Kayıt Ol")
        for b in [self._login_tab, self._reg_tab]:
            b.setFixedHeight(36)
            b.setStyleSheet("border-radius:9px;font-size:12px;font-weight:700;background:transparent;color:#3a3570;border:none;")
        self._login_tab.clicked.connect(lambda: self._switch("login"))
        self._reg_tab.clicked.connect(lambda: self._switch("register"))
        tab_r.addWidget(self._login_tab); tab_r.addWidget(self._reg_tab)
        vl.addWidget(tab_f)
        vl.addSpacing(22)

        # Inputs
        self._email  = FancyInput("Email adresi", "✉", parent=self)
        self._pass1  = FancyInput("Şifre", "🔒", password=True, parent=self)
        self._pass2  = FancyInput("Şifreyi tekrarla", "🔒", password=True, parent=self)
        self._pass2.setVisible(False)
        vl.addWidget(self._email); vl.addSpacing(10)
        vl.addWidget(self._pass1); vl.addSpacing(10)
        vl.addWidget(self._pass2); vl.addSpacing(6)

        # Remember me
        self._remember = QCheckBox("Beni hatırla")
        self._remember.setChecked(True)
        self._remember.setStyleSheet("""
            QCheckBox{color:#3a3570;font-size:11px;background:transparent;}
            QCheckBox::indicator{width:15px;height:15px;border-radius:4px;
                border:1.5px solid rgba(108,99,255,0.3);background:rgba(10,8,22,0.6);}
            QCheckBox::indicator:checked{background:rgba(108,99,255,0.7);border:1.5px solid #6c63ff;}
        """)
        vl.addWidget(self._remember)
        vl.addSpacing(18)

        # Status
        self._status = QLabel("")
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setWordWrap(True)
        self._status.setStyleSheet("color:#ff6060;font-size:11px;background:transparent;min-height:16px;")
        vl.addWidget(self._status)
        vl.addSpacing(10)

        # Submit
        self._submit = QPushButton("Giriş Yap")
        self._submit.setFixedHeight(50)
        self._submit.setStyleSheet("""
            QPushButton{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6c63ff,stop:1 #00d4ff);
                color:white;border:none;border-radius:14px;font-size:14px;font-weight:800;}
            QPushButton:hover{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7d75ff,stop:1 #22ddff);}
            QPushButton:disabled{background:rgba(108,99,255,0.25);color:rgba(255,255,255,0.3);}
        """)
        self._submit.clicked.connect(self._do_submit)
        vl.addWidget(self._submit)
        vl.addSpacing(14)

        # Divider
        div = QHBoxLayout(); div.setSpacing(8)
        l1 = QFrame(); l1.setFrameShape(QFrame.Shape.HLine); l1.setStyleSheet("color:rgba(108,99,255,0.15);")
        l2 = QFrame(); l2.setFrameShape(QFrame.Shape.HLine); l2.setStyleSheet("color:rgba(108,99,255,0.15);")
        ol = QLabel("veya"); ol.setStyleSheet("color:#2a2850;font-size:10px;background:transparent;")
        div.addWidget(l1,1); div.addWidget(ol); div.addWidget(l2,1)
        vl.addLayout(div)
        vl.addSpacing(12)

        # Google button — official Google colors
        self._google = QPushButton()
        self._google.setFixedHeight(46)
        self._google.setText("  Google ile oturum aç")
        self._google.setStyleSheet("""
            QPushButton{
                background:#ffffff;
                color:#3c4043;
                border:1.5px solid #dadce0;
                border-radius:4px;
                font-size:14px;
                font-weight:500;
                font-family:'Roboto','Segoe UI',sans-serif;
            }
            QPushButton:hover{background:#f8f9fa;border-color:#c6c9cc;}
            QPushButton:disabled{background:#f1f3f4;color:#aaa;}
        """)
        # Google G logo via SVG-like approach — use unicode G in brand color
        self._google.clicked.connect(self._do_google)
        vl.addWidget(self._google)
        vl.addSpacing(14)

        # Skip
        skip = QPushButton("Şimdilik atla →")
        skip.setStyleSheet("background:transparent;color:#2a2850;border:none;font-size:10px;font-weight:600;")
        skip.clicked.connect(self._skip)
        vl.addWidget(skip, alignment=Qt.AlignmentFlag.AlignCenter)

        # X button
        x_btn = QPushButton("✕", card)
        x_btn.setFixedSize(30, 30)
        x_btn.move(self.width()-76, 14)
        x_btn.setStyleSheet("background:rgba(108,99,255,0.1);color:#4a4870;border-radius:7px;border:none;font-size:12px;")
        x_btn.clicked.connect(self._skip)

        self._switch("login")

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _find_logo(self):
        base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        p = os.path.join(base, "assets", "logo.png")
        return p if os.path.exists(p) else ""

    def _switch(self, mode: str):
        self._mode = mode
        on  = "background:rgba(108,99,255,0.75);color:#fff;border-radius:9px;font-size:12px;font-weight:700;border:none;"
        off = "background:transparent;color:#3a3570;border-radius:9px;font-size:12px;font-weight:700;border:none;"
        self._login_tab.setStyleSheet(on  if mode=="login"    else off)
        self._reg_tab.setStyleSheet(  on  if mode=="register" else off)
        self._submit.setText("Giriş Yap" if mode=="login" else "Kayıt Ol")
        self._pass2.setVisible(mode == "register")
        self._status.setText("")
        self._email.set_error(False); self._pass1.set_error(False)

    def _set_status(self, msg: str, color: str):
        self._status.setStyleSheet(f"color:{color};font-size:11px;background:transparent;min-height:16px;")
        self._status.setText(msg)

    # ── Submit ────────────────────────────────────────────────────────────────
    def _do_submit(self):
        email = self._email.text().strip()
        pw1   = self._pass1.text()
        pw2   = self._pass2.text()

        if not email or "@" not in email:
            self._set_status("❌  Geçerli bir email girin.", "#ff6060")
            self._email.set_error(True); return
        if len(pw1) < 6:
            self._set_status("❌  Şifre en az 6 karakter olmalı.", "#ff6060")
            self._pass1.set_error(True); return
        if self._mode == "register" and pw1 != pw2:
            self._set_status("❌  Şifreler eşleşmiyor.", "#ff6060")
            self._pass2.set_error(True); return

        self._email.set_error(False); self._pass1.set_error(False); self._pass2.set_error(False)
        self._submit.setEnabled(False)
        self._submit.setText("⏳  Bekleniyor...")
        self._set_status("Sunucuya bağlanılıyor...", "#6c63ff")

        self._thread = QThread(self)
        self._worker = AuthWorker(self._mode, email, pw1)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_done)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _on_done(self, ok: bool, msg: str, data: dict):
        self._submit.setEnabled(True)
        self._submit.setText("Giriş Yap" if self._mode == "login" else "Kayıt Ol")
        if ok and data.get("access_token"):
            self._set_status(f"✅  {msg}", "#00e87a")
            QTimer.singleShot(700, lambda: self.login_success.emit(data))
        elif ok:
            self._set_status("📧  Email onayı gerekiyor — emailinizi kontrol edin ya da 'Şimdilik atla'ya basın.", "#f97316")
        else:
            self._set_status(f"❌  {msg}", "#ff6060")

    # ── Google ────────────────────────────────────────────────────────────────
    def _do_google(self):
        self._google.setEnabled(False)
        self._google.setText("⏳  Tarayıcı açılıyor...")
        self._set_status("Google hesabınızla giriş yapın...", "#6c63ff")
        from core.auth import sign_in_google
        sign_in_google(
            on_success=lambda s: QTimer.singleShot(0, lambda: self._google_ok(s)),
            on_error=lambda e:   QTimer.singleShot(0, lambda: self._google_err(e)),
        )

    def _google_ok(self, session: dict):
        self._google.setEnabled(True)
        self._google.setText("  Google ile oturum aç")
        self._set_status("✅  Google girişi başarılı!", "#00e87a")
        QTimer.singleShot(600, lambda: self.login_success.emit(session))

    def _google_err(self, msg: str):
        self._google.setEnabled(True)
        self._google.setText("  Google ile oturum aç")
        self._set_status(f"❌  {msg}", "#ff6060")

    def _skip(self):
        self.login_success.emit({"guest": True})

    # ── Drag ──────────────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        g = QRadialGradient(self.width()/2, self.height()/2, 280)
        g.setColorAt(0, QColor(108,99,255,12)); g.setColorAt(1, QColor(0,0,0,0))
        p.fillRect(self.rect(), QBrush(g))
