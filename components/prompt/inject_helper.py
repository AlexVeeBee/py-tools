import os
import fnmatch
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                             QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
                             QDialogButtonBox, QMessageBox, QTreeWidgetItemIterator)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPainter, QColor, QPixmap

from components.styles import C_TEXT_MUTED, C_BG_INPUT, C_BORDER, C_DANGER, C_PRIMARY, C_TEXT_MAIN

class TreeSelectionDialog(QDialog):
    """Popup dialog to select specific files from a tree."""
    def __init__(self, parent, root_path, ignore_str, current_selection):
        super().__init__(parent)
        self.setWindowTitle("Select Context Files")
        self.resize(650, 550)
        self.root_path = root_path
        self.ignores = {x.strip() for x in ignore_str.split(',') if x.strip()}
        self.current_selection = set(current_selection)
        
        layout = QVBoxLayout(self)
        
        # Header Info
        lbl_info = QLabel(f"Check files to inject content from:\nRoot: {root_path}")
        lbl_info.setStyleSheet(f"color: {C_TEXT_MUTED}; font-style: italic;")
        layout.addWidget(lbl_info)

        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Project Files")
        self.tree.itemChanged.connect(self.update_status)
        layout.addWidget(self.tree)

        # Bottom Tools & Buttons
        bottom_layout = QHBoxLayout()
        
        btn_all = QPushButton("Select All")
        btn_none = QPushButton("Deselect All")
        
        btn_style = f"""
            QPushButton {{ background: transparent; color: {C_TEXT_MAIN}; border: 1px solid {C_BORDER}; border-radius: 4px; padding: 4px 12px; }}
            QPushButton:hover {{ background: {C_BG_INPUT}; color: {C_PRIMARY}; }}
        """
        btn_all.setStyleSheet(btn_style)
        btn_none.setStyleSheet(btn_style)
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_none.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_all.clicked.connect(lambda: self.set_all_checked(True))
        btn_none.clicked.connect(lambda: self.set_all_checked(False))
        
        self.lbl_status = QLabel("0 / 0 files selected")
        self.lbl_status.setStyleSheet(f"color: {C_PRIMARY}; font-weight: bold;")
        
        bottom_layout.addWidget(btn_all)
        bottom_layout.addWidget(btn_none)
        bottom_layout.addWidget(self.lbl_status)
        bottom_layout.addStretch()

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        bottom_layout.addWidget(btns)
        
        layout.addLayout(bottom_layout)

        # Populate and Initialize status
        self.populate_tree()
        self.update_status()

    def is_ignored(self, name):
        for pattern in self.ignores:
            if fnmatch.fnmatch(name, pattern): return True
        return False

    def populate_tree(self):
        self.tree.blockSignals(True)
        self.tree.clear()
        if not os.path.exists(self.root_path): return

        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, os.path.basename(self.root_path))
        root_item.setData(0, Qt.ItemDataRole.UserRole, self.root_path)
        root_item.setExpanded(True)
        self._add_children(root_item, self.root_path)
        self.tree.blockSignals(False)

    def _add_children(self, parent_item, path):
        try:
            all_items = os.listdir(path)
        except PermissionError:
            return

        dirs, files = [], []

        for name in all_items:
            if name.startswith('.') or self.is_ignored(name):
                continue
            
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                dirs.append((name, full_path))
            else:
                files.append((name, full_path))

        dirs.sort(key=lambda x: x[0].lower())
        files.sort(key=lambda x: x[0].lower())

        for name, full_path in dirs:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, name)
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            
            icon = QIcon.fromTheme("folder")
            if not icon.isNull():
                pixmap = icon.pixmap(16, 16)
                painter = QPainter(pixmap)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), QColor(C_TEXT_MAIN))
                painter.end()
                item.setIcon(0, QIcon(pixmap))
            
            self._add_children(item, full_path)

        for name, full_path in files:
            item = QTreeWidgetItem(parent_item)
            item.setText(0, name)
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            state = Qt.CheckState.Checked if full_path in self.current_selection else Qt.CheckState.Unchecked
            item.setCheckState(0, state)

    def set_all_checked(self, checked):
        self.tree.blockSignals(True)
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(0, state)
            iterator += 1
        self.tree.blockSignals(False)
        self.update_status()

    def update_status(self):
        selected, total = 0, 0
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                total += 1
                if item.checkState(0) == Qt.CheckState.Checked:
                    selected += 1
            iterator += 1
        self.lbl_status.setText(f"{selected} / {total} files selected")

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

        # 2. Status Label (Smart)
        self.lbl_status = QLabel()
        self.lbl_status.setStyleSheet(f"font-size: 11px;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        # 3. Clear Button
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet(f"color: {C_DANGER}; border: none; font-size: 11px; font-weight: bold;")
        self.btn_clear.clicked.connect(self.clear_files)
        self.btn_clear.setVisible(False)
        layout.addWidget(self.btn_clear)
        
        self.update_ui()

    def set_read_only(self, val: bool):
        self.is_read_only = val
        self.btn_open.setVisible(not val)
        self.btn_clear.setVisible(False)

    def set_files(self, files):
        self.selected_files = files if files else []
        self.update_ui()

    def get_files(self):
        return self.selected_files

    def get_total_files(self, path, ignore_str):
        if not path or not os.path.exists(path): return 0
        
        ignores = {x.strip() for x in ignore_str.split(',') if x.strip()}
        
        def is_ignored(name):
            for pattern in ignores:
                if fnmatch.fnmatch(name, pattern): return True
            return False

        total = 0
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and not is_ignored(d)]
            for f in files:
                if not f.startswith('.') and not is_ignored(f):
                    total += 1
        return total

    def update_ui(self):
        path = self.path_getter() if self.path_getter else ""
        ignore = self.ignore_getter() if self.ignore_getter else ""
        
        if not path or not os.path.exists(path):
            self.lbl_status.setText(f"<span style='color: {C_TEXT_MUTED}; font-style: italic;'>Waiting for valid directory...</span>")
            self.btn_clear.setVisible(False)
            return

        # Dynamically calculate totals matching exactly what the dialog would show
        total = self.get_total_files(path, ignore)

        # Clean up files that might have been deleted from disk
        self.selected_files = [f for f in self.selected_files if os.path.exists(f)]
        count = len(self.selected_files)

        if total == 0:
            self.lbl_status.setText(f"<span style='color: {C_TEXT_MUTED}; font-style: italic;'>No selectable files found</span>")
            self.btn_clear.setVisible(False)
        else:
            color = C_PRIMARY if count > 0 else C_TEXT_MUTED
            weight = "bold" if count > 0 else "normal"
            self.lbl_status.setText(f"<span style='color: {color}; font-weight: {weight};'>{count}</span> <span style='color: {C_TEXT_MUTED};'>/ {total} files selected</span>")
            self.btn_clear.setVisible(count > 0 and not self.is_read_only)

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