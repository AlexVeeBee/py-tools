import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QTextEdit, QLabel, 
                             QFileDialog, QLineEdit, QSplitter, QMessageBox,
                             QAbstractItemView, QApplication, QDialog, QMenu)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent

from components.prompt_item import PromptItemWidget
from components.db_manager import DBManager
from components.prompt_state_dialog import PromptStateDialog
from components.styles import apply_class, C_PRIMARY
from components.mime_parser import DragAndDropParser  # Imported Plugin

# --- CUSTOM WIDGET: List with Absolute Drop Overlay ---
class OverlayFileListWidget(QListWidget):
    filesDropped = pyqtSignal(list) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        self.overlay = QLabel("DROP FILES HERE", self)
        self.overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.overlay.setStyleSheet(f"""
            background-color: rgba(18, 13, 3, 0.9);
            color: {C_PRIMARY}; 
            font-size: 20px; 
            font-family: 'Consolas';
            font-weight: bold;
            border: 2px dashed {C_PRIMARY};
        """)
        self.overlay.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(self.rect().adjusted(4, 4, -4, -4))

    def dragEnterEvent(self, event: QDragEnterEvent):
        # Use Plugin
        if DragAndDropParser.parse_paths(event.mimeData()):
            event.accept()
            self.overlay.show()
            self.overlay.raise_()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        # Use Plugin
        if DragAndDropParser.parse_paths(event.mimeData()):
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self.overlay.hide()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.overlay.hide()
        # Use Plugin
        paths = DragAndDropParser.parse_paths(event.mimeData())
        if paths:
            event.accept()
            self.filesDropped.emit(paths)
        else:
            super().dropEvent(event)

# --- Main Tool Class ---

