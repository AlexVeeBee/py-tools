import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QListWidgetItem, QTextEdit, QLabel, 
                             QFileDialog, QSplitter, QMessageBox,
                             QAbstractItemView, QApplication, QDialog, QMenu)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QDragMoveEvent

# --- IMPORTS ---
from components.prompt import PromptItemWidget, DroppableLineEdit
from components.prompt.settings import ProjectSettingsDialog
from components.prompt.generator import generate_tree_text
from components.db_manager import DBManager
from components.prompt_state_dialog import PromptStateDialog
from components.styles import apply_class, C_PRIMARY, C_BG_MAIN, C_DANGER
from components.mime_parser import DragAndDropParser

# --- Helpers ---

def parse_gitignore_lines(file_path):
    """Reads a .gitignore file and returns a list of valid patterns."""
    patterns = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    patterns.append(line)
    except Exception as e:
        print(f"Error reading .gitignore: {e}")
    return patterns

def find_git_ignore(start_path):
    """Searches for a .gitignore file from start_path upwards."""
    current_path = os.path.abspath(start_path)
    while True:
        gitignore_path = os.path.join(current_path, '.gitignore')
        if os.path.isfile(gitignore_path):
            return gitignore_path
        parent_path = os.path.dirname(current_path)
        if parent_path == current_path:
            break
        current_path = parent_path
    return None


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
        self.is_modified = False
        self.current_save_name = None
        
        # Default Project Settings
        self.project_settings = {
            "include_tree": False,
            "global_ignore": ".git, __pycache__, node_modules, .idea, .vscode, .venv, dist, build"
        }

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)
        
        # 1. Top Bar: Root Path & Global Actions
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

        # Settings Button
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

        # 2. Main Content Area (Splitter)
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # A. Prompt Items List
        self.list_widget = OverlayFileListWidget()
        self.list_widget.model().rowsMoved.connect(lambda: self.mark_as_modified())
        self.list_widget.filesDropped.connect(self.handle_files_dropped)
        self.list_widget.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        splitter.addWidget(self.list_widget)

        # B. Preview Area
        preview_widget = QWidget()
        preview_layout = QVBoxLayout(preview_widget)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        preview_layout.setSpacing(4)
        
        # Outdated Warning
        self.lbl_outdated = QLabel("⚠ PREVIEW OUTDATED - REGENERATE")
        self.lbl_outdated.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_outdated.setStyleSheet(f"color: {C_DANGER}; font-weight: bold; font-size: 11px; margin-bottom: 2px;")
        self.lbl_outdated.setVisible(False)
        preview_layout.addWidget(self.lbl_outdated)

        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        preview_layout.addWidget(self.txt_result)

        # Bottom Toolbar (Generation & Options)
        bottom_bar = QHBoxLayout()
        
        self.btn_options = QPushButton(" OPTIONS ")
        self.options_menu = QMenu(self)
        
        act_import = self.options_menu.addAction("Import JSON")
        act_import.triggered.connect(self.import_from_json)
        
        act_export = self.options_menu.addAction("Export JSON")
        act_export.triggered.connect(self.export_to_json)
        
        self.options_menu.addSeparator()

        act_git = self.options_menu.addAction("Import .gitignore")
        act_git.triggered.connect(self.import_gitignore)

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
        actions_layout.setSpacing(5)
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
        
        # Start with one empty block
        self.add_item() 

    # --- Settings Logic ---
    def open_settings_dialog(self):
        """Open the project settings dialog."""
        dlg = ProjectSettingsDialog(self, self.project_settings)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.project_settings = dlg.get_settings()
            self.mark_as_modified()
            self.statusMessage.emit("Settings updated.")

    # --- Item Management ---
    def handle_files_dropped(self, paths):
        for path in paths:
            self.add_item({
                "type": "Folder Tree" if os.path.isdir(path) else "File",
                "target_path": path,
                "path_mode": "Relative Path"
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

    def clear_all(self):
        self.list_widget.clear()
        self.txt_result.clear()
        self.lbl_outdated.hide()
        self.current_save_name = None
        self.mark_as_modified()

    def import_gitignore(self):
        """Finds .gitignore, parses it, and appends unique patterns to global settings."""
        root = self.get_project_root()
        if not root or not os.path.exists(root):
            QMessageBox.warning(self, "Path Error", "Please select a valid Project Root first.")
            return

        git_path = find_git_ignore(root)
        
        if not git_path:
            QMessageBox.information(self, "Not Found", "No .gitignore file found in project root or parent directories.")
            return

        # Parse the file
        new_patterns = parse_gitignore_lines(git_path)
        if not new_patterns:
            self.statusMessage.emit(".gitignore found, but it was empty.")
            return

        # Get existing settings
        current_str = self.project_settings.get("global_ignore", "")
        # Convert comma-string to list, stripping whitespace
        current_list = [x.strip() for x in current_str.split(',') if x.strip()]
        
        added_count = 0
        for pattern in new_patterns:
            if pattern not in current_list:
                current_list.append(pattern)
                added_count += 1
        
        if added_count > 0:
            # Update settings
            self.project_settings["global_ignore"] = ", ".join(current_list)
            self.mark_as_modified()
            
            QMessageBox.information(self, "Success", 
                                    f"Imported {added_count} new patterns from:\n{git_path}")
            self.statusMessage.emit(f"Imported {added_count} ignore patterns.")
        else:
            self.statusMessage.emit("All patterns in .gitignore are already included.")

    def refresh_all_paths(self):
        """Updates display text of relative paths if root changes."""
        for i in range(self.list_widget.count()):
            w = self.list_widget.itemWidget(self.list_widget.item(i))
            if w: w.update_display() 

    # --- Save/Load/Import/Export ---
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
            try:
                with open(fname, 'r') as f: self._load_data(json.load(f))
                self.current_save_name = None
                self.mark_as_modified()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Invalid JSON: {str(e)}")

    def export_to_json(self):
        data = self._gather_data()
        fname, _ = QFileDialog.getSaveFileName(self, "Export", "", "JSON (*.json)")
        if fname:
            with open(fname, 'w') as f: json.dump(data, f, indent=2)

    def _gather_data(self):
        """Collects state from inputs and widgets."""
        data = { 
            "project_root": self.ln_root.text(), 
            "settings": self.project_settings, 
            "items": [] 
        }
        for i in range(self.list_widget.count()):
            w = self.list_widget.itemWidget(self.list_widget.item(i))
            if w: data["items"].append(w.get_state())
        return data

    def _load_data(self, data):
        """Restores state to inputs and widgets."""
        if isinstance(data, list): 
            # Legacy format support
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

    # --- Generation Logic ---
    def generate_only(self):
        output = []
        
        # 1. Prepend Project Tree if enabled in settings
        if self.project_settings.get("include_tree"):
            root = self.get_project_root()
            ignores = self.project_settings.get("global_ignore", "")
            if root and os.path.exists(root):
                try:
                    tree_content = generate_tree_text(root, ignores)
                    output.append(f"PROJECT DIRECTORY STRUCTURE:\n```\n{tree_content}\n```\n")
                    output.append("-" * 30)
                except Exception as e:
                    output.append(f"[ERROR generating tree: {str(e)}]\n")
            elif root:
                output.append(f"[WARNING: Project root '{root}' not found]\n")

        # 2. Append Standard Blocks
        for i in range(self.list_widget.count()):
            widget = self.list_widget.itemWidget(self.list_widget.item(i))
            if widget:
                block = widget.get_compiled_output()
                if block.strip():
                    output.append(block)

        res = "\n".join(output)
        self.txt_result.setText(res)
        self.lbl_outdated.setVisible(False) 
        self.statusMessage.emit("Prompt generated!")
        self.label_chr_info.setText(f"Characters: {len(res)}")
        return res

    def copy_only(self):
        res = self.txt_result.toPlainText()
        if not res and self.list_widget.count() > 0:
            res = self.generate_only()
            
        QApplication.clipboard().setText(res)
        self.statusMessage.emit("Prompt copied!")

    def generate_and_copy(self):
        self.generate_only()
        self.copy_only()
        self.statusMessage.emit("Prompt generated and copied to clipboard!")

    # --- Helpers ---
    def set_modified(self, state=True):
        self.is_modified = state
        self.modificationChanged.emit(state)
    
    def mark_as_modified(self):
        if not self.is_modified: self.set_modified(True)
        if self.txt_result.toPlainText().strip():
            self.lbl_outdated.setVisible(True)

    def get_project_root(self): 
        return self.ln_root.text().strip()
    
    def browse_root(self):
        d = QFileDialog.getExistingDirectory(self, "Select Project Root")
        if d:
            if os.name == 'nt':
                d = d.replace("/", "\\")
            self.ln_root.setText(d)
            self.import_gitignore()

    def request_clear(self):
        if self.handle_unsaved_changes(): self.clear_all()