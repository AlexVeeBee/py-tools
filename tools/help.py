from PyQt6.QtWidgets import QWidget, QVBoxLayout
from components.help.viewer import HelpWidget
from components.styles import C_BG_MAIN

class HelpViewerTool(QWidget):
    """
    The standalone window container for the Help System.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Prompt Builder Guide")
        self.resize(900, 650)
        self.setStyleSheet(f"background-color: {C_BG_MAIN};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.viewer = HelpWidget()
        layout.addWidget(self.viewer)