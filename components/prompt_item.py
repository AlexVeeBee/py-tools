import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QComboBox, QPushButton, QFileDialog, QPlainTextEdit, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from components.styles import C_DANGER, C_TEXT_MUTED, C_TEXT_MAIN, C_BORDER, C_BG_INPUT, C_PRIMARY
from components.mime_parser import DragAndDropParser # Imported Plugin
doeblockFileTypes = {
    'txt': 'plaintext',
    'md': 'Markdown',
    'json': 'JSON',
    'yaml': 'YAML',
    'yml': 'YAML',
    'csv': 'CSV',
    'py': 'Python',
    'js': 'JavaScript',
    'ts': 'TypeScript',
    'java': 'Java',
    'cpp': 'C++',
}

# Helper for Droppable Line Edit
class DroppableLineEdit(QLineEdit):
    fileDropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._original_style = ""

    def dragEnterEvent(self, e):
        # Use Plugin
        paths = DragAndDropParser.parse_paths(e.mimeData())
        if paths:
            e.accept()
            # Save current style (e.g., error red border) to restore later
            self._original_style = self.styleSheet()
            # Apply visual indicator
            self.setStyleSheet(f"border: 2px dashed {C_PRIMARY}; background-color: {C_BG_INPUT};")
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        # Use Plugin
        if DragAndDropParser.parse_paths(e.mimeData()):
            e.accept()
        else:
            super().dragMoveEvent(e)

    def dragLeaveEvent(self, e):
        # Restore original style
        self.setStyleSheet(self._original_style)
        super().dragLeaveEvent(e)

    def dropEvent(self, e):
        # Restore original style
        self.setStyleSheet(self._original_style)
        
        # Use Plugin
        paths = DragAndDropParser.parse_paths(e.mimeData())
        if paths:
            # Only take the first path for single line edit
            self.fileDropped.emit(paths[0])
        else:
            super().dropEvent(e)

# --- Logic Helpers ---
def get_formatted_path(target, mode, root):
    if not target: return ""
    if mode == "Name Only": return os.path.basename(target)
    if mode == "Relative Path" and root and target.startswith(root):
        try: return os.path.relpath(target, root)
        except: pass
    return target

def generate_tree(root, ignore):
    output = []
    ignores = {x.strip() for x in ignore.split(',') if x.strip()}
    def add(d, p=''):
        try:
            items = sorted([x for x in os.listdir(d) if x not in ignores and not x.startswith('.')])
            ptrs = ['├── '] * (len(items)-1) + ['└── '] if items else []
            for ptr, name in zip(ptrs, items):
                output.append(f"{p}{ptr}{name}")
                full = os.path.join(d, name)
                if os.path.isdir(full): add(full, p + ('│   ' if ptr == '├── ' else '    '))
        except: pass
    if root: output.append(os.path.basename(root)+"/"); add(root)
    return "\n".join(output)

def get_codeblock_language(path):
    ext = os.path.splitext(path)[1][1:].lower()
    return doeblockFileTypes.get(ext, 'plaintext')

def compile_prompt_data(data, root=""):
    mode = data.get("type", "Message")
    text = data.get("text", "").strip()
    tgt = data.get("target_path", "")
    out = f"{text}\n" if text else ""
    if mode != "Message" and tgt and os.path.exists(tgt):
        disp = get_formatted_path(tgt, data.get("path_mode"), root)
        if mode == "File":
            try: 
                with open(tgt, 'r', encoding='utf-8', errors='ignore') as f:
                    lang = get_codeblock_language(tgt)
                    out += f"\nFile: {disp}\n```{lang}\n{f.read()}\n```\n"
            except: out += f"[Error reading {disp}]\n"
        elif mode == "Folder Tree":
            out += f"\nDir: {disp}\n```\n{generate_tree(tgt, data.get('ignore_patterns',''))}\n```\n"
    return out

