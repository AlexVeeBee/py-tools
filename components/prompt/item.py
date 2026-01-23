import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
                             QComboBox, QPushButton, QFileDialog, QPlainTextEdit, 
                             QLineEdit, QCheckBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QCursor, QIcon, QPainter, QColor

from components.styles import C_BG_MAIN, C_DANGER, C_TEXT_MUTED, C_TEXT_MAIN, C_BORDER, C_BG_INPUT, C_PRIMARY, C_SUCCESS

# Import from siblings
from .common import DroppableLineEdit
from .generator import get_formatted_path, compile_prompt_data
from .inject_helper import FileInjectHelper

class PromptItemWidget(QWidget):
    contentChanged = pyqtSignal()

    def __init__(self, parent_item, list_widget, root_getter, read_only=False):
        super().__init__()
        self.parent_item = parent_item
        self.list_widget = list_widget
        self.get_root = root_getter
        self.read_only = read_only
        self.target_path = ""
        
        # Resizing State
        self.resizing = False
        self.drag_start_y = 0
        self.initial_height = 0
        self.drag_min_height = 80 

        # --- Main Layout (Vertical) ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ---------------------------------------------------------
        # 0. Header Row (Toggle + Tag)
        # ---------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 2, 0, 0)
        header_layout.setSpacing(6)

        # A. Custom Active Toggle
        self.chk_active = QCheckBox()
        self.chk_active.setChecked(True)
        self.chk_active.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_active.setToolTip("Enable/Disable this block in generation")
        self.chk_active.setStyleSheet(f"""
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border-radius: 2px;
                background-color: {C_BORDER};
            }}
            QCheckBox::indicator:checked {{
                background-color: {C_SUCCESS}; 
                image: url(none);
            }}
            QCheckBox::indicator:unchecked {{
                background-color: {C_DANGER};
            }}
        """)
        self.chk_active.toggled.connect(self.on_toggle_active)
        self.chk_active.toggled.connect(self._emit)
        header_layout.addWidget(self.chk_active)

        # B. Header Tag
        self.lbl_header_tag = QLabel("</>")
        self.lbl_header_tag.setFixedHeight(20)
        self.lbl_header_tag.setStyleSheet(f"""
            QLabel {{
                background-color: {C_BG_MAIN}; 
                color: {C_PRIMARY}; 
                font-weight: bold; 
                font-size: 11px;
                padding: 2px 6px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
        """)
        self.lbl_header_tag.setVisible(False)
        header_layout.addWidget(self.lbl_header_tag)
        
        header_layout.addStretch()
        self.main_layout.addLayout(header_layout)

        # ---------------------------------------------------------
        # --- Content Container (Horizontal) ---
        # ---------------------------------------------------------
        self.content_widget = QWidget()
        content_layout = QHBoxLayout(self.content_widget)
        content_layout.setContentsMargins(4, 4, 4, 4)
        content_layout.setSpacing(6)
        self.main_layout.addWidget(self.content_widget)

        # 1. Drag Handle
        self.lbl_handle = QLabel("||")
        self.lbl_handle.setFixedWidth(15)
        self.lbl_handle.setStyleSheet(f"color: {C_TEXT_MUTED}; font-weight: bold; font-family: monospace;")
        if not read_only:
            self.lbl_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.lbl_handle.setVisible(False)
        content_layout.addWidget(self.lbl_handle)

        # 2. Config Column
        col_cfg = QVBoxLayout()
        col_cfg.setSpacing(2)
        col_cfg.setContentsMargins(0,0,0,0)
        
        self.combo_type = QComboBox()
        self.combo_type.addItems(["Message", "File", "Folder Tree"])
        self.combo_type.currentTextChanged.connect(self.on_type_changed)
        self.combo_type.currentIndexChanged.connect(self._emit)
        
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Name Only", "Relative Path", "Full Path"])
        self.combo_mode.currentIndexChanged.connect(self.update_display)
        self.combo_mode.currentIndexChanged.connect(self._emit)
        
        col_cfg.addWidget(self.combo_type)
        col_cfg.addWidget(self.combo_mode)
        col_cfg.addStretch()
        
        w_cfg = QWidget()
        w_cfg.setFixedWidth(140)
        w_cfg.setLayout(col_cfg)
        content_layout.addWidget(w_cfg)

        # 3. Text Area
        self.txt_prompt = QPlainTextEdit()
        self.txt_prompt.setAcceptDrops(False)
        self.txt_prompt.textChanged.connect(self._emit)
        content_layout.addWidget(self.txt_prompt, stretch=3)

        # 4. Path Controls
        col_path = QVBoxLayout()
        col_path.setSpacing(4)
        col_path.setContentsMargins(0,0,0,0)
        
        # Row 1: Input + Browse
        row_p = QHBoxLayout()
        self.ln_path = DroppableLineEdit()
        self.ln_path.setReadOnly(True)
        self.ln_path.setPlaceholderText("<Drag file here>")
        self.ln_path.fileDropped.connect(self.handle_drop)
        
        self.btn_br = QPushButton("...")
        self.btn_br.setFixedWidth(30)
        self.btn_br.clicked.connect(self.browse)
        
        row_p.addWidget(self.ln_path)
        row_p.addWidget(self.btn_br)
        
        # Row 2: Ignore (Restored to Body)
        self.ln_ignore = QLineEdit()
        self.ln_ignore.setPlaceholderText("Ignore: .git, node_modules, ...")
        self.ln_ignore.setText(".git, node_modules, __pycache__, .idea, .vscode, dist, build")
        self.ln_ignore.textChanged.connect(self._emit)
        
        col_path.addLayout(row_p)
        col_path.addWidget(self.ln_ignore)
        col_path.addStretch()
        
        self.w_path = QWidget()
        self.w_path.setLayout(col_path)
        content_layout.addWidget(self.w_path, stretch=4)

        # 5. Delete
        self.btn_del = QPushButton()
        self.btn_del.setFixedSize(22, 22)
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del.setStyleSheet(f"background: transparent; border: 1px solid {C_DANGER}; font-weight: bold;")
        
        icon = QIcon.fromTheme("edit-delete")
        if not icon.isNull():
            pixmap = icon.pixmap(16, 16)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(C_TEXT_MAIN))
            painter.end()
            self.btn_del.setIcon(QIcon(pixmap))
            self.btn_del.setText("")
        else:
            self.btn_del.setText("X")
            self.btn_del.setStyleSheet(f"background: transparent; border: 1px solid {C_DANGER}; color: {C_DANGER}; font-weight: bold;")

        self.btn_del.clicked.connect(self.remove_self)
        
        if read_only:
            self.btn_del.setVisible(False)
        else:
            content_layout.addWidget(self.btn_del, alignment=Qt.AlignmentFlag.AlignTop)

        # --- Inject Helper ---
        self.inject_helper = FileInjectHelper(
            parent=self, 
            path_getter=lambda: self.target_path, 
            ignore_getter=lambda: self.ln_ignore.text()
        )
        self.inject_helper.filesChanged.connect(self._emit)
        self.inject_helper.setVisible(False)
        self.main_layout.addWidget(self.inject_helper)

        # --- Resize Handle ---
        if not read_only:
            self.resize_handle = QFrame()
            self.resize_handle.setFixedHeight(6)
            self.resize_handle.setCursor(Qt.CursorShape.SizeVerCursor)
            self.resize_handle.setStyleSheet(f"""
                QFrame {{
                    background-color: {C_BG_INPUT};
                    border-top: 1px solid {C_BORDER};
                }}
                QFrame:hover {{
                    background-color: {C_PRIMARY};
                }}
            """)
            self.resize_handle.mousePressEvent = self.resize_mouse_press
            self.resize_handle.mouseMoveEvent = self.resize_mouse_move
            self.resize_handle.mouseReleaseEvent = self.resize_mouse_release
            self.main_layout.addWidget(self.resize_handle)

        if read_only:
            self._apply_read_only_mode()

        self.on_type_changed("Message")
        self.setMinimumHeight(60)

    # --- Resize Logic ---
    def get_ui_min_height(self):
        base = 25 
        mode = self.combo_type.currentText()
        if mode == "Message":
            return base + 60 
        elif mode == "File":
            return base + 20 + 40 + 30 
        elif mode == "Folder Tree":
            return base + 20 + 40 + 30 + 35 
        return 80

    def resize_mouse_press(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = True
            self.drag_start_y = QCursor.pos().y()
            self.initial_height = self.parent_item.sizeHint().height()
            if self.initial_height <= 0: self.initial_height = self.height()
            self.drag_min_height = self.get_ui_min_height()
            event.accept()

    def resize_mouse_move(self, event):
        if self.resizing:
            delta = QCursor.pos().y() - self.drag_start_y
            new_height = self.initial_height + delta
            if new_height < self.drag_min_height: new_height = self.drag_min_height
            self.parent_item.setSizeHint(QSize(self.parent_item.sizeHint().width(), new_height))
            event.accept()

    def resize_mouse_release(self, event):
        self.resizing = False
        event.accept()

    def enforce_min_height(self):
        min_req = self.get_ui_min_height()
        current_h = self.parent_item.sizeHint().height()
        if current_h < min_req:
             self.parent_item.setSizeHint(QSize(self.parent_item.sizeHint().width(), min_req))

    # --- Standard Widget Logic ---
    def _apply_read_only_mode(self):
        self.combo_type.setEnabled(False)
        self.combo_mode.setEnabled(False)
        self.chk_active.setEnabled(False)
        self.txt_prompt.setReadOnly(True)
        self.ln_ignore.setReadOnly(True)
        self.ln_path.setAcceptDrops(False)
        self.btn_br.setVisible(False)
        self.inject_helper.set_read_only(True)
        
        style_disabled = f"color: {C_TEXT_MAIN}; background: {C_BG_INPUT}; border: none;"
        self.combo_type.setStyleSheet(style_disabled)
        self.combo_mode.setStyleSheet(style_disabled)

    def _emit(self): 
        if not self.read_only:
            self.contentChanged.emit()

    def on_toggle_active(self, checked):
        # Visual feedback: Reduce opacity/color when disabled
        opacity = 1.0 if checked else 0.4
        self.content_widget.setStyleSheet(f"QWidget {{ opacity: {opacity}; }}")
        
        # Also gray out the text area specifically so it looks disabled
        color = C_TEXT_MAIN if checked else C_TEXT_MUTED
        self.txt_prompt.setStyleSheet(f"color: {color};")

    def on_type_changed(self, text):
        is_msg = text == "Message"
        is_tree = text == "Folder Tree"
        
        self.w_path.setVisible(not is_msg)
        self.combo_mode.setVisible(not is_msg)
        self.ln_ignore.setVisible(is_tree)
        self.lbl_header_tag.setVisible(not is_msg) 
        self.inject_helper.setVisible(is_tree)
        
        if not self.read_only:
            self.txt_prompt.setPlaceholderText("// Enter instructions..." if is_msg else "// Context note...")
        
        if is_msg: 
            self.ln_path.clear() 
            self.target_path = ""
            self.lbl_header_tag.setText("</>")
        
        self.enforce_min_height()

    def handle_drop(self, path):
        if self.read_only: return
        self.target_path = path
        self.combo_type.setCurrentText("Folder Tree" if os.path.isdir(path) else "File")
        self.update_display()
        self._emit()

    def browse(self):
        if self.read_only: return
        mode = self.combo_type.currentText()
        if mode == "File":
            f, _ = QFileDialog.getOpenFileName(self, "Select")
            if f: self.handle_drop(f)
        elif mode == "Folder Tree":
            d = QFileDialog.getExistingDirectory(self, "Select")
            if d: self.handle_drop(d)

    def update_display(self):
        txt = get_formatted_path(self.target_path, self.combo_mode.currentText(), self.get_root())
        self.ln_path.setText(txt)
        
        if self.target_path:
            name = os.path.basename(self.target_path)
            self.lbl_header_tag.setText(f"{name}")
        else:
            self.lbl_header_tag.setText("")
        
        if not self.read_only and self.target_path and not os.path.exists(self.target_path):
            self.ln_path.setStyleSheet(f"border: 1px solid {C_DANGER}; color: {C_DANGER};")
        else:
            self.ln_path.setStyleSheet("")

    def remove_self(self):
        if self.read_only: return
        self.list_widget.takeItem(self.list_widget.row(self.parent_item))
        self._emit()

    def get_state(self):
        current_h = self.parent_item.sizeHint().height()
        return {
            "type": self.combo_type.currentText(),
            "path_mode": self.combo_mode.currentText(),
            "text": self.txt_prompt.toPlainText(),
            "target_path": self.target_path,
            "ignore_patterns": self.ln_ignore.text(),
            "tree_inject_files": self.inject_helper.get_files(),
            "is_active": self.chk_active.isChecked(),
            "height": current_h if current_h > 0 else 80
        }

    def set_state(self, d):
        self.blockSignals(True)
        self.combo_type.setCurrentText(d.get("type", "Message"))
        self.combo_mode.setCurrentText(d.get("path_mode", "Relative Path"))
        self.txt_prompt.setPlainText(d.get("text", ""))
        self.ln_ignore.setText(d.get("ignore_patterns", ".git, node_modules, __pycache__, .idea, .vscode, dist, build"))
        self.target_path = d.get("target_path", "")
        self.inject_helper.set_files(d.get("tree_inject_files", []))
        
        # Restore active state
        self.chk_active.setChecked(d.get("is_active", True))
        self.on_toggle_active(self.chk_active.isChecked())
        
        h = d.get("height", 0)
        if h > 50:
             self.parent_item.setSizeHint(QSize(self.parent_item.sizeHint().width(), h))
        
        self.update_display()
        self.blockSignals(False)
        self.enforce_min_height() 

    def get_compiled_output(self):
        return compile_prompt_data(self.get_state(), self.get_root())