class PromptComposerTool(QWidget):
    statusMessage = pyqtSignal(str)
    modificationChanged = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.is_modified = False
        self.current_save_name = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        # 1. Top Bar
        top_layout = QHBoxLayout()
        
        lbl_root = QLabel("PROJECT ROOT:")
        apply_class(lbl_root, "text-primary font-bold")
        self.ln_root = QLineEdit()
        self.ln_root.setPlaceholderText("/path/to/project/root")
        self.ln_root.textChanged.connect(self.mark_as_modified)
        self.ln_root.textChanged.connect(self.refresh_all_paths)
        
        btn_browse = QPushButton("[...]")
        btn_browse.setFixedWidth(40)
        btn_browse.clicked.connect(self.browse_root)
        
        self.btn_add = QPushButton(" + BLOCK ")
        apply_class(self.btn_add, "font-bold")
        self.btn_add.clicked.connect(lambda: self.add_item())
        
        self.btn_clear = QPushButton(" CLEAR ")
        self.btn_clear.clicked.connect(self.request_clear)

        top_layout.addWidget(lbl_root)
        top_layout.addWidget(self.ln_root)
        top_layout.addWidget(btn_browse)
        top_layout.addSpacing(15)
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_clear)
        
        main_layout.addLayout(top_layout)

        # 2. Splitter Area
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # List
        self.list_widget = OverlayFileListWidget()
        self.list_widget.model().rowsMoved.connect(lambda: self.mark_as_modified())
        self.list_widget.filesDropped.connect(self.handle_files_dropped)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        splitter.addWidget(self.list_widget)

        # Preview Area
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(4)
        
        # --- PREVIEW TOOLBAR ---
        p_bar = QHBoxLayout()
        p_lbl = QLabel("> COMPILED OUTPUT")
        apply_class(p_lbl, "text-primary font-bold")
        
        # 1. Options Menu (Import/Export)
        self.btn_options = QPushButton(" OPTIONS ")
        self.options_menu = QMenu(self)
        
        act_import = self.options_menu.addAction("Import JSON")
        act_import.triggered.connect(self.import_from_json)
        
        act_export = self.options_menu.addAction("Export JSON")
        act_export.triggered.connect(self.export_to_json)
        
        self.btn_options.setMenu(self.options_menu)

        # 2. Action Buttons
        self.btn_generate_copy = QPushButton(" GEN & COPY ")
        self.btn_generate_copy.clicked.connect(self.generate_and_copy)
        apply_class(self.btn_generate_copy, "font-bold")

        self.btn_generate = QPushButton(" GEN ONLY ")
        self.btn_generate.clicked.connect(self.generate_only)

        self.btn_copy = QPushButton(" COPY ONLY ")
        self.btn_copy.clicked.connect(self.copy_only)

        # Layout Assembly
        p_bar.addWidget(p_lbl)
        p_bar.addStretch()
        p_bar.addWidget(self.btn_options)         # Context Menu Button
        p_bar.addWidget(self.btn_generate_copy)   # Priority 1
        p_bar.addWidget(self.btn_generate)        # Priority 2
        p_bar.addWidget(self.btn_copy)            # Priority 3
        
        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        
        preview_layout.addLayout(p_bar)
        preview_layout.addWidget(self.txt_result)
        
        splitter.addWidget(preview_widget)
        splitter.setSizes([500, 200]) 
        main_layout.addWidget(splitter)
        
        self.add_item() 

    # --- Handlers ---
    def handle_files_dropped(self, paths):
        for path in paths:
            self.add_item({
                "type": "Folder Tree" if os.path.isdir(path) else "File",
                "target_path": path,
                "path_mode": "Relative Path"
            })
        self.mark_as_modified()
        self.statusMessage.emit(f"Added {len(paths)} items.")

    def handle_unsaved_changes(self):
        if not self.is_modified: return True
        msg = QMessageBox(self)
        msg.setWindowTitle("Unsaved Changes")
        msg.setText("Save unsaved changes?")
        msg.setStandardButtons(QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel)
        ret = msg.exec()
        if ret == QMessageBox.StandardButton.Save: return self.save_content()
        elif ret == QMessageBox.StandardButton.Discard: return True
        return False

    def save_content(self):
        config_data = self._gather_data()
        dlg = PromptStateDialog(self, mode="save", current_name=self.current_save_name)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            save_name = dlg.selected_name
            success, msg = DBManager.save_prompt(save_name, config_data)
            if success:
                self.current_save_name = save_name
                self.statusMessage.emit(f"Saved: {self.current_save_name}")
                self.set_modified(False)
                return True
            else:
                QMessageBox.critical(self, "Error", msg)
                return False
        return False

    def load_content(self):
        if not self.handle_unsaved_changes(): return
        dlg = PromptStateDialog(self, mode="load")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            load_name = dlg.selected_name
            data = DBManager.load_prompt(load_name)
            if data:
                self._load_data(data)
                self.current_save_name = load_name
                self.set_modified(False)
                self.statusMessage.emit(f"Loaded: {self.current_save_name}")

    def import_from_json(self):
        if not self.handle_unsaved_changes(): return
        fname, _ = QFileDialog.getOpenFileName(self, "Import", "", "JSON (*.json)")
        if fname:
            with open(fname, 'r') as f: self._load_data(json.load(f))
            self.current_save_name = None
            self.mark_as_modified()

    def export_to_json(self):
        data = self._gather_data()
        fname, _ = QFileDialog.getSaveFileName(self, "Export", "", "JSON (*.json)")
        if fname:
            with open(fname, 'w') as f: json.dump(data, f, indent=2)

    def request_clear(self):
        if self.handle_unsaved_changes(): self.clear_all()

    def _gather_data(self):
        data = { "project_root": self.ln_root.text(), "items": [] }
        for i in range(self.list_widget.count()):
            w = self.list_widget.itemWidget(self.list_widget.item(i))
            if w: data["items"].append(w.get_state())
        return data

    def _load_data(self, data):
        if isinstance(data, list): items, root = data, ""
        else: items, root = data.get("items", []), data.get("project_root", "")
        self.ln_root.setText(root)
        self.list_widget.clear()
        for entry in items: self.add_item(entry)

    def set_modified(self, state=True):
        self.is_modified = state
        self.modificationChanged.emit(state)
    
    def mark_as_modified(self):
        if not self.is_modified: self.set_modified(True)

    def get_project_root(self): return self.ln_root.text().strip()
    
    def browse_root(self):
        d = QFileDialog.getExistingDirectory(self, "Select Project Root")
        if d: self.ln_root.setText(d)

    def refresh_all_paths(self):
        for i in range(self.list_widget.count()):
            w = self.list_widget.itemWidget(self.list_widget.item(i))
            if w: w.update_display() 

    def add_item(self, data=None):
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(100, 105)) 
        widget = PromptItemWidget(item, self.list_widget, self.get_project_root)
        widget.contentChanged.connect(self.mark_as_modified)
        self.list_widget.setItemWidget(item, widget)
        if data: widget.set_state(data)
        else: self.mark_as_modified()

    def clear_all(self):
        self.list_widget.clear()
        self.txt_result.clear()
        self.current_save_name = None
        self.mark_as_modified()

    # --- Generation Logic ---

    def generate_only(self):
        output = []
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if widget: output.append(widget.get_compiled_output())
        res = "\n".join(output)
        self.txt_result.setText(res)
        self.statusMessage.emit("Prompt generated!")
        return res

    def copy_only(self):
        # Regenerate to ensure we are copying exact current state
        res = self.generate_only() 
        QApplication.clipboard().setText(res)
        self.statusMessage.emit("Prompt copied!")

    def generate_and_copy(self):
        self.generate_only()
        self.copy_only()
        self.statusMessage.emit("Prompt generated and copied to clipboard!")