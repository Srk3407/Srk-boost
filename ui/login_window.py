"""
SRK Boost - Login / Register Window  v1.0
Premium dark glassmorphism design.
"""

import os
import sys
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QApplication, QGraphicsDropShadowEffect,
    QCheckBox, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, QObject, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtGui import (
    QPainter, QColor, QLinearGradient, QBrush, QPen,
    QFont, QPixmap, QPainterPath, QRadialGradient
)

logger = logging.getLogger(__name__)


# ── Worker ────────────────────────────────────────────────────────────────────

class AuthWorker(QObject):
    finished = pyqtSignal(bool, str, dict)

    def __init__(self, mode: str, email: str, password: str):
        super().__init__()
        self.mode     = mode
        self.email    = email
        self.password = password

    def run(self):
        from core.auth import sign_in, sign_up
        if self.mode == "login":
            ok, msg, data = sign_in(self.email, self.password)
        else:
            ok, msg, data = sign_up(self.email, self.password)
        self.finished.emit(ok, msg, data)


# ── Animated input field ──────────────────────────────────────────────────────

class FancyInput(QFrame):
    def __init__(self, placeholder: str, icon: str = "", password: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setObjectName("fancy_input")
        self._focused = False
        self._error   = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        if icon:
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size:16px; background:transparent; color: #4a4870;")
            icon_lbl.setFixedWidth(22)
            layout.addWidget(icon_lbl)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        if password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #e0dcff;
                font-size: 14px;
                font-family: 'Segoe UI';
            }
            QLineEdit::placeholder { color: #3a3560; }
        """)
        self.input.focusInEvent  = lambda e: (self._set_focus(True),  super(QLineEdit, self.input).focusInEvent(e))
        self.input.focusOutEvent = lambda e: (self._set_focus(False), super(QLineEdit, self.input).focusOutEvent(e))
        layout.addWidget(self.input, 1)

        if password:
            self._toggle = QPushButton("👁")
            self._toggle.setFixedSize(28, 28)
            self._toggle.setStyleSheet(
                "background:transparent;border:none;font-size:14px;color:#3a3560;"
            )
            self._toggle.clicked.connect(self._toggle_visibility)
            layout.addWidget(self._toggle)
            self._visible = False

        self._update_style()

    def _set_focus(self, focused: bool):
        self._focused = focused
        self._update_style()

    def set_error(self, error: bool):
        self._error = error
        self._update_style()

    def _update_style(self):
        if self._error:
            border = "rgba(239,68,68,0.7)"
            bg     = "rgba(239,68,68,0.06)"
        elif self._focused:
            border = "rgba(108,99,255,0.8)"
            bg     = "rgba(108,99,255,0.08)"
        else:
            border = "rgba(108,99,255,0.2)"
            bg     = "rgba(10,8,22,0.6)"
        self.setStyleSheet(f"""
            QFrame#fancy_input {{
                background: {bg};
                border: 1.5px solid {border};
                border-radius: 14px;
            }}
        """)

    def _toggle_visibility(self):
        self._visible = not self._visible
        self.input.setEchoMode(
            QLineEdit.EchoMode.Normal if self._visible else QLineEdit.EchoMode.Password
        )
        self._toggle.setText("🙈" if self._visible else "👁")

    def text(self) -> str:
        return self.input.text()

    def clear(self):
        self.input.clear()


# ── Login Window ──────────────────────────────────────────────────────────────

class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)  # emits session data

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SRK Boost")
        self.setFixedSize(460, 620)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._drag_pos = None
        self._thread = None
        self._worker = None
        self._mode = "login"  # login | register
        self._build_ui()
        self._center()

    def _center(self):
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width()  - self.width())  // 2,
            (screen.height() - self.height()) // 2
        )

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Card
        card = QFrame()
        card.setObjectName("login_card")
        card.setStyleSheet("""
            QFrame#login_card {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(14,12,30,0.97),
                    stop:1 rgba(8,7,18,0.99)
                );
                border: 1px solid rgba(108,99,255,0.25);
                border-radius: 28px;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(60)
        shadow.setOffset(0, 20)
        shadow.setColor(QColor(0, 0, 0, 180))
        card.setGraphicsEffect(shadow)
        root.addWidget(card)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(48, 40, 48, 40)
        layout.setSpacing(0)

        # ── Logo ──────────────────────────────────────────────────────────
        logo_row = QHBoxLayout()
        logo_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_row.setSpacing(14)

        # Logo image or fallback
        logo_lbl = QLabel()
        logo_lbl.setFixedSize(52, 52)
        logo_path = self._find_logo()
        if logo_path:
            pix = QPixmap(logo_path).scaled(52, 52,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setStyleSheet(
                "border-radius:14px;border:2px solid rgba(108,99,255,0.4);"
                "background:#0a0914;"
            )
        else:
            logo_lbl.setText("⚡")
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_lbl.setStyleSheet(
                "background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #6c63ff,stop:1 #00d4ff);"
                "border-radius:14px;font-size:24px;"
            )

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        app_name = QLabel("SRK Boost")
        app_name.setStyleSheet("color:#c0b8ff;font-size:22px;font-weight:900;background:transparent;")
        app_sub  = QLabel("PC Performance Suite")
        app_sub.setStyleSheet("color:#2a2850;font-size:10px;letter-spacing:1px;background:transparent;")
        text_col.addWidget(app_name)
        text_col.addWidget(app_sub)

        logo_row.addWidget(logo_lbl)
        logo_row.addLayout(text_col)
        layout.addLayout(logo_row)
        layout.addSpacing(32)

        # ── Tab switcher ──────────────────────────────────────────────────
        tab_frame = QFrame()
        tab_frame.setStyleSheet(
            "background:rgba(108,99,255,0.06);border-radius:14px;"
            "border:1px solid rgba(108,99,255,0.12);"
        )
        tab_row = QHBoxLayout(tab_frame)
        tab_row.setContentsMargins(4, 4, 4, 4)
        tab_row.setSpacing(4)

        self._login_tab = QPushButton("Giriş Yap")
        self._reg_tab   = QPushButton("Kayıt Ol")
        for btn in [self._login_tab, self._reg_tab]:
            btn.setFixedHeight(38)
            btn.setStyleSheet(
                "border-radius:10px;font-size:13px;font-weight:700;"
                "background:transparent;color:#3a3570;border:none;"
            )
        self._login_tab.clicked.connect(lambda: self._switch_mode("login"))
        self._reg_tab.clicked.connect(lambda: self._switch_mode("register"))
        tab_row.addWidget(self._login_tab)
        tab_row.addWidget(self._reg_tab)
        layout.addWidget(tab_frame)
        layout.addSpacing(28)

        # ── Form ──────────────────────────────────────────────────────────
        self._email_input = FancyInput("Email adresi", "✉", parent=self)
        self._pass_input  = FancyInput("Şifre", "🔒", password=True, parent=self)
        self._pass2_input = FancyInput("Şifreyi tekrarla", "🔒", password=True, parent=self)
        self._pass2_input.setVisible(False)

        layout.addWidget(self._email_input)
        layout.addSpacing(12)
        layout.addWidget(self._pass_input)
        layout.addSpacing(12)
        layout.addWidget(self._pass2_input)
        layout.addSpacing(8)

        # Remember me (login only)
        self._remember = QCheckBox("Beni hatırla")
        self._remember.setChecked(True)
        self._remember.setStyleSheet("""
            QCheckBox { color: #3a3570; font-size: 12px; background: transparent; }
            QCheckBox::indicator { width:16px; height:16px; border-radius:4px;
                border:1.5px solid rgba(108,99,255,0.3); background:rgba(10,8,22,0.6); }
            QCheckBox::indicator:checked {
                background:rgba(108,99,255,0.7); border:1.5px solid #6c63ff; }
        """)
        layout.addWidget(self._remember)
        layout.addSpacing(24)

        # ── Status label ──────────────────────────────────────────────────
        self._status_lbl = QLabel("")
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setStyleSheet(
            "color:#ff6060;font-size:12px;background:transparent;min-height:18px;"
        )
        layout.addWidget(self._status_lbl)
        layout.addSpacing(12)

        # ── Submit button ─────────────────────────────────────────────────
        self._submit_btn = QPushButton("Giriş Yap")
        self._submit_btn.setFixedHeight(52)
        self._submit_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #6c63ff, stop:1 #00d4ff);
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #7d75ff, stop:1 #22ddff); }
            QPushButton:pressed { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 #5a52ee, stop:1 #00b8e0); }
            QPushButton:disabled { background: rgba(108,99,255,0.25); color: rgba(255,255,255,0.4); }
        """)
        self._submit_btn.clicked.connect(self._submit)
        layout.addWidget(self._submit_btn)
        layout.addSpacing(16)

        # ── Google button ─────────────────────────────────────────────────
        or_row = QHBoxLayout()
        or_row.setSpacing(10)
        line1 = QFrame(); line1.setFrameShape(QFrame.Shape.HLine)
        line1.setStyleSheet("color:rgba(108,99,255,0.15);")
        or_lbl = QLabel("veya")
        or_lbl.setStyleSheet("color:#2a2850;font-size:11px;background:transparent;")
        line2 = QFrame(); line2.setFrameShape(QFrame.Shape.HLine)
        line2.setStyleSheet("color:rgba(108,99,255,0.15);")
        or_row.addWidget(line1, 1)
        or_row.addWidget(or_lbl)
        or_row.addWidget(line2, 1)
        layout.addLayout(or_row)
        layout.addSpacing(12)

        self._google_btn = QPushButton("  Google ile Giriş Yap")
        self._google_btn.setFixedHeight(48)
        self._google_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.04);
                color: #c0b8ff;
                border: 1.5px solid rgba(108,99,255,0.25);
                border-radius: 14px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.08);
                border-color: rgba(108,99,255,0.5);
            }
            QPushButton:disabled { color: rgba(255,255,255,0.3); }
        """)
        # Google G icon via unicode
        self._google_btn.setText("🌐  Google ile Giriş Yap")
        self._google_btn.clicked.connect(self._google_login)
        layout.addWidget(self._google_btn)
        layout.addSpacing(16)

        # ── Close button ──────────────────────────────────────────────────
        skip_btn = QPushButton("Şimdilik atla →")
        skip_btn.setStyleSheet(
            "background:transparent;color:#2a2850;border:none;"
            "font-size:11px;font-weight:600;"
        )
        skip_btn.clicked.connect(self._skip)
        layout.addWidget(skip_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Close X
        close_btn = QPushButton("✕")
        close_btn.setParent(card)
        close_btn.setFixedSize(32, 32)
        close_btn.move(self.width() - 86, 16)
        close_btn.setStyleSheet(
            "background:rgba(108,99,255,0.1);color:#4a4870;border-radius:8px;"
            "border:none;font-size:13px;font-weight:700;"
        )
        close_btn.clicked.connect(self._skip)

        self._switch_mode("login")

    def _find_logo(self) -> str:
        if hasattr(sys, '_MEIPASS'):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        p = os.path.join(base, "assets", "logo.png")
        return p if os.path.exists(p) else ""

    def _switch_mode(self, mode: str):
        self._mode = mode
        active_style = (
            "background:rgba(108,99,255,0.7);color:#ffffff;"
            "border-radius:10px;font-size:13px;font-weight:700;border:none;"
        )
        inactive_style = (
            "background:transparent;color:#3a3570;"
            "border-radius:10px;font-size:13px;font-weight:700;border:none;"
        )
        if mode == "login":
            self._login_tab.setStyleSheet(active_style)
            self._reg_tab.setStyleSheet(inactive_style)
            self._submit_btn.setText("Giriş Yap")
            self._pass2_input.setVisible(False)
        else:
            self._reg_tab.setStyleSheet(active_style)
            self._login_tab.setStyleSheet(inactive_style)
            self._submit_btn.setText("Kayıt Ol")
            self._pass2_input.setVisible(True)
        self._status_lbl.setText("")
        self._email_input.set_error(False)
        self._pass_input.set_error(False)

    def _submit(self):
        email    = self._email_input.text().strip()
        password = self._pass_input.text()
        password2= self._pass2_input.text()

        # Validate
        if not email or "@" not in email:
            self._show_error("Geçerli bir email adresi girin.")
            self._email_input.set_error(True)
            return
        if len(password) < 6:
            self._show_error("Şifre en az 6 karakter olmalıdır.")
            self._pass_input.set_error(True)
            return
        if self._mode == "register" and password != password2:
            self._show_error("Şifreler eşleşmiyor.")
            self._pass2_input.set_error(True)
            return

        self._email_input.set_error(False)
        self._pass_input.set_error(False)
        self._pass2_input.set_error(False)
        self._submit_btn.setEnabled(False)
        self._submit_btn.setText("⏳  Lütfen bekleyin...")
        self._status_lbl.setText("")
        self._status_lbl.setStyleSheet("color:#6c63ff;font-size:12px;background:transparent;")
        self._status_lbl.setText("Sunucuya bağlanılıyor...")

        self._thread = QThread()
        self._worker = AuthWorker(self._mode, email, password)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_auth_done)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _on_auth_done(self, ok: bool, msg: str, data: dict):
        self._submit_btn.setEnabled(True)
        self._submit_btn.setText("Giriş Yap" if self._mode == "login" else "Kayıt Ol")

        if ok and data.get("access_token"):
            # Success with session
            self._status_lbl.setStyleSheet("color:#00e87a;font-size:12px;background:transparent;")
            self._status_lbl.setText(f"✅  {msg}")
            QTimer.singleShot(800, lambda: self.login_success.emit(data))
        elif ok:
            # Email confirmation needed
            self._status_lbl.setStyleSheet("color:#f97316;font-size:12px;background:transparent;")
            self._status_lbl.setText(f"📧  {msg}")
        else:
            self._show_error(msg)

    def _show_error(self, msg: str):
        self._status_lbl.setStyleSheet("color:#ff6060;font-size:12px;background:transparent;")
        self._status_lbl.setText(f"❌  {msg}")

    def _google_login(self):
        self._google_btn.setEnabled(False)
        self._google_btn.setText("⏳  Tarayıcı açılıyor...")
        self._status_lbl.setStyleSheet("color:#6c63ff;font-size:12px;background:transparent;")
        self._status_lbl.setText("Google hesabınızla giriş yapın...")
        from core.auth import sign_in_google
        sign_in_google(
            on_success=self._on_google_success,
            on_error=self._on_google_error,
        )

    def _on_google_success(self, session: dict):
        """Called from background thread — use QTimer to switch to main thread."""
        QTimer.singleShot(0, lambda: self._finish_google(session))

    def _finish_google(self, session: dict):
        self._google_btn.setEnabled(True)
        self._google_btn.setText("🌐  Google ile Giriş Yap")
        self._status_lbl.setStyleSheet("color:#00e87a;font-size:12px;background:transparent;")
        self._status_lbl.setText("✅  Google girişi başarılı!")
        QTimer.singleShot(600, lambda: self.login_success.emit(session))

    def _on_google_error(self, msg: str):
        QTimer.singleShot(0, lambda: self._finish_google_err(msg))

    def _finish_google_err(self, msg: str):
        self._google_btn.setEnabled(True)
        self._google_btn.setText("🌐  Google ile Giriş Yap")
        self._show_error(msg)

    def _skip(self):
        """Skip auth — launch app as guest."""
        self.login_success.emit({"guest": True})

    # ── Dragging ──────────────────────────────────────────────────────────────
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag_pos and e.buttons() == Qt.MouseButton.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e):
        self._drag_pos = None

    # ── Background glow ───────────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Outer ambient glow
        glow = QRadialGradient(self.width() / 2, self.height() / 2, 300)
        glow.setColorAt(0, QColor(108, 99, 255, 15))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), QBrush(glow))