# --- Widget ---
class PromptItemWidget(QWidget):
    contentChanged = pyqtSignal()

    def __init__(self, parent_item, list_widget, root_getter, read_only=False):
        super().__init__()
        self.parent_item = parent_item
        self.list_widget = list_widget
        self.get_root = root_getter
        self.read_only = read_only
        self.target_path = ""

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # 1. Drag Handle (Hide in Read Only)
        self.lbl_handle = QLabel("||")
        self.lbl_handle.setFixedWidth(15)
        self.lbl_handle.setStyleSheet(f"color: {C_TEXT_MUTED}; font-weight: bold; font-family: monospace;")
        if not read_only:
            self.lbl_handle.setCursor(Qt.CursorShape.SizeAllCursor)
        else:
            self.lbl_handle.setVisible(False)
        layout.addWidget(self.lbl_handle)

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
        layout.addWidget(w_cfg)

        # 3. Text Area
        self.txt_prompt = QPlainTextEdit()
        self.txt_prompt.setAcceptDrops(False) # Disable drops to prevent interfering with parent list drag-drop
        self.txt_prompt.textChanged.connect(self._emit)
        layout.addWidget(self.txt_prompt, stretch=3)

        # 4. Path Controls
        col_path = QVBoxLayout()
        col_path.setSpacing(2)
        col_path.setContentsMargins(0,0,0,0)
        
        row_p = QHBoxLayout()
        self.ln_path = DroppableLineEdit()
        self.ln_path.setReadOnly(True) # Always read only, but accepts drops
        self.ln_path.setPlaceholderText("<Drag file here>")
        self.ln_path.fileDropped.connect(self.handle_drop)
        
        self.btn_br = QPushButton("...")
        self.btn_br.setFixedWidth(30)
        self.btn_br.clicked.connect(self.browse)
        
        row_p.addWidget(self.ln_path)
        row_p.addWidget(self.btn_br)
        
        self.ln_ignore = QLineEdit()
        self.ln_ignore.setPlaceholderText("Ignore: .git, node_modules, __pycache__, .idea, .vscode, dist, build")
        self.ln_ignore.setText("Ignore: .git, node_modules, __pycache__, .idea, .vscode, dist, build")
        self.ln_ignore.textChanged.connect(self._emit)
        
        col_path.addLayout(row_p)
        col_path.addWidget(self.ln_ignore)
        col_path.addStretch()
        
        self.w_path = QWidget()
        self.w_path.setLayout(col_path)
        layout.addWidget(self.w_path, stretch=4)

        # 5. Delete (Hide in Read Only)
        self.btn_del = QPushButton("X")
        self.btn_del.setFixedSize(22, 22)
        self.btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_del.setStyleSheet(f"background: transparent; border: 1px solid {C_DANGER}; color: {C_DANGER}; font-weight: bold;")
        self.btn_del.clicked.connect(self.remove_self)
        
        if read_only:
            self.btn_del.setVisible(False)
            self._apply_read_only_mode()
        else:
            layout.addWidget(self.btn_del, alignment=Qt.AlignmentFlag.AlignTop)

        self.on_type_changed("Message")

    def _apply_read_only_mode(self):
        """Disables interactions for preview mode"""
        self.combo_type.setEnabled(False)
        self.combo_mode.setEnabled(False)
        self.txt_prompt.setReadOnly(True)
        self.ln_ignore.setReadOnly(True)
        self.ln_path.setAcceptDrops(False)
        self.btn_br.setVisible(False)
        
        # Style tweaks to make it look "locked" but readable
        style_disabled = f"color: {C_TEXT_MAIN}; background: {C_BG_INPUT}; border: none;"
        self.combo_type.setStyleSheet(style_disabled)
        self.combo_mode.setStyleSheet(style_disabled)

    def _emit(self): 
        if not self.read_only:
            self.contentChanged.emit()

    def on_type_changed(self, text):
        is_msg = text == "Message"
        self.w_path.setVisible(not is_msg)
        self.combo_mode.setVisible(not is_msg)
        self.ln_ignore.setVisible(text == "Folder Tree")
        
        if not self.read_only:
            self.txt_prompt.setPlaceholderText("// Enter instructions..." if is_msg else "// Context note...")
        
        if is_msg: self.ln_path.clear(); self.target_path = ""

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
        
        # Only check existence if we are editing. In preview, file might not exist on this machine if moved.
        if not self.read_only and self.target_path and not os.path.exists(self.target_path):
            self.ln_path.setStyleSheet(f"border: 1px solid {C_DANGER}; color: {C_DANGER};")
        else:
            self.ln_path.setStyleSheet("")

    def remove_self(self):
        if self.read_only: return
        self.list_widget.takeItem(self.list_widget.row(self.parent_item))
        self._emit()

    def get_state(self):
        return {
            "type": self.combo_type.currentText(),
            "path_mode": self.combo_mode.currentText(),
            "text": self.txt_prompt.toPlainText(),
            "target_path": self.target_path,
            "ignore_patterns": self.ln_ignore.text()
        }

    def set_state(self, d):
        self.blockSignals(True)
        self.combo_type.setCurrentText(d.get("type", "Message"))
        self.combo_mode.setCurrentText(d.get("path_mode", "Relative Path"))
        self.txt_prompt.setPlainText(d.get("text", ""))
        self.ln_ignore.setText(d.get("ignore_patterns", ".git, node_modules, __pycache__, .idea, .vscode, dist, build"))
        self.target_path = d.get("target_path", "")
        self.update_display()
        self.blockSignals(False)

    def get_compiled_output(self):
        return compile_prompt_data(self.get_state(), self.get_root())