from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, 
                             QListWidget, QSplitter, QListWidgetItem)
from PyQt6.QtCore import Qt
from components.styles import C_BG_MAIN, C_TEXT_MAIN, C_BG_SECONDARY, C_BORDER, C_PRIMARY

# Import the data from the new pages file
from .pages import PAGES

class HelpWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter for Navigation (Left) vs Content (Right)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"QSplitter::handle {{ background-color: {C_BORDER}; }}")

        # --- LEFT: Topic List ---
        self.topic_list = QListWidget()
        self.topic_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {C_BG_SECONDARY};
                color: {C_TEXT_MAIN};
                border: none;
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {C_BORDER};
            }}
            QListWidget::item:selected {{
                background-color: {C_PRIMARY};
                color: #120d03;
                font-weight: bold;
            }}
            QListWidget::item:hover:!selected {{
                background-color: #3d3d3d;
            }}
        """)
        self.topic_list.setMaximumWidth(300)
        self.topic_list.currentRowChanged.connect(self.display_page)

        # --- RIGHT: Content Browser ---
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: {C_BG_MAIN};
                border: none;
                padding: 10px;
            }}
        """)

        # Add to Splitter
        splitter.addWidget(self.topic_list)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(1, 4) # Give browser more space

        layout.addWidget(splitter)

        # Initialize Data
        self.pages_data = PAGES
        self.populate_topics()

    def populate_topics(self):
        """Fill the list widget with keys from PAGES."""
        self.topic_list.clear()
        for title in self.pages_data.keys():
            item = QListWidgetItem(title)
            self.topic_list.addItem(item)
        
        # Select first item by default
        if self.topic_list.count() > 0:
            self.topic_list.setCurrentRow(0)

    def display_page(self, row_index):
        """Update browser content based on selection."""
        if row_index < 0: return
        
        topic_key = self.topic_list.item(row_index).text()
        html_content = self.pages_data.get(topic_key, "<h1>Page not found</h1>")
        self.browser.setHtml(html_content)