import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
                             QComboBox, QPushButton, QCheckBox, QGraphicsOpacityEffect, 
                             QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QCursor, QIcon, QPainter, QColor

from components.styles import C_BG_MAIN, C_BG_INPUT, C_DANGER, C_SUCCESS, C_TEXT_MUTED, C_BORDER, C_PRIMARY, C_TEXT_MAIN
from components.plugin_system import PluginManager

class PromptItemWidget(QWidget):
    contentChanged = pyqtSignal()

    def __init__(self, parent_item, list_widget, root_getter, read_only=False):
        super().__init__()
        self.parent_item = parent_item
        self.list_widget = list_widget
        self.get_root = root_getter
        self.read_only = read_only
        self.pm = PluginManager()
        
        self.current_plugin = None
        self.current_plugin_widget = None
        
        self.missing_plugin_id = None
        self.missing_data_payload = {}
        
        self.resizing = False
        self.drag_start_y = 0
        self.initial_height = 0

        # --- Main Layout ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ---------------------------------------------------------
        # 1. Header Row
        # ---------------------------------------------------------
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 4, 4, 0)
        header_layout.setSpacing(6)

        # Active Toggle
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
        self.chk_active.toggled.connect(self._on_active_toggled)
        header_layout.addWidget(self.chk_active)

        # Drag Handle
        self.lbl_handle = QLabel("||")
        self.lbl_handle.setFixedWidth(15)
        self.lbl_handle.setStyleSheet(f"color: {C_TEXT_MUTED}; font-weight: bold; font-family: monospace;")
        self.lbl_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        header_layout.addWidget(self.lbl_handle)

        # Plugin Selector
        self.combo_type = QComboBox()
        self.combo_type.setStyleSheet(f"background-color: {C_BG_INPUT}; border: 1px solid {C_BORDER};")
        self._populate_plugins()
        self.combo_type.activated.connect(self._on_user_changed_plugin) 
        header_layout.addWidget(self.combo_type)

        # Label tag
        self.lbl_header_tag = QLabel("") 
        self.lbl_header_tag.setVisible(False)
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
        header_layout.addWidget(self.lbl_header_tag)
        
        header_layout.addStretch()

        # Delete Button
        self.btn_del = QPushButton()
        self.btn_del.setFixedSize(22, 22)
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del.clicked.connect(self.remove_self)
        
        icon = QIcon.fromTheme("edit-delete")
        if not icon.isNull():
            pixmap = icon.pixmap(16, 16)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(C_TEXT_MAIN))
            painter.end()
            self.btn_del.setIcon(QIcon(pixmap))
            self.btn_del.setStyleSheet(f"background: transparent; border: 1px solid {C_DANGER};")
        else:
            self.btn_del.setText("X")
            self.btn_del.setStyleSheet(f"background: transparent; border: 1px solid {C_DANGER}; color: {C_DANGER}; font-weight: bold;")
        
        header_layout.addWidget(self.btn_del)
        self.main_layout.addLayout(header_layout)

        # ---------------------------------------------------------
        # 2. Content Area
        # ---------------------------------------------------------
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        
        self.opacity_effect = QGraphicsOpacityEffect(self.content_area)
        self.opacity_effect.setOpacity(1.0)
        self.content_area.setGraphicsEffect(self.opacity_effect)
        
        self.main_layout.addWidget(self.content_area)

        # ---------------------------------------------------------
        # 3. Resize Handle
        # ---------------------------------------------------------
        self.resize_handle = QFrame()
        self.resize_handle.setFixedHeight(6)
        self.resize_handle.setCursor(Qt.CursorShape.SizeVerCursor)
        self.resize_handle.setStyleSheet(f"""
            QFrame {{ background-color: {C_BG_INPUT}; border-top: 1px solid {C_BORDER}; }}
            QFrame:hover {{ background-color: {C_PRIMARY}; }}
        """)
        self.resize_handle.mousePressEvent = self.resize_mouse_press
        self.resize_handle.mouseMoveEvent = self.resize_mouse_move
        self.resize_handle.mouseReleaseEvent = self.resize_mouse_release
        self.main_layout.addWidget(self.resize_handle)

        if self.read_only:
            self.chk_active.setEnabled(False)
            self.lbl_handle.setVisible(False)
            self.combo_type.setEnabled(False)
            self.combo_type.setStyleSheet(f"color: {C_TEXT_MAIN}; background: transparent; border: none; font-weight: bold;")
            self.btn_del.setVisible(False)
            self.resize_handle.setVisible(False)

        self._load_plugin_by_id(self.pm.get_default_plugin_id())

    def _populate_plugins(self):
        self.combo_type.clear()
        for name, pid in self.pm.get_plugin_names():
            self.combo_type.addItem(name, pid)

    def _on_active_toggled(self, checked):
        if not self.read_only:
            self.opacity_effect.setOpacity(1.0 if checked else 0.5)
            self._emit_change()

    def _on_user_changed_plugin(self):
        if self.read_only: return
        pid = self.combo_type.currentData()
        self._load_plugin_by_id(pid, preserve_state=True)

    # --- NEW FUNCTION REQUIRED FOR INTERACTION ---
    def set_header_tag(self, text):
        if not text:
            self.lbl_header_tag.setVisible(False)
        else:
            self.lbl_header_tag.setText(text)
            self.lbl_header_tag.setVisible(True)

    def _load_plugin_by_id(self, pid, preserve_state=False):
        if not pid: return
        
        transfer_data = {}
        if preserve_state and self.current_plugin and self.current_plugin_widget:
            try: transfer_data = self.current_plugin.get_state(self.current_plugin_widget)
            except: pass

        if self.current_plugin_widget:
            self.content_layout.removeWidget(self.current_plugin_widget)
            self.current_plugin_widget.deleteLater()
            self.current_plugin_widget = None

        self.current_plugin = None
        self.set_header_tag("") # Reset tag
        
        new_plugin = self.pm.get_plugin(pid)

        if not new_plugin:
            self._render_missing_ui(pid)
        else:
            self.missing_plugin_id = None
            self.missing_data_payload = {}
            self.current_plugin = new_plugin
            
            # --- PASS KWARGS HERE ---
            self.current_plugin_widget = self.current_plugin.create_ui(
                self.content_area, 
                self.get_root,
                update_tag=self.set_header_tag
            )
            
            if not self.read_only:
                self.current_plugin.dataChanged.connect(self._emit_change)
            
            self.content_layout.addWidget(self.current_plugin_widget)
            
            if preserve_state and transfer_data:
                try: self.current_plugin.set_state(self.current_plugin_widget, transfer_data)
                except: pass

            if self.read_only:
                self._apply_recursive_readonly(self.current_plugin_widget)

            min_h = self.current_plugin.get_min_height()
            current_h = self.parent_item.sizeHint().height()
            if current_h < min_h:
                self.parent_item.setSizeHint(QSize(self.parent_item.sizeHint().width(), min_h))

        idx = self.combo_type.findData(pid)
        if idx >= 0:
            if self.combo_type.currentIndex() != idx:
                self.combo_type.setCurrentIndex(idx)
        else:
            self.combo_type.addItem(f"? {pid}", pid)
            self.combo_type.setCurrentIndex(self.combo_type.count() - 1)

        self._emit_change()

    def _render_missing_ui(self, pid):
        container = QWidget()
        container.setMinimumHeight(60)
        l = QVBoxLayout(container)
        l.setContentsMargins(10, 10, 10, 10)
        l.setSpacing(2)
        lbl_title = QLabel(f"Unknown Plugin: {pid}")
        lbl_title.setStyleSheet(f"color: {C_DANGER}; font-weight: bold;")
        l.addWidget(lbl_title)
        lbl_desc = QLabel("This block type is not registered. Data is preserved.")
        lbl_desc.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11px;")
        l.addWidget(lbl_desc)
        self.current_plugin_widget = container
        self.content_layout.addWidget(container)
        self.missing_plugin_id = pid
        
    def _apply_recursive_readonly(self, widget):
        for inp in widget.findChildren((QLineEdit, QTextEdit, QPlainTextEdit)):
            inp.setReadOnly(True)
        for w in widget.findChildren((QComboBox, QCheckBox, QAbstractSpinBox)):
            w.setEnabled(False)
        for btn in widget.findChildren(QPushButton):
            btn.setVisible(False)
        for child in widget.findChildren(QWidget):
            child.setAcceptDrops(False)

    def _emit_change(self):
        if not self.read_only:
            self.contentChanged.emit()

    def remove_self(self):
        if self.read_only: return
        self.list_widget.takeItem(self.list_widget.row(self.parent_item))
        self._emit_change()

    def get_state(self):
        if self.current_plugin and self.current_plugin_widget:
            return {
                "plugin_id": self.current_plugin.id,
                "is_active": self.chk_active.isChecked(),
                "height": self.parent_item.sizeHint().height(),
                "data": self.current_plugin.get_state(self.current_plugin_widget)
            }
        elif self.missing_plugin_id:
             return {
                "plugin_id": self.missing_plugin_id,
                "is_active": self.chk_active.isChecked(),
                "height": self.parent_item.sizeHint().height(),
                "data": self.missing_data_payload
            }
        return {}

    def set_state(self, state):
        pid = state.get("plugin_id")
        data_payload = state.get("data")

        if not pid and "type" in state:
            legacy_type = state["type"]
            if legacy_type == "File":
                pid = "core.file"
                data_payload = {
                    "path": state.get("target_path", ""),
                    "mode": state.get("path_mode", "Relative Path"),
                    "text": state.get("text", "")
                }
            elif legacy_type == "Folder Tree":
                pid = "core.tree"
                data_payload = {
                    "path": state.get("target_path", ""),
                    "mode": state.get("path_mode", "Relative Path"),
                    "text": state.get("text", ""),
                    "ignore": state.get("ignore_patterns", ""),
                    "inject": state.get("tree_inject_files", [])
                }
            else: 
                pid = "core.message"
                data_payload = {
                    "text": state.get("text", "")
                }

        if not pid: pid = "core.message"
        if data_payload is None: data_payload = state

        # Load plugin (this creates the UI)
        self._load_plugin_by_id(pid, preserve_state=False)

        # Populate data
        if self.current_plugin and self.current_plugin_widget:
            try:
                self.current_plugin.set_state(self.current_plugin_widget, data_payload)
            except Exception as e:
                print(f"Error setting state for {pid}: {e}")
        else:
            self.missing_plugin_id = pid
            self.missing_data_payload = data_payload

        is_active = state.get("is_active", True)
        self.chk_active.setChecked(is_active)
        
        if not self.read_only:
            self._on_active_toggled(is_active)
        else:
            self.opacity_effect.setOpacity(1.0 if is_active else 0.5)

        h = state.get("height", 0)
        if h > 50:
             self.parent_item.setSizeHint(QSize(self.parent_item.sizeHint().width(), h))

    def get_compiled_output(self, global_ignore=""):
        if not self.chk_active.isChecked(): return ""
        
        if self.current_plugin and self.current_plugin_widget:
            try:
                data = self.current_plugin.get_state(self.current_plugin_widget)
                return self.current_plugin.compile(data, self.get_root(), global_ignore=global_ignore)
            except Exception as e:
                return f"[Error: {str(e)}]\n"
        elif self.missing_plugin_id:
            return f"[MISSING: {self.missing_plugin_id}]\n"
        return ""

    def resize_mouse_press(self, event):
        if self.read_only: return
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing = True
            self.drag_start_y = QCursor.pos().y()
            self.initial_height = self.parent_item.sizeHint().height()
            if self.initial_height <= 0: self.initial_height = self.height()
            event.accept()

    def resize_mouse_move(self, event):
        if self.resizing:
            delta = QCursor.pos().y() - self.drag_start_y
            new_height = self.initial_height + delta
            min_h = self.current_plugin.get_min_height() if self.current_plugin else 80
            if new_height < min_h: new_height = min_h
            self.parent_item.setSizeHint(QSize(self.parent_item.sizeHint().width(), new_height))
            event.accept()

    def resize_mouse_release(self, event):
        self.resizing = False
        event.accept()