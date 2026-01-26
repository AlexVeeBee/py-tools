import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QPlainTextEdit, QPushButton
from components.plugin_system import BlockPluginInterface
from components.prompt.common import DroppableLineEdit
from components.styles import C_TEXT_MAIN
from components.prompt.generator import (
    get_formatted_path, 
    read_file_content, 
    get_codeblock_language
)

class FileBlock(BlockPluginInterface):
    @property
    def name(self): return "File"
    @property
    def id(self): return "core.file"
    @property
    def drag_types(self): return ["file"]

    def create_ui(self, parent, root_getter, **kwargs):
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 1. Config
        col_cfg = QVBoxLayout()
        col_cfg.setContentsMargins(0,0,0,0)
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["Relative Path", "Name Only", "Full Path"])
        self.cb_mode.currentIndexChanged.connect(lambda: self._update_display(container))
        self.cb_mode.currentIndexChanged.connect(self.dataChanged.emit)
        col_cfg.addWidget(self.cb_mode)
        col_cfg.addStretch()
        
        w_cfg = QWidget()
        w_cfg.setFixedWidth(140)
        w_cfg.setLayout(col_cfg)
        layout.addWidget(w_cfg)

        # 2. Text
        self.txt_prompt = QPlainTextEdit()
        self.txt_prompt.setPlaceholderText("// Context note...")
        self.txt_prompt.setStyleSheet(f"color: {C_TEXT_MAIN};")
        self.txt_prompt.textChanged.connect(self.dataChanged.emit)
        layout.addWidget(self.txt_prompt, stretch=3)

        # 3. Path
        col_path = QVBoxLayout()
        col_path.setContentsMargins(0,0,0,0)
        row_p = QHBoxLayout()
        self.ln_path = DroppableLineEdit()
        self.ln_path.setReadOnly(True)
        self.ln_path.setPlaceholderText("<Drag file>")
        self.ln_path.fileDropped.connect(lambda p: self._handle_drop(container, p))

        btn_br = QPushButton("...")
        btn_br.setFixedWidth(30)
        btn_br.clicked.connect(lambda: self._browse(container))

        row_p.addWidget(self.ln_path)
        row_p.addWidget(btn_br)
        col_path.addLayout(row_p)
        col_path.addStretch()

        w_path = QWidget()
        w_path.setLayout(col_path)
        layout.addWidget(w_path, stretch=4)

        container.refs = {
            "mode": self.cb_mode,
            "text": self.txt_prompt,
            "path_display": self.ln_path,
            "target_path": ""
        }
        
        container.get_root = root_getter
        
        # --- Store the update_tag callback ---
        container.set_tag_cb = kwargs.get("update_tag", None)
        
        return container

    def _handle_drop(self, c, path):
        if os.path.isfile(path):
            c.refs["target_path"] = path
            self._update_display(c)
            self.dataChanged.emit()

    def _browse(self, c):
        from PyQt6.QtWidgets import QFileDialog
        f, _ = QFileDialog.getOpenFileName(c, "Select File")
        if f: self._handle_drop(c, f)

    def _update_display(self, c):
        p = c.refs["target_path"]
        m = c.refs["mode"].currentText()
        root = c.get_root() if hasattr(c, 'get_root') else ""
        txt = get_formatted_path(p, m, root)
        c.refs["path_display"].setText(txt)

        # --- Update the parent item's header tag ---
        if hasattr(c, "set_tag_cb") and c.set_tag_cb:
            if p:
                # Use file name and extension as tag
                tag = os.path.basename(p)
                c.set_tag_cb(tag)
            else:
                c.set_tag_cb("") # Hide if empty

    def get_state(self, w):
        return {
            "path": w.refs["target_path"],
            "mode": w.refs["mode"].currentText(),
            "text": w.refs["text"].toPlainText()
        }

    def set_state(self, w, s):
        w.refs["target_path"] = s.get("path", "")
        w.refs["mode"].setCurrentText(s.get("mode", "Relative Path"))
        w.refs["text"].setPlainText(s.get("text", ""))
        self._update_display(w)

    def compile(self, s, root, **kwargs):
        p = s.get("path", "")
        if not p or not os.path.exists(p): return f"[FILE NOT FOUND: {p}]"
        
        display_name = get_formatted_path(p, s.get("mode", "Relative Path"), root)
        lang = get_codeblock_language(p)
        content = read_file_content(p)
        
        note = s.get("text", "")
        header = f"File: {display_name}"
        if note: header += f" /* {note} */"
        
        return f"\n{header}\n```{lang}\n{content}\n```\n"
        
    def get_min_height(self): return 100