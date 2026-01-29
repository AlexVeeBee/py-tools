import os
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QComboBox, QPlainTextEdit, QPushButton, QLineEdit
from components.plugin_system import BlockPluginInterface
from components.prompt.common import DroppableLineEdit
from components.prompt.inject_helper import FileInjectHelper
from components.styles import C_TEXT_MAIN

from components.prompt.generator import (
    get_formatted_path, 
    generate_tree_text, 
    read_file_content, 
    get_codeblock_language
)

class TreeBlock(BlockPluginInterface):
    @property
    def name(self): return "Folder Tree"
    @property
    def id(self): return "core.tree"
    @property
    def drag_types(self): return ["folder"]

    # --- FIX: Add **kwargs here ---
    def create_ui(self, parent, root_getter, **kwargs):
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # 1. Config
        col_cfg = QVBoxLayout()
        col_cfg.setContentsMargins(0,0,0,0)
        self.cb_mode = QComboBox()
        self.cb_mode.addItems(["Relative Path", "Full Path"])
        self.cb_mode.currentIndexChanged.connect(lambda: self._update_display(container, root_getter))
        self.cb_mode.currentIndexChanged.connect(self.dataChanged.emit)
        col_cfg.addWidget(self.cb_mode)
        col_cfg.addStretch()
        
        w_cfg = QWidget()
        w_cfg.setFixedWidth(140)
        w_cfg.setLayout(col_cfg)
        layout.addWidget(w_cfg)

        # 2. Text
        self.txt_prompt = QPlainTextEdit()
        self.txt_prompt.setPlaceholderText("// Context for tree...")
        self.txt_prompt.setStyleSheet(f"color: {C_TEXT_MAIN};")
        self.txt_prompt.textChanged.connect(self.dataChanged.emit)
        layout.addWidget(self.txt_prompt, stretch=3)

        # 3. Path & Helpers
        col_path = QVBoxLayout()
        col_path.setContentsMargins(0,0,0,0)
        row_p = QHBoxLayout()
        self.ln_path = DroppableLineEdit()
        self.ln_path.setReadOnly(True)
        self.ln_path.fileDropped.connect(lambda p: self._handle_drop(container, p, root_getter))
        btn = QPushButton("...")
        btn.setFixedWidth(30)
        btn.clicked.connect(lambda: self._browse(container, root_getter))
        row_p.addWidget(self.ln_path)
        row_p.addWidget(btn)
        
        self.ln_ignore = QLineEdit(".git, __pycache__, node_modules")
        self.ln_ignore.setPlaceholderText("Ignore patterns...")
        self.ln_ignore.textChanged.connect(self.dataChanged.emit)

        self.helper = FileInjectHelper(
            container, 
            path_getter=lambda: container.refs["target_path"],
            ignore_getter=lambda: container.refs["ignore"].text()
        )
        self.helper.filesChanged.connect(self.dataChanged.emit)

        col_path.addLayout(row_p)
        col_path.addWidget(self.ln_ignore)
        col_path.addWidget(self.helper)
        col_path.addStretch()

        w_path = QWidget()
        w_path.setLayout(col_path)
        layout.addWidget(w_path, stretch=4)

        container.refs = {
            "mode": self.cb_mode,
            "text": self.txt_prompt,
            "path_display": self.ln_path,
            "ignore": self.ln_ignore,
            "helper": self.helper,
            "target_path": ""
        }
        
        # Capture optional tag callback
        container.set_tag_cb = kwargs.get("update_tag", None)
        
        return container

    def _handle_drop(self, c, p, rg):
        if os.path.isdir(p):
            c.refs["target_path"] = p
            self._update_display(c, rg)
            self.dataChanged.emit()

    def _browse(self, c, rg):
        from PyQt6.QtWidgets import QFileDialog
        d = QFileDialog.getExistingDirectory(c)
        if d: self._handle_drop(c, d, rg)

    def _get_root_path(self, rg):
        root = rg()
        if root and os.path.isdir(root):
            return root
        return os.path.expanduser("~")

    def _update_display(self, c, rg):
        p = c.refs["target_path"]
        m = c.refs["mode"].currentText()
        txt = get_formatted_path(p, m, self._get_root_path(rg))
        c.refs["path_display"].setText(txt)
        
        if hasattr(c, "set_tag_cb") and c.set_tag_cb:
            c.set_tag_cb("TREE" if p else "")

    def get_state(self, w):
        return {
            "path": w.refs["target_path"],
            "mode": w.refs["mode"].currentText(),
            "text": w.refs["text"].toPlainText(),
            "ignore": w.refs["ignore"].text(),
            "inject": w.refs["helper"].get_files()
        }

    def set_state(self, w, s):
        w.refs["target_path"] = s.get("path", "")
        w.refs["mode"].setCurrentText(s.get("mode", "Relative Path"))
        w.refs["text"].setPlainText(s.get("text", ""))
        w.refs["ignore"].setText(s.get("ignore", ""))
        w.refs["helper"].set_files(s.get("inject", []))
        w.refs["path_display"].setText(s.get("path", ""))
        self._update_display(w, lambda: os.path.expanduser("~"))

    def compile(self, s, root, **kwargs):
        p = s.get("path", "")
        if not p: return "[NO TREE PATH]"
        
        display_name = get_formatted_path(p, s.get("mode", "Relative Path"), root)
        
        local_ign = s.get("ignore", "")
        global_ign = kwargs.get("global_ignore", "")
        combined_ignore = f"{global_ign}, {local_ign}"

        # 1. Tree
        tree = generate_tree_text(p, combined_ignore)
        note = s.get("text", "")
        header = f"Dir: {display_name}"
        if note: header += f" /* {note} */"
        
        out = f"\n{header}\n```\n{tree}\n```\n"

        # 2. Injected Files
        injected = s.get("inject", [])
        if injected:
            out += "\n# --- Context Files for Tree ---\n"
            for rel_path in injected:
                full_path = os.path.join(p, rel_path)
                if os.path.exists(full_path):
                    f_disp = get_formatted_path(full_path, s.get("mode", "Relative Path"), root)
                    lang = get_codeblock_language(full_path)
                    content = read_file_content(full_path)
                    out += f"File: {f_disp}\n```{lang}\n{content}\n```\n"
        return out
    
    def get_min_height(self): return 180