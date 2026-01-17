from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QSizePolicy, QScrollArea, QLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QPoint
from PyQt6.QtGui import QIcon, QPainter, QColor

from components.styles import (C_PRIMARY, C_BG_INPUT, C_BG_SURFACE, 
                               C_BORDER, C_TEXT_MAIN, C_TEXT_MUTED, C_BG_MAIN)

# --- 1. Custom Flow Layout ---
class FlowLayout(QLayout):
    """Standard Qt Flow Layout: wraps items to next row when width runs out."""
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self._do_layout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        m = self.contentsMargins()
        size += QSize(m.left() + m.right(), m.top() + m.bottom())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self.itemList:
            wid = item.widget()
            space_x = spacing + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Horizontal)
            space_y = spacing + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Vertical)
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()

# --- 2. Tool Card Widget ---
class ToolCard(QFrame):
    clicked = pyqtSignal()

    def __init__(self, title, description, icon_name, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(280, 160)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {C_BG_INPUT};
                border: 1px solid {C_BORDER};
                border-radius: 4px;
            }}
            QFrame:hover {{
                border: 1px solid {C_PRIMARY};
                background-color: {C_BG_SURFACE};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(20, 20, 20, 20)

        self.lbl_icon = QLabel()
        icon = QIcon.fromTheme(icon_name)
        if not icon.isNull():
            pixmap = icon.pixmap(32, 32)
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), QColor(C_PRIMARY))
            painter.end()
            self.lbl_icon.setPixmap(pixmap)
        else:
            self.lbl_icon.setText("[*]") 
            self.lbl_icon.setStyleSheet(f"color: {C_PRIMARY}; font-size: 28px; font-weight: bold;")
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"color: {C_PRIMARY}; font-size: 16px; font-weight: bold; font-family: 'Consolas';")
        
        self.lbl_desc = QLabel(description)
        self.lbl_desc.setWordWrap(True)
        self.lbl_desc.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 12px;")
        self.lbl_desc.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(self.lbl_icon)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_desc)
        layout.addStretch()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

# --- 3. Main Dashboard Widget ---
class PlaceholderWidget(QWidget):
    toolRequested = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"background-color: {C_BG_MAIN}; border: none;")
        scroll.setMinimumSize(0, 0)
        scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        self.container = QWidget()
        self.container.setStyleSheet(f"background-color: {C_BG_MAIN};")
        
        content_layout = QVBoxLayout(self.container)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
        content_layout.setSpacing(40)
        content_layout.setContentsMargins(20, 40, 20, 40)

        # Hero
        hero_widget = QWidget()
        hero_layout = QVBoxLayout(hero_widget)
        hero_layout.setSpacing(10)
        
        lbl_title = QLabel("PROMPT BUILDER")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(f"font-size: 42px; font-weight: 900; color: {C_PRIMARY}; letter-spacing: 4px;")
        
        lbl_subtitle = QLabel("AI CONTEXT COMPOSER & DATABASE MANAGER")
        lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_subtitle.setStyleSheet(f"font-size: 14px; color: {C_TEXT_MAIN}; letter-spacing: 2px;")

        hero_layout.addWidget(lbl_title)
        hero_layout.addWidget(lbl_subtitle)
        content_layout.addWidget(hero_widget)

        # Cards
        cards_container = QWidget()
        
        self.flow_layout = FlowLayout(cards_container, margin=0, spacing=20)
        
        card_prompt = ToolCard("Prompt Builder", "Compose complex prompts using modular blocks, file injection, and tree structures.", "document-edit")
        card_prompt.clicked.connect(lambda: self.toolRequested.emit("prompt"))
        
        card_db = ToolCard("Database Editor", "Manage your saved prompts, inspect raw JSON data, and organize your library.", "drive-harddisk")
        card_db.clicked.connect(lambda: self.toolRequested.emit("db"))
        
        card_help = ToolCard("Help / Documentation", "Access help and documentation for using the application.", "help-browser")
        card_help.clicked.connect(lambda: self.toolRequested.emit("help"))

        self.flow_layout.addWidget(card_prompt)
        self.flow_layout.addWidget(card_db)
        self.flow_layout.addWidget(card_help)
        # FIX: Use Preferred. 'Expanding' kept height locked after wrapping/unwrapping.
        cards_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        
        wrapper_h = QHBoxLayout()
        wrapper_h.addStretch()
        wrapper_h.addWidget(cards_container)
        wrapper_h.addStretch()
        
        content_layout.addLayout(wrapper_h)

        # Footer
        content_layout.addStretch() # Push footer down if extra space
        
        lbl_footer = QLabel("SYSTEM STATUS: ONLINE  |  V1.0.0")
        lbl_footer.setStyleSheet(f"color: {C_TEXT_MUTED}; font-size: 11px;")
        lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_footer.setFixedHeight(20)
        
        content_layout.addWidget(lbl_footer)

        scroll.setWidget(self.container)
        main_layout.addWidget(scroll)

    def resizeEvent(self, event):
        width = event.size().width()
        card_slot_width = 300 
        
        if width > card_slot_width * 3 + 100:
            target_width = card_slot_width * 3
        elif width > card_slot_width * 2 + 80:
            target_width = card_slot_width * 2
        else:
            target_width = card_slot_width * 1
            
        wrapper_layout = self.container.layout().itemAt(1)
        if wrapper_layout:
            widget_item = wrapper_layout.itemAt(1)
            if widget_item and widget_item.widget():
                widget_item.widget().setFixedWidth(int(target_width))
        
        super().resizeEvent(event)