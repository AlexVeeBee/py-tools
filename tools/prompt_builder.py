import json
import os
from PyQt6.QtWidgets import (QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QTextEdit, QLabel,
                             QFileDialog, QSplitter, QMessageBox,
                             QAbstractItemView, QApplication, QDialog, QMenu, QComboBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent

# --- IMPORTS ---
from components.prompt import PromptItemWidget, DroppableLineEdit
from components.prompt.settings import ProjectSettingsDialog
from components.prompt.generator import generate_tree_text
from components.db_manager import DBManager
from components.prompt_state_dialog import PromptStateDialog
from components.styles import apply_class, C_PRIMARY, C_BG_MAIN, C_DANGER, C_BG_SECONDARY, C_BORDER, C_TEXT_MAIN
from components.mime_parser import DragAndDropParser
from components.plugin_system import PluginManager

# Import Core Plugins Registerer
from components.plugin_system import PluginManager
from components.plugins_core import register_core_plugins

# --- HELPERS ---
def find_git_ignore(start_path):
    # ... (Keep existing implementation) ...
    current_path = os.path.abspath(start_path)
    while True:
        gitignore_path = os.path.join(current_path, '.gitignore')
        if os.path.isfile(gitignore_path):
            return gitignore_path
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path: break
        current_path = parent_path
    return None

def parse_gitignore_lines(file_path):
    # ... (Keep existing implementation) ...
    patterns = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'): patterns.append(line)
    except: pass
    return patterns

# --- NEW: Drop Selection Dialog ---
class DropSelectionDialog(QDialog):
    def __init__(self, paths, plugin_manager, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Import Files")
        self.setMinimumWidth(400)
        self.paths = paths
        self.pm = plugin_manager
        
        layout = QVBoxLayout(self)
        
        # Header
        label_dropped_count = QLabel(f"Dropped {len(paths)} item(s):")
        label_dropped_count.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(label_dropped_count)
        
        # File List
        self.list_w = QListWidget()
        self.list_w.addItems([os.path.basename(p) for p in paths])
        self.list_w.setStyleSheet(f"background: {C_BG_SECONDARY}; color: {C_TEXT_MAIN}; border: 1px solid {C_BORDER};")
        self.list_w.setMinimumHeight(100)
        layout.addWidget(self.list_w)
        
        # Logic to Detect Content Types
        has_files = any(os.path.isfile(p) for p in paths)
        has_folders = any(os.path.isdir(p) for p in paths)
        
        # Selection
        label_select = QLabel("Import as Block Type:")
        layout.addWidget(label_select)
        self.combo = QComboBox()
        self.combo.setStyleSheet(f"background: {C_BG_SECONDARY}; color: {C_TEXT_MAIN}; border: 1px solid {C_BORDER}; padding: 5px;")
        
        # --- Filter Plugins based on drag_types ---
        valid_count = 0
        all_plugins = self.pm.get_all_plugins()

        for plugin in all_plugins:
            supported = plugin.drag_types 
            
            # Check constraints
            if has_folders and "folder" not in supported: continue
            if has_files and "file" not in supported: continue
            
            self.combo.addItem(plugin.name, plugin.id)
            valid_count += 1

            # Smart Selection Pre-set
            if has_folders and plugin.id == "core.tree":
                self.combo.setCurrentIndex(valid_count - 1)
            elif not has_folders and has_files and plugin.id == "core.file":
                self.combo.setCurrentIndex(valid_count - 1)

        # Fallback: If no strict matches, show all (avoids locking UI)
        if valid_count == 0:
            self.combo.clear()
            self.combo.addItem("--- No matching plugins found (Showing All) ---", None)
            self.combo.model().item(0).setEnabled(False) 
            for plugin in all_plugins:
                self.combo.addItem(plugin.name, plugin.id)
            if self.combo.count() > 1: self.combo.setCurrentIndex(1)
                
        layout.addWidget(self.combo)
        
        # Buttons
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_selected_plugin_id(self):
        return self.combo.currentData()
        
# --- CUSTOM WIDGET: List with Absolute Drop Overlay ---
class OverlayFileListWidget(QListWidget):
    filesDropped = pyqtSignal(list) 

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Visual Overlay for Dragging
        self.overlay = QLabel("DROP FILES OR FOLDERS HERE", self)
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
        if DragAndDropParser.parse_paths(event.mimeData()):
            event.accept()
            self.overlay.show()
            self.overlay.raise_()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragMoveEvent):
        if DragAndDropParser.parse_paths(event.mimeData()):
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self.overlay.hide()
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent):
        self.overlay.hide()
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
        
        # 1. SETUP PLUGINS
        self.pm = PluginManager()
        register_core_plugins() # Load Core (Msg, File, Tree)
        
        # Load custom plugins from 'plugins' folder next to 'tools'
        current_dir = os.path.dirname(os.path.abspath(__file__)) # tools/
        root_dir = os.path.dirname(current_dir) # root/
        plugins_dir = os.path.join(root_dir, "plugins")
        self.pm.load_from_folder(plugins_dir)

        self.is_modified = False
        self.current_save_name = None
        
        # Project Settings
        self.project_settings = {
            "include_tree": False,
            "global_ignore": ".git, __pycache__, node_modules, .idea, .vscode, .venv, dist, build"
        }

        # --- UI LAYOUT ---
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        # 1. Top Bar
        top_layout = QHBoxLayout()
        lbl_root = QLabel("PROJECT ROOT:")
        apply_class(lbl_root, "text-primary font-bold")
        
        self.ln_root = DroppableLineEdit()
        self.ln_root.setPlaceholderText("/path/to/project/root")
        self.ln_root.textChanged.connect(self.mark_as_modified)
        self.ln_root.textChanged.connect(self.refresh_all_paths)
        self.ln_root.fileDropped.connect(self.ln_root.setText)
        
        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(40)
        btn_browse.clicked.connect(self.browse_root)

        btn_settings = QPushButton("SETTINGS")
        btn_settings.clicked.connect(self.open_settings_dialog)
        
        self.btn_add = QPushButton("+ BLOCK")
        apply_class(self.btn_add, "font-bold")
        self.btn_add.clicked.connect(lambda: self.add_item())
        
        self.btn_clear = QPushButton("CLEAR")
        self.btn_clear.clicked.connect(self.request_clear)

        top_layout.addWidget(lbl_root)
        top_layout.addWidget(self.ln_root)
        top_layout.addWidget(btn_browse)
        top_layout.addWidget(btn_settings)
        top_layout.addSpacing(15)
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_clear)
        
        main_layout.addLayout(top_layout)

        # 2. Main Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # List Widget
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
        
        self.lbl_outdated = QLabel("⚠ PREVIEW OUTDATED - REGENERATE")
        self.lbl_outdated.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_outdated.setStyleSheet(f"color: {C_DANGER}; font-weight: bold; font-size: 11px;")
        self.lbl_outdated.setVisible(False)
        preview_layout.addWidget(self.lbl_outdated)

        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        preview_layout.addWidget(self.txt_result)

        # Bottom Bar
        bottom_bar = QHBoxLayout()
        self.btn_options = QPushButton(" OPTIONS ")
        self.options_menu = QMenu(self)
        self.options_menu.addAction("Import JSON").triggered.connect(self.import_from_json)
        self.options_menu.addAction("Export JSON").triggered.connect(self.export_to_json)
        self.options_menu.addSeparator()
        self.options_menu.addAction("Import .gitignore").triggered.connect(self.import_gitignore)
        self.btn_options.setMenu(self.options_menu)

        self.btn_generate_copy = QPushButton("GENERATE & COPY")
        self.btn_generate_copy.clicked.connect(self.generate_and_copy)
        self.btn_generate_copy.setStyleSheet(f"background-color: {C_PRIMARY}; color: {C_BG_MAIN}; font-weight: bold;")

        self.btn_generate = QPushButton("GENERATE")
        self.btn_generate.clicked.connect(self.generate_only)
        self.btn_copy = QPushButton("COPY")
        self.btn_copy.clicked.connect(self.copy_only)
        self.label_chr_info = QLabel("Characters: 0")

        self.btn_actions = QWidget()
        actions_layout = QHBoxLayout(self.btn_actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.addWidget(self.btn_generate_copy)
        actions_layout.addWidget(self.btn_generate)
        actions_layout.addWidget(self.btn_copy)
        actions_layout.addWidget(self.label_chr_info)

        bottom_bar.addWidget(self.btn_actions)
        bottom_bar.addStretch()
        bottom_bar.addWidget(self.btn_options)
        
        preview_layout.addLayout(bottom_bar)
        splitter.addWidget(preview_widget)
        splitter.setSizes([500, 200]) 
        main_layout.addWidget(splitter)
        
        self.add_item() 

    # --- UPDATED: HANDLE FILES DROPPED ---
    def handle_files_dropped(self, paths):
        """Shows selection dialog (or auto-imports if only 1 option exists)."""
        if not paths: return
        
        # 1. Initialize Dialog (Calculates valid options internally)
        dlg = DropSelectionDialog(paths, self.pm, self)
        
        selected_plugin_id = None
        
        # 2. Check Logic: Auto-Import vs Show Dialog
        # If we have exactly 1 valid option, skip the .exec() call
        if dlg.combo.count() == 1:
            selected_plugin_id = dlg.get_selected_plugin_id()
            self.statusMessage.emit(f"Auto-importing using: {self.pm.get_plugin(selected_plugin_id).name}")
        else:
            # Multiple options or No matches (fallback mode) -> Show Dialog
            if dlg.exec() == QDialog.DialogCode.Accepted:
                selected_plugin_id = dlg.get_selected_plugin_id()
            else:
                return # User cancelled

        # 3. Add Blocks if we have a valid ID
        if selected_plugin_id:
            # Check if this plugin expects specific drag types to handle data keys
            plugin_name = self.pm.get_plugin(selected_plugin_id).id
            
            for path in paths:
                data = {}
                # Generic handling: most blocks use 'path'
                data["path"] = path 
                
                self.add_item({
                    "plugin_id": selected_plugin_id,
                    "data": data
                })
            
            self.mark_as_modified()
            self.statusMessage.emit(f"Added {len(paths)} items.")

    def add_item(self, data=None):
        item = QListWidgetItem(self.list_widget)
        item.setSizeHint(QSize(100, 80)) 
        widget = PromptItemWidget(item, self.list_widget, self.get_project_root)
        widget.contentChanged.connect(self.mark_as_modified)
        self.list_widget.setItemWidget(item, widget)
        if data: widget.set_state(data)
        else: self.mark_as_modified()

    # ... (Keep remaining methods: open_settings_dialog, import_gitignore, save/load, generate logic) ...
    # They are unchanged from previous versions aside from ensuring imports exist.
    
    def open_settings_dialog(self):
        dlg = ProjectSettingsDialog(self, self.project_settings)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.project_settings = dlg.get_settings()
            self.mark_as_modified()
            self.statusMessage.emit("Settings updated.")

    def clear_all(self):
        self.list_widget.clear()
        self.txt_result.clear()
        self.lbl_outdated.hide()
        self.current_save_name = None
        self.mark_as_modified()

    def import_gitignore(self):
        root = self.get_project_root()
        if not root or not os.path.exists(root):
            QMessageBox.warning(self, "Path Error", "Select Project Root first.")
            return
        git_path = find_git_ignore(root)
        if not git_path:
            QMessageBox.information(self, "Not Found", "No .gitignore found.")
            return
        new_patterns = parse_gitignore_lines(git_path)
        if not new_patterns: return
        
        current_str = self.project_settings.get("global_ignore", "")
        current_list = [x.strip() for x in current_str.split(',') if x.strip()]
        added = 0
        for p in new_patterns:
            if p not in current_list:
                current_list.append(p)
                added += 1
        
        if added > 0:
            self.project_settings["global_ignore"] = ", ".join(current_list)
            self.mark_as_modified()
            QMessageBox.information(self, "Success", f"Imported {added} patterns.")

    def refresh_all_paths(self):
        # We can't force refresh easily on plugin widgets without a standardized 'refresh' method,
        # but most update on interaction. 
        # Ideally, we could add a `refresh_ui()` to BlockPluginInterface.
        pass

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
        data = self._gather_data()
        dlg = PromptStateDialog(self, mode="save", current_name=self.current_save_name)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            save_name = dlg.selected_name
            success, msg = DBManager.save_prompt(save_name, data)
            if success:
                self.current_save_name = save_name
                self.statusMessage.emit(f"Saved: {save_name}")
                self.set_modified(False)
                return True
            else:
                QMessageBox.critical(self, "Error", msg)
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
                self.statusMessage.emit(f"Loaded: {load_name}")

    def import_from_json(self):
        if not self.handle_unsaved_changes(): return
        fname, _ = QFileDialog.getOpenFileName(self, "Import", "", "JSON (*.json)")
        if fname:
            try:
                with open(fname, 'r') as f: self._load_data(json.load(f))
                self.current_save_name = None
                self.mark_as_modified()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid JSON: {e}")

    def export_to_json(self):
        data = self._gather_data()
        fname, _ = QFileDialog.getSaveFileName(self, "Export", "", "JSON (*.json)")
        if fname:
            with open(fname, 'w') as f: json.dump(data, f, indent=2)

    def _gather_data(self):
        data = { "project_root": self.ln_root.text(), "settings": self.project_settings, "items": [] }
        for i in range(self.list_widget.count()):
            w = self.list_widget.itemWidget(self.list_widget.item(i))
            if w: data["items"].append(w.get_state())
        return data

    def _load_data(self, data):
        # Handle Legacy List format
        if isinstance(data, list):
            items = data
            root = ""
            settings = {}
        else:
            items = data.get("items", [])
            root = data.get("project_root", "")
            settings = data.get("settings", {})

        self.ln_root.setText(root)
        self.project_settings.update(settings)
        self.list_widget.clear()
        self.txt_result.clear()
        self.lbl_outdated.hide()
        for entry in items: self.add_item(entry)

    def generate_only(self):
        output = []
        
        # Get Global Ignore Setting
        global_ignores = self.project_settings.get("global_ignore", "")

        # Prepend Tree if enabled globally
        if self.project_settings.get("include_tree"):
            root = self.get_project_root()
            if root and os.path.exists(root):
                try:
                    tree = generate_tree_text(root, global_ignores)
                    output.append(f"PROJECT STRUCTURE:\n```\n{tree}\n```\n{'-'*30}")
                except Exception as e: output.append(f"[Error tree: {e}]")
        
        # Plugins
        for i in range(self.list_widget.count()):
            w = self.list_widget.itemWidget(self.list_widget.item(i))
            if w:
                # PASS THE GLOBAL IGNORE HERE
                block = w.get_compiled_output(global_ignore=global_ignores)
                if block.strip(): output.append(block)

        res = "\n".join(output)
        self.txt_result.setText(res)
        self.lbl_outdated.setVisible(False)
        self.statusMessage.emit("Generated.")
        self.label_chr_info.setText(f"Characters: {len(res)}")
        return res
    
    def copy_only(self):
        res = self.txt_result.toPlainText()
        if not res and self.list_widget.count() > 0: res = self.generate_only()
        QApplication.clipboard().setText(res)
        self.statusMessage.emit("Copied.")

    def generate_and_copy(self):
        self.generate_only()
        self.copy_only()

    def set_modified(self, state=True):
        self.is_modified = state
        self.modificationChanged.emit(state)
    
    def mark_as_modified(self):
        if not self.is_modified: self.set_modified(True)
        if self.txt_result.toPlainText().strip(): self.lbl_outdated.setVisible(True)

    def get_project_root(self): return self.ln_root.text().strip()
    
    def browse_root(self):
        d = QFileDialog.getExistingDirectory(self, "Project Root")
        if d:
            self.ln_root.setText(d.replace("/", "\\") if os.name=='nt' else d)
            self.import_gitignore()

    def request_clear(self):
        if self.handle_unsaved_changes(): self.clear_all()