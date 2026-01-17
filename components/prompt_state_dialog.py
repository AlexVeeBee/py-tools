import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QListWidget, QLabel, QLineEdit, QListWidgetItem,
                             QSplitter, QDialogButtonBox, QMessageBox, QWidget,
                             QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from components.db_manager import DBManager
# --- UPDATED IMPORT ---
from components.prompt import PromptItemWidget
from components.db_selector import DBSelector 
from components.styles import apply_class, C_PRIMARY

class PromptStateDialog(QDialog):
    def __init__(self, parent=None, mode="load", current_name=None):
        super().__init__(parent)
        self.mode = mode
        self.selected_name = None
        
        title = "LOAD PROMPT" if mode == "load" else "SAVE PROMPT"
        self.setWindowTitle(f"{title}")
        self.resize(1000, 700)
        
        # Main Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # --- 1. Header ---
        self.db_selector = DBSelector()
        self.db_selector.db_changed.connect(self.on_db_changed)
        self.db_selector.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.db_selector)

        # --- 2. Central Area ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left: Names List
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0,0,0,0)
        list_layout.addWidget(QLabel("EXISTING PROMPTS:"))
        
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.on_selection_change)
        self.list_widget.itemDoubleClicked.connect(self.handle_double_click)
        list_layout.addWidget(self.list_widget)
        
        # Right: Visual Preview (Using Read-Only Prompt Items)
        preview_container = QWidget()
        prev_layout = QVBoxLayout(preview_container)
        prev_layout.setContentsMargins(0,0,0,0)
        
        lbl_preview = QLabel("VISUAL PREVIEW (READ ONLY):")
        prev_layout.addWidget(lbl_preview)
        
        self.preview_list = QListWidget()
        self.preview_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        prev_layout.addWidget(self.preview_list)

        splitter.addWidget(list_container)
        splitter.addWidget(preview_container)
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

        # --- 3. Footer ---
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(5)
        
        # Save Name Input
        self.ln_name = QLineEdit()
        self.ln_name.setPlaceholderText("ENTER PROMPT NAME...")
        self.ln_name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ln_name.setFixedHeight(30) 

        if current_name:
            self.ln_name.setText(current_name)
            
        if mode == "save":
            lbl_input = QLabel("SAVE AS:")
            apply_class(lbl_input, "text-primary font-bold")
            lbl_input.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            footer_layout.addWidget(lbl_input)
            footer_layout.addWidget(self.ln_name)
        else:
            self.ln_name.hide()

        # Dialog Buttons
        btns = QDialogButtonBox()
        self.btn_action = btns.addButton("LOAD" if mode == "load" else "SAVE", QDialogButtonBox.ButtonRole.AcceptRole)
        self.btn_cancel = btns.addButton(QDialogButtonBox.StandardButton.Cancel)
        
        self.btn_action.setStyleSheet(f"background-color: {C_PRIMARY}; color: #120d03; font-weight: bold;")
        
        btns.accepted.connect(self.validate_and_accept)
        btns.rejected.connect(self.reject)
        
        footer_layout.addWidget(btns)
        layout.addLayout(footer_layout)

        self.refresh_list()

    def on_db_changed(self, new_path):
        """Called when DBSelector changes the database"""
        self.refresh_list()
        self.preview_list.clear()

    def refresh_list(self):
        self.list_widget.clear()
        try:
            prompts = DBManager.get_all_prompts()
            for row in prompts:
                self.list_widget.addItem(f"{row['name']}")
        except Exception as e:
            self.list_widget.addItem(f"Error reading DB")
            print(e)

    def on_selection_change(self):
        item = self.list_widget.currentItem()
        if not item:
            self.preview_list.clear()
            return
            
        name = item.text()
        if name == "Error reading DB": return

        if self.mode == "save":
            self.ln_name.setText(name)
            
        # Load data and populate the preview list
        data = DBManager.load_prompt(name)
        self.populate_preview(data)

    def populate_preview(self, data):
        self.preview_list.clear()
        if not data: return
        
        root_path = data.get("project_root", "")
        items = data.get("items", [])
        
        if root_path:
            lbl = QLabel(f"PROJECT ROOT: {root_path}")
            lbl.setStyleSheet("color: #7c5826; font-style: italic; padding: 5px;")
            item = QListWidgetItem()
            item.setSizeHint(QSize(100, 30))
            self.preview_list.addItem(item)
            self.preview_list.setItemWidget(item, lbl)

        for item_data in items:
            list_item = QListWidgetItem(self.preview_list)
            # Default height is updated dynamically by set_state
            list_item.setSizeHint(QSize(100, 105))
            
            widget = PromptItemWidget(
                parent_item=list_item, 
                list_widget=self.preview_list, 
                root_getter=lambda: root_path,
                read_only=True
            )
            widget.set_state(item_data)
            
            self.preview_list.addItem(list_item)
            self.preview_list.setItemWidget(list_item, widget)

    def handle_double_click(self):
        self.validate_and_accept()

    def validate_and_accept(self):
        if self.mode == "load":
            item = self.list_widget.currentItem()
            if not item or item.text() == "Error reading DB":
                QMessageBox.warning(self, "Selection Required", "Please select a valid prompt to load.")
                return
            self.selected_name = item.text()
            self.accept()

        elif self.mode == "save":
            name = self.ln_name.text().strip()
            if not name:
                QMessageBox.warning(self, "Name Required", "Please enter a name for the prompt.")
                return
            
            existing_items = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
            if name in existing_items:
                reply = QMessageBox.question(
                    self, "Confirm Overwrite", 
                    f"'{name}' already exists.\nOverwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.No:
                    return

            self.selected_name = name
            self.accept()