from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTextBrowser)
from components.help.viewer import HELP_HTML
from components.styles import C_BG_MAIN, C_TEXT_MAIN, C_PRIMARY, C_BORDER

class HelpViewerTool(QWidget):
    """A simple help viewer displaying static HTML content."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help / Documentation")
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        self.text_browser = QTextBrowser()
        self.text_browser.setStyleSheet(f"background-color: {C_BG_MAIN}; color: {C_TEXT_MAIN}; border: 1px solid {C_BORDER};")
        self.text_browser.setHtml(HELP_HTML)
        
        layout.addWidget(self.text_browser)