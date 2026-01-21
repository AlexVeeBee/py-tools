import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QCheckBox, 
                             QLineEdit, QDialogButtonBox, QWidget, QHBoxLayout, 
                             QPushButton, QFileDialog, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from components.styles import (C_BG_MAIN, C_PRIMARY, C_BORDER, C_TEXT_MAIN, 
                               C_BG_INPUT, C_TEXT_MUTED, C_BG_SECONDARY)

class ProjectSettingsDialog(QDialog):
    def __init__(self, parent=None, settings_data=None):
        super().__init__(parent)
        self.setWindowTitle("Project Settings")
        
        # --- GLOBAL DIALOG STYLESHEET ---
        # Matches the Prompt Builder tool's aesthetic
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {C_BG_MAIN};
                color: {C_TEXT_MAIN};
            }}
            QLabel {{
                color: {C_TEXT_MAIN};
                font-size: 13px;
            }}
            /* Headings */
            QLabel[cssClass="header"] {{
                color: {C_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
            QLabel[cssClass="sub_header"] {{
                font-weight: bold;
                font-size: 13px;
                margin-top: 10px;
            }}
            QLabel[cssClass="help"] {{
                color: {C_TEXT_MUTED};
                font-size: 11px;
                font-style: italic;
            }}
            
            /* Inputs */
            QLineEdit {{
                background-color: {C_BG_INPUT};
                border: 1px solid {C_BORDER};
                color: {C_TEXT_MAIN};
                padding: 8px;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
            }}
            QLineEdit:focus {{
                border: 1px solid {C_PRIMARY};
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {C_BG_INPUT};
                color: {C_TEXT_MAIN};
                border: 1px solid {C_BORDER};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {C_BG_SECONDARY};
                border-color: {C_TEXT_MAIN};
            }}
            QPushButton:pressed {{
                background-color: {C_PRIMARY};
                color: {C_BG_MAIN};
            }}
        """)

        self.settings = settings_data or {}
        
        # --- LAYOUT ---
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(12, 12, 12, 12)

        # 1. Header
        header_layout = QVBoxLayout()
        header_layout.setSpacing(5)
        
        lbl_title = QLabel("CONFIGURATION")
        lbl_title.setProperty("cssClass", "header")
        
        lbl_desc = QLabel("Global settings for prompt generation and file structure injection.")
        lbl_desc.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12px;")
        
        header_layout.addWidget(lbl_title)
        header_layout.addWidget(lbl_desc)
        self.main_layout.addLayout(header_layout)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {C_BORDER}; max-height: 1px; border: none;")
        self.main_layout.addWidget(line)

        # 2. Directory Tree Config
        group_tree = QWidget()
        layout_tree = QVBoxLayout(group_tree)
        layout_tree.setContentsMargins(0,0,0,0)
        layout_tree.setSpacing(10)

        lbl_tree_head = QLabel("PROJECT STRUCTURE")
        lbl_tree_head.setProperty("cssClass", "sub_header")
        layout_tree.addWidget(lbl_tree_head)

        self.chk_include_tree = QCheckBox("Prepend Project Directory Tree")
        self.chk_include_tree.setChecked(self.settings.get("include_tree", False))
        layout_tree.addWidget(self.chk_include_tree)
        
        help_tree = QLabel("Adds a visual tree of your project files at the very top of the generated prompt.")
        help_tree.setProperty("cssClass", "help")
        layout_tree.addWidget(help_tree)

        self.main_layout.addWidget(group_tree)

        # 3. Exclude Patterns
        group_ignore = QWidget()
        layout_ignore = QVBoxLayout(group_ignore)
        layout_ignore.setContentsMargins(0,0,0,0)
        layout_ignore.setSpacing(10)

        lbl_ignore_head = QLabel("GLOBAL EXCLUDE PATTERNS")
        lbl_ignore_head.setProperty("cssClass", "sub_header")
        layout_ignore.addWidget(lbl_ignore_head)

        # Input Row
        row_input = QHBoxLayout()
        row_input.setSpacing(10)

        self.ln_exclude = QLineEdit()
        self.ln_exclude.setPlaceholderText(".git, __pycache__, node_modules, .venv")
        default_ignore = ".git, __pycache__, node_modules, .idea, .vscode, .venv, dist, build, .DS_Store"
        self.ln_exclude.setText(self.settings.get("global_ignore", default_ignore))
        
        btn_import_git = QPushButton("IMPORT .GITIGNORE")
        btn_import_git.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_import_git.setToolTip("Parse a .gitignore file and add patterns to the list")
        btn_import_git.clicked.connect(self.import_gitignore)
        
        row_input.addWidget(self.ln_exclude)
        row_input.addWidget(btn_import_git)
        layout_ignore.addLayout(row_input)

        lbl_help = QLabel("Comma-separated list of folders/files to exclude from the structure tree.")
        lbl_help.setProperty("cssClass", "help")
        layout_ignore.addWidget(lbl_help)

        self.main_layout.addWidget(group_ignore)

        # Spacer to push buttons to bottom
        self.main_layout.addStretch()

        # 4. Buttons (Footer)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_save = QPushButton("SAVE SETTINGS")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.clicked.connect(self.accept)
        # Apply specific Primary style to Save button
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_PRIMARY};
                color: {C_BG_MAIN};
                border: none;
            }}
        """)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_cancel)
        buttons_layout.addWidget(self.btn_save)
        
        self.main_layout.addLayout(buttons_layout)

    def import_gitignore(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select .gitignore file", "", "Git Ignore (.gitignore);;All Files (*)")
        if fname:
            try:
                new_patterns = []
                with open(fname, 'r', encoding='utf-8') as f:
                    for line in f:
                        l = line.strip()
                        if not l or l.startswith('#'): continue
                        clean = l.strip('/')
                        if clean: new_patterns.append(clean)
                
                if not new_patterns:
                    QMessageBox.information(self, "Info", "No valid patterns found in file.")
                    return

                # Merge unique
                current_text = self.ln_exclude.text()
                current_list = [x.strip() for x in current_text.split(',') if x.strip()]
                combined = current_list + [p for p in new_patterns if p not in current_list]
                
                self.ln_exclude.setText(", ".join(combined))
                QMessageBox.information(self, "Success", f"Imported {len(new_patterns)} patterns.")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to read file:\n{str(e)}")

    def get_settings(self):
        return {
            "include_tree": self.chk_include_tree.isChecked(),
            "global_ignore": self.ln_exclude.text().strip()
        }