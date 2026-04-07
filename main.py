"""
SRK Boost - Main Entry Point
Professional Windows PC Optimizer
"""

import sys
import os
import logging
from datetime import datetime


def resource_path(relative_path: str) -> str:
    """Get absolute path to resource — works for dev and PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller extracts files to a temp folder (_MEIPASS)
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


# ── Auto dependency installer ───────────────────────────────────────────────────────────────────────────────

REQUIRED_PACKAGES = [
    ("psutil",      "psutil"),
    ("win32api",    "pywin32"),
    ("wmi",         "wmi"),
    ("speedtest",   "speedtest-cli"),
    ("qt_material", "qt-material"),
    ("PIL",         "Pillow"),
]


def _check_importable(name: str) -> bool:
    """Check if a package is importable without actually running its module-level code."""
    import importlib.util
    # speedtest.py calls sys.stdout.fileno() at module level which crashes in PyInstaller
    # Use find_spec instead of import_module to avoid executing the module
    try:
        spec = importlib.util.find_spec(name)
        return spec is not None
    except Exception:
        return False


def _install_missing(splash_update_fn=None):
    """Silently install any missing packages before app starts."""
    import subprocess as _sp
    # Skip dependency check when running as PyInstaller bundle
    # (all deps are already bundled or will fail gracefully at runtime)
    if getattr(sys, 'frozen', False):
        return
    missing = []
    for import_name, pip_name in REQUIRED_PACKAGES:
        if not _check_importable(import_name):
            missing.append((import_name, pip_name))

    if not missing:
        return

    flags = 0
    if sys.platform == "win32":
        flags = _sp.CREATE_NO_WINDOW  # type: ignore[attr-defined]

    for i, (import_name, pip_name) in enumerate(missing):
        if splash_update_fn:
            splash_update_fn(f"Installing {pip_name}... ({i+1}/{len(missing)})")
        try:
            _sp.run(
                [sys.executable, "-m", "pip", "install", pip_name, "--quiet"],
                check=False,
                creationflags=flags,
                timeout=120,
            )
        except Exception as e:
            print(f"[WARN] Failed to install {pip_name}: {e}")


# ── Logging setup ─────────────────────────────────────────────────────────────

LOG_DIR = os.path.join(os.path.expanduser("~"), ".srk_boost", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"srk_boost_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger("srk_boost")
logger.info("=" * 60)
logger.info("SRK Boost starting up...")

# ── Qt import ─────────────────────────────────────────────────────────────────

try:
    from PyQt6.QtWidgets import QApplication, QSplashScreen, QLabel
    from PyQt6.QtCore import Qt, QTimer
    from PyQt6.QtGui import QColor, QFont, QPixmap, QPainter, QPen, QBrush
except ImportError as e:
    logger.critical(f"PyQt6 not installed: {e}")
    print("ERROR: PyQt6 is required. Install with: pip install PyQt6 PyQt6-Charts")
    sys.exit(1)

# High-DPI support
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)


def load_stylesheet(app: QApplication):
    """Load the global QSS stylesheet."""
    qss_path = resource_path(os.path.join("assets", "styles.qss"))
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
        logger.info(f"Loaded stylesheet: {qss_path}")
    else:
        logger.warning(f"Stylesheet not found at {qss_path}")


def create_splash(app: QApplication) -> QSplashScreen:
    """Create a branded splash screen."""
    pixmap = QPixmap(480, 280)
    pixmap.fill(QColor("#0a0a0f"))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Glow circle
    glow = QColor("#6c63ff")
    glow.setAlpha(30)
    painter.setBrush(QBrush(glow))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(160, 40, 160, 160)

    # Border
    painter.setPen(QPen(QColor("#1e1e2e"), 2))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(1, 1, 478, 278, 12, 12)

    # Logo text
    painter.setPen(QPen(QColor("#6c63ff")))
    font = QFont("Segoe UI", 42, QFont.Weight.Bold)
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
    painter.setFont(font)
    painter.drawText(0, 60, 480, 120, Qt.AlignmentFlag.AlignCenter, "SRK BOOST")

    # Subtitle
    painter.setPen(QPen(QColor("#00d4ff")))
    font2 = QFont("Segoe UI", 12)
    font2.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 4)
    painter.setFont(font2)
    painter.drawText(0, 150, 480, 40, Qt.AlignmentFlag.AlignCenter, "PC PERFORMANCE OPTIMIZER")

    # Version
    painter.setPen(QPen(QColor("#3a3a6a")))
    font3 = QFont("Segoe UI", 10)
    painter.setFont(font3)
    painter.drawText(0, 230, 480, 30, Qt.AlignmentFlag.AlignCenter, "Loading...")

    painter.end()

    splash = QSplashScreen(pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.setWindowFlag(Qt.WindowType.FramelessWindowHint)
    return splash


def main():
    import platform
    if platform.system() == 'Windows':
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            from PyQt6.QtWidgets import QMessageBox
            _app = QApplication.instance() or QApplication(sys.argv)
            msg = QMessageBox()
            msg.setWindowTitle("Administrator Required")
            msg.setText(
                "SRK Boost works best with administrator privileges.\n\n"
                "Some features (service management, registry edits) may not work "
                "without admin rights.\n\nRun as Administrator for full functionality."
            )
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setStandardButtons(
                QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
            )
            if msg.exec() == QMessageBox.StandardButton.Cancel:
                sys.exit(0)

    app = QApplication(sys.argv)
    app.setApplicationName("SRK Boost")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SRK Boost")

    # Apply qt-material base theme (dark purple - matches our #6c63ff accent)
    try:
        from qt_material import apply_stylesheet
        apply_stylesheet(app, theme='dark_purple.xml', extra={
            'density_scale': '-1',
            'font_family': 'Segoe UI',
        })
        logger.info("qt-material theme applied: dark_purple.xml")
    except ImportError:
        logger.warning("qt-material not installed, falling back to custom QSS only")

    # Load stylesheet (overrides/extends qt-material)
    load_stylesheet(app)

    # Splash screen
    splash = create_splash(app)
    splash.show()
    app.processEvents()

    # Auto-install missing dependencies (shows status on splash)
    def _splash_msg(msg: str):
        splash.showMessage(
            msg,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            QColor("#6c63ff")
        )
        app.processEvents()

    _splash_msg("Checking dependencies...")
    _install_missing(_splash_msg)
    _splash_msg("Loading SRK Boost...")
    app.processEvents()

    # Import heavy modules after splash
    try:
        from ui.main_window import MainWindow
    except ImportError as e:
        logger.critical(f"Failed to import MainWindow: {e}")
        splash.close()
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setWindowTitle("Import Error")
        msg.setText(f"Failed to load SRK Boost:\n\n{e}\n\nMake sure all dependencies are installed.")
        msg.exec()
        sys.exit(1)

    window = MainWindow()

    def _launch(session: dict):
        """Called after login/skip — show main window."""
        try:
            splash.finish(window)
        except Exception:
            pass
        try:
            if session.get("access_token"):
                user_email = session.get("user", {}).get("email", "")
                window.setWindowTitle(f"SRK Boost  —  {user_email}")
            window.show()
            window.raise_()
            window.activateWindow()
        except Exception as e:
            logger.error(f"Launch error: {e}")
        logger.info("Main window shown.")

    def _show_login_or_main():
        try:
            splash.hide()
        except Exception:
            pass
        _launch({"guest": True})

    QTimer.singleShot(1800, _show_login_or_main)

    logger.info("Entering Qt event loop.")
    exit_code = app.exec()
    logger.info(f"SRK Boost exited with code {exit_code}.")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
