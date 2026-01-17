import os
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QLabel, QPushButton, 
                             QFileDialog, QSizePolicy)
from PyQt6.QtCore import pyqtSignal
from components.db_manager import DBManager
from components.styles import apply_class

class DBSelector(QWidget):
    # Signal emitted when the database path changes
    db_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        self.lbl_db = QLabel()
        apply_class(self.lbl_db, "text-primary font-bold")
        self.update_label()
        
        # Button
        btn_switch_db = QPushButton("SWITCH DB")
        btn_switch_db.setFixedWidth(100)
        btn_switch_db.clicked.connect(self.change_database)
        
        layout.addWidget(self.lbl_db)
        layout.addStretch()
        layout.addWidget(btn_switch_db)

    def update_label(self):
        path = DBManager.get_db_path()
        name = os.path.basename(path) if path else "None"
        self.lbl_db.setText(f"DATABASE: {name}")

    def change_database(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select Database", "", "SQLite Files (*.db);;All Files (*)"
        )
        if fname:
            DBManager.set_db_path(fname)
            self.update_label()
            self.db_changed.emit(fname)