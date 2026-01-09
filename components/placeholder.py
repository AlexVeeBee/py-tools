from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStyle
from PyQt6.QtCore import Qt

class PlaceholderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Large Icon
        icon_label = QLabel()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)
        icon_label.setPixmap(icon.pixmap(128, 128))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Text
        text_label = QLabel("Click the 'Tools' menu at the top left to select a tool.")
        text_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffb74d;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(text_label)