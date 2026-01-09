from PyQt6.QtWidgets import QPlainTextEdit, QLineEdit
from PyQt6.QtCore import pyqtSignal, QMimeData

class RawPlainTextEdit(QPlainTextEdit):
    """A QPlainTextEdit that strips formatting from pasted text."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Enter instructions...")
        # self.setStyleSheet("""
        #     QPlainTextEdit { 
        #         background: #151a23; 
        #         color: #B3B9C5; 
        #         border: 1px solid #333; 
        #         border-radius: 4px;
        #     }
        # """)

    def insertFromMimeData(self, source: QMimeData):
        if source.hasText():
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)

class DroppableLineEdit(QLineEdit):
    """A QLineEdit that accepts file drags and emits the path."""
    fileDropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        # self.default_style = "color: #888; background: #0F131A; border: 1px solid #333;"
        # self.hover_style = "color: #E6B450; background: #1A202C; border: 1px dashed #E6B450;"
        # self.setStyleSheet(self.default_style)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            # self.setStyleSheet(self.hover_style)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        # self.setStyleSheet(self.default_style)
        event.accept()

    def dropEvent(self, event):
        # self.setStyleSheet(self.default_style)
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path:
                self.fileDropped.emit(file_path)