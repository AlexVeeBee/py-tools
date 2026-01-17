from PyQt6.QtWidgets import QLineEdit
from PyQt6.QtCore import pyqtSignal
from components.styles import C_PRIMARY, C_BG_INPUT
from components.mime_parser import DragAndDropParser

# File extension mapping for Code Blocks
doeblockFileTypes = {
    'txt': 'plaintext', 'md': 'Markdown', 'json': 'JSON', 'yaml': 'YAML', 'yml': 'YAML',
    'csv': 'CSV', 'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript', 'java': 'Java',
    'cpp': 'C++', 'html': 'HTML', 'htm': 'HTML', 'css': 'CSS', 'vue': 'Vue',
}

class DroppableLineEdit(QLineEdit):
    """Line Edit that accepts file drops."""
    fileDropped = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._original_style = ""

    def dragEnterEvent(self, e):
        paths = DragAndDropParser.parse_paths(e.mimeData())
        if paths:
            e.accept()
            self._original_style = self.styleSheet()
            self.setStyleSheet(f"border: 2px dashed {C_PRIMARY}; background-color: {C_BG_INPUT};")
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if DragAndDropParser.parse_paths(e.mimeData()):
            e.accept()
        else:
            super().dragMoveEvent(e)

    def dragLeaveEvent(self, e):
        self.setStyleSheet(self._original_style)
        super().dragLeaveEvent(e)

    def dropEvent(self, e):
        self.setStyleSheet(self._original_style)
        paths = DragAndDropParser.parse_paths(e.mimeData())
        if paths:
            self.fileDropped.emit(paths[0])
        else:
            super().dropEvent(e)