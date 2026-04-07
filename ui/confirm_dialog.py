"""
SRK Boost - Confirmation Dialog
A reusable dark-themed confirmation dialog shown before any destructive action.
"""

from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class ConfirmDialog(QDialog):
    """
    Dark-themed modal confirmation dialog.

    Usage::

        dlg = ConfirmDialog(
            parent=self,
            title="Apply FPS Boost?",
            description="The following optimizations will be applied to your system:",
            actions=[
                "Set power plan to High Performance",
                "Disable Xbox Game Bar (registry)",
                "Disable SysMain service",
                "Disable DiagTrack service",
                "Adjust visual effects for performance",
                "Clear standby memory",
            ],
            show_restore_note=True,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # user clicked Proceed
            ...
    """

    def __init__(
        self,
        parent=None,
        title: str = "Confirm Action",
        description: str = "Are you sure you want to proceed?",
        actions: Optional[List[str]] = None,
        show_restore_note: bool = True,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(480)
        self.setMaximumWidth(600)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        self._build_ui(title, description, actions or [], show_restore_note)
        self._apply_styles()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(
        self,
        title: str,
        description: str,
        actions: List[str],
        show_restore_note: bool,
    ):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("confirm_header")
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        icon = QLabel("⚠")
        icon.setObjectName("confirm_icon")
        title_lbl = QLabel(title)
        title_lbl.setObjectName("confirm_title")

        header_layout.addWidget(icon)
        header_layout.addSpacing(10)
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        root.addWidget(header)

        # ── Body ──────────────────────────────────────────────────────────────
        body = QFrame()
        body.setObjectName("confirm_body")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 20)
        body_layout.setSpacing(14)

        desc_lbl = QLabel(description)
        desc_lbl.setObjectName("confirm_desc")
        desc_lbl.setWordWrap(True)
        body_layout.addWidget(desc_lbl)

        if actions:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setMaximumHeight(220)

            actions_widget = QWidget()
            actions_layout = QVBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(6)

            for action in actions:
                row = QHBoxLayout()
                row.setSpacing(10)

                check_lbl = QLabel("✓")
                check_lbl.setObjectName("confirm_check")
                check_lbl.setFixedWidth(16)

                action_lbl = QLabel(action)
                action_lbl.setObjectName("confirm_action")
                action_lbl.setWordWrap(True)

                row.addWidget(check_lbl)
                row.addWidget(action_lbl, 1)
                actions_layout.addLayout(row)

            scroll.setWidget(actions_widget)
            body_layout.addWidget(scroll)

        if show_restore_note:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setObjectName("confirm_sep")
            body_layout.addWidget(sep)

            note = QLabel("📌  A restore point will be created before making any changes.")
            note.setObjectName("confirm_note")
            note.setWordWrap(True)
            body_layout.addWidget(note)

        root.addWidget(body)

        # ── Footer buttons ────────────────────────────────────────────────────
        footer = QFrame()
        footer.setObjectName("confirm_footer")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 12, 20, 16)
        footer_layout.setSpacing(10)
        footer_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("confirm_cancel_btn")
        cancel_btn.setMinimumHeight(38)
        cancel_btn.setMinimumWidth(100)
        cancel_btn.clicked.connect(self.reject)

        proceed_btn = QPushButton("Proceed")
        proceed_btn.setObjectName("confirm_proceed_btn")
        proceed_btn.setMinimumHeight(38)
        proceed_btn.setMinimumWidth(120)
        proceed_btn.setDefault(True)
        proceed_btn.clicked.connect(self.accept)

        footer_layout.addWidget(cancel_btn)
        footer_layout.addWidget(proceed_btn)
        root.addWidget(footer)

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0e0e1a;
                border: 1px solid #2a1a4a;
                border-radius: 12px;
            }

            /* Header */
            QFrame#confirm_header {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a0a2e, stop:1 #0e0e1a
                );
                border-bottom: 1px solid #2a1a4a;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
            QLabel#confirm_icon {
                color: #ffaa00;
                font-size: 20px;
            }
            QLabel#confirm_title {
                color: #e0e0ff;
                font-size: 16px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }

            /* Body */
            QFrame#confirm_body {
                background-color: #0e0e1a;
            }
            QLabel#confirm_desc {
                color: #c0c0e0;
                font-size: 13px;
                line-height: 1.5;
            }
            QLabel#confirm_check {
                color: #6c63ff;
                font-size: 14px;
                font-weight: bold;
            }
            QLabel#confirm_action {
                color: #e0e0ff;
                font-size: 13px;
            }
            QFrame#confirm_sep {
                background-color: #2a1a4a;
                max-height: 1px;
            }
            QLabel#confirm_note {
                color: #8888bb;
                font-size: 12px;
                font-style: italic;
            }

            /* Footer */
            QFrame#confirm_footer {
                background-color: #0a0a15;
                border-top: 1px solid #1a1a2e;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }

            /* Cancel button – gray */
            QPushButton#confirm_cancel_btn {
                background-color: #2a2a3a;
                color: #a0a0c0;
                border: 1px solid #3a3a5a;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#confirm_cancel_btn:hover {
                background-color: #3a3a5a;
                color: #e0e0ff;
            }
            QPushButton#confirm_cancel_btn:pressed {
                background-color: #1a1a2a;
            }

            /* Proceed button – accent purple */
            QPushButton#confirm_proceed_btn {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6c63ff, stop:1 #8b5cf6
                );
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                font-size: 13px;
                font-weight: 700;
            }
            QPushButton#confirm_proceed_btn:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7d75ff, stop:1 #9d6fff
                );
            }
            QPushButton#confirm_proceed_btn:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5a52e0, stop:1 #7b4ee0
                );
            }

            /* Scroll area inside body */
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QWidget {
                background-color: transparent;
                color: #e0e0ff;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QScrollBar:vertical {
                background: #12121a;
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #2a2a4a;
                border-radius: 3px;
                min-height: 16px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6c63ff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
