import os
import fnmatch
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                             QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
                             QDialogButtonBox, QMessageBox, QTreeWidgetItemIterator)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from components.styles import C_TEXT_MAIN, C_TEXT_MUTED, C_BG_INPUT, C_BORDER, C_DANGER, C_PRIMARY
from PyQt6.QtGui import QPainter, QColor

class TreeSelectionDialog(QDialog):
    """Popup dialog to select specific files from a tree."""
    def __init__(self, parent, root_path, ignore_str, current_selection):
        super().__init__(parent)
        self.setWindowTitle("Select Context Files")
        self.resize(600, 500)
        self.root_path = root_path
        self.ignores = {x.strip() for x in ignore_str.split(',') if x.strip()}
        self.current_selection = set(current_selection)
        
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel(f"Check files to inject content from:\nRoot: {root_path}")
        lbl_info.setStyleSheet(f"color: {C_TEXT_MUTED}; font-style: italic;")
        layout.addWidget(lbl_info)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Project Files")
        self.tree.setStyleSheet(f"background-color: {C_BG_INPUT}; border: 1px solid {C_BORDER};")
        layout.addWidget(self.tree)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        self.populate_tree()

    def is_ignored(self, name):
        for pattern in self.ignores:
            if fnmatch.fnmatch(name, pattern): return True
        return False

    def populate_tree(self):
        self.tree.clear()
        if not os.path.exists(self.root_path): return

        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, os.path.basename(self.root_path))
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.root_path)
        root_item.setExpanded(True)
        self._add_children(root_item, self.root_path)

    def _add_children(self, parent_item, path):
        try: items = sorted(os.listdir(path))
        except PermissionError: return

        for name in items:
            if name.startswith('.') or self.is_ignored(name): continue

            full_path = os.path.join(path, name)
            item = QTreeWidgetItem(parent_item)
            item.setText(0, name)
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            
            if os.path.isdir(full_path):
                # Set folder icon with custom color
                icon = QIcon.fromTheme("folder")
                pixmap = icon.pixmap(16, 16)
                painter = QPainter(pixmap)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), QColor(C_TEXT_MAIN))
                painter.end()
                item.setIcon(0, QIcon(pixmap))
                self._add_children(item, full_path)
                self._add_children(item, full_path)
            else:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(0, Qt.CheckState.Checked if full_path in self.current_selection else Qt.CheckState.Unchecked)

    def get_selected_files(self):
        selected = []
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.checkState(0) == Qt.CheckState.Checked:
                path = item.data(0, Qt.ItemDataRole.UserRole)
                if path and os.path.isfile(path): selected.append(path)
            iterator += 1
        return selected

class FileInjectHelper(QWidget):
    """
    Manages the UI for selecting additional files to inject into the prompt.
    """
    filesChanged = pyqtSignal()

    def __init__(self, parent=None, path_getter=None, ignore_getter=None):
        super().__init__(parent)
        self.path_getter = path_getter     
        self.ignore_getter = ignore_getter 
        self.selected_files = []
        self.is_read_only = False

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 4, 4)
        layout.setSpacing(10)

        # 1. Open Dialog Button
        self.btn_open = QPushButton(" Select Context Files... ")
        self.btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open.setStyleSheet(f"""
            QPushButton {{
                background-color: {C_BG_INPUT};
                border: 1px solid {C_BORDER};
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {C_PRIMARY}; color: #000; }}
        """)
        self.btn_open.clicked.connect(self.open_dialog)
        layout.addWidget(self.btn_open)

        # 2. Status Label
        self.lbl_status = QLabel("No context files selected")
        self.lbl_status.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11px; font-style: italic;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        # 3. Clear Button
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet(f"color: {C_DANGER}; border: none; font-size: 11px; font-weight: bold;")
        self.btn_clear.clicked.connect(self.clear_files)
        self.btn_clear.setVisible(False)
        layout.addWidget(self.btn_clear)

    def set_read_only(self, val: bool):
        self.is_read_only = val
        self.btn_open.setVisible(not val)
        self.btn_clear.setVisible(False)

    def set_files(self, files):
        self.selected_files = files if files else []
        self.update_ui()

    def get_files(self):
        return self.selected_files

    def update_ui(self):
        count = len(self.selected_files)
        if count == 0:
            self.lbl_status.setText("No context files selected")
            self.btn_clear.setVisible(False)
        else:
            self.lbl_status.setText(f"{count} files selected for injection")
            if not self.is_read_only:
                self.btn_clear.setVisible(True)

    def open_dialog(self):
        if self.is_read_only: return
        
        path = self.path_getter() if self.path_getter else ""
        ignore = self.ignore_getter() if self.ignore_getter else ""

        if not path or not os.path.exists(path) or not os.path.isdir(path):
            QMessageBox.warning(self, "Invalid Path", "Please select a valid folder first.")
            return

        dlg = TreeSelectionDialog(self, path, ignore, self.selected_files)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.selected_files = dlg.get_selected_files()
            self.update_ui()
            self.filesChanged.emit()

    def clear_files(self):
        if self.is_read_only: return
        self.selected_files = []
        self.update_ui()
        self.filesChanged.emit()