from PyQt6.QtWidgets import QWidget

# --- RETRO ORANGE PALETTE ---
C_BG_MAIN           = "#120d03"            # --bg
C_BG_SECONDARY      = "#1e1406"            # --sidebar-bg
C_BG_SURFACE        = "#1a1305"            # --header-bg
C_BG_INPUT          = "#261b07"            # --button-bg (used for inputs/list items)
C_BORDER            = "#44320D"            # --border
C_PRIMARY           = "#ff9800"            # --primary
C_SECONDARY         = "#e65100"            # --keyword (Deep Orange)
C_TEXT_MAIN         = "#ffb74d"            # --text
C_TEXT_ACTIVE       = "#ffffff"            # --text-active
C_TEXT_MUTED        = "#7c5826"            # --line-number / comment
C_DANGER            = "#bf360c"            # --error-color
C_SCROLL            = "#ff9800"            # --scroll-thumb
C_CHECKBOX_BG       = "#261b07"            # --checkbox-bg (Matches Input)
C_CHECKBOX_BORDER   = "#7c5826"            # --checkbox-border (Muted Text color for visibility)
C_SUCCESS           = "#388e3c"            # --success-color

# High Contrast Checkmark SVG (Dark Tick on Transparent -> will sit on Orange BG)
# Stroke is #120d03 (C_BG_MAIN) to look like a cutout against the #ff9800 (Orange) background
SVG_CHECKMARK = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAABnSURBVHgBtZHRDYAwCESpcRfGFMdkmgqJmBPR9sdL2gDhHiUl+kOq2v14vEw0b5gPDSaZNiS6+NUGhh4xM7fPCRX9mgAkMdL+RnetCSzWSLmGSYPxQoWQTrHD+YzK8Kjd3PmTYh/UAUGxLEbrn+LDAAAAAElFTkSuQmCC"

# --- COMPACT THEME STYLESHEET ---
MAIN_THEME_DARK = f"""
    /* GLOBAL RESET */
    QWidget {{
        color: {C_TEXT_MAIN};
        background-color: {C_BG_MAIN};
        font-family: 'Consolas', 'Segoe UI', monospace;
        font-size: 13px;
        outline: none;
    }}

    /* MAIN WINDOW */
    QMainWindow {{ background-color: {C_BG_MAIN}; }}

    /* TABS - RETRO COMPACT */
    QTabWidget::pane {{
        border: 1px solid {C_BORDER};
        background: {C_BG_SURFACE};
        top: -1px;
    }}
    
    QTabBar::tab {{
        background: {C_BG_MAIN};
        color: {C_TEXT_MUTED};
        padding: 4px 12px;
        border: 1px solid {C_BORDER};
        border-bottom: none;
        margin-right: 2px;
        border-top-left-radius: 2px;
        border-top-right-radius: 2px;
    }}
    
    QTabBar::tab:selected {{
        background: {C_BG_SURFACE};
        color: {C_PRIMARY};
        border-bottom: 1px solid {C_BG_SURFACE};
        font-weight: bold;
    }}

    QTabBar::tab:hover {{
        color: {C_TEXT_ACTIVE};
        background: {C_BG_INPUT};
    }}

    /* INPUTS & EDITORS */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {C_BG_INPUT};
        border: 1px solid {C_BORDER};
        color: {C_TEXT_MAIN};
        padding: 4px;
        selection-background-color: {C_PRIMARY};
        selection-color: {C_BG_MAIN};
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {C_PRIMARY};
    }}

    /* LIST WIDGETS */
    QListWidget {{
        background-color: {C_BG_MAIN};
        border: 1px solid {C_BORDER};
    }}
    
    QListWidget::item {{
        background: {C_BG_INPUT};
        margin: 2px 4px; 
        padding: 2px;
        border: 1px solid {C_BORDER};
    }}
    
    QListWidget::item:selected {{
        border: 1px solid {C_PRIMARY};
        background: {C_BG_SURFACE};
    }}

    /* --- TABLES & TREES --- */
    QTableView, QTreeWidget, QTreeView {{
        background-color: {C_BG_INPUT};
        alternate-background-color: {C_BG_SURFACE};
        gridline-color: {C_BORDER};
        border: 1px solid {C_BORDER};
        selection-background-color: {C_PRIMARY};
        selection-color: {C_BG_MAIN};
        outline: none;
    }}

    QHeaderView::section {{
        background-color: {C_BG_SURFACE};
        color: {C_TEXT_MAIN};
        padding: 4px;
        border: 1px solid {C_BORDER};
        font-weight: bold;
    }}

    QHeaderView::section:horizontal {{
        border-bottom: 2px solid {C_BORDER};
    }}

    QTableCornerButton::section {{
        background-color: {C_BG_SURFACE};
        border: 1px solid {C_BORDER};
    }}

    /* --- CHECKBOXES, TREE & GROUPBOX INDICATORS --- */
    
    QCheckBox, QTreeView, QGroupBox {{
        spacing: 6px;
        color: {C_TEXT_MAIN};
        background: transparent;
    }}

    /* The box itself (Unchecked) */
    QCheckBox::indicator, QTreeView::indicator, QGroupBox::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {C_CHECKBOX_BORDER};
        background-color: {C_CHECKBOX_BG};
        border-radius: 2px;
    }}

    /* Hover over the box (Unchecked) */
    QCheckBox::indicator:hover, QTreeView::indicator:hover, QGroupBox::indicator:hover {{
        border: 1px solid {C_PRIMARY};
        background-color: {C_BG_INPUT};
    }}

    /* Checked State - Orange background with Dark Tick */
    QCheckBox::indicator:checked, QTreeView::indicator:checked, QGroupBox::indicator:checked {{
        background-color: {C_PRIMARY};
        border: 1px solid {C_PRIMARY};
        image: url(:/images/checkmark.png);
    }}

    /* Checked State Hover - Slightly Darker Orange */
    QCheckBox::indicator:checked:hover, QTreeView::indicator:checked:hover, QGroupBox::indicator:checked:hover {{
        background-color: {C_SECONDARY};
        border: 1px solid {C_SECONDARY};
        image: url(:/images/checkmark.png);
    }}

    /* BUTTONS */
    QPushButton {{
        background-color: {C_BG_INPUT};
        color: {C_TEXT_MAIN};
        border: 1px solid {C_BORDER};
        padding: 4px 12px;
        border-radius: 0px; 
        font-weight: bold;
    }}
    
    QPushButton:hover {{
        border: 1px solid {C_PRIMARY};
        color: {C_PRIMARY};
    }}
    
    QPushButton:pressed {{
        background-color: {C_PRIMARY};
        color: {C_BG_MAIN};
    }}

    /* MENUS */
    QMenuBar {{ background-color: {C_BG_SURFACE}; border-bottom: 1px solid {C_BORDER}; }}
    QMenuBar::item {{ padding: 6px 12px; color: {C_TEXT_MAIN}; }}
    QMenuBar::item:selected {{ background-color: {C_PRIMARY}; color: {C_BG_MAIN}; }}
    
    QMenu {{ background-color: {C_BG_SURFACE}; border: 1px solid {C_BORDER}; }}
    QMenu::item {{ padding: 4px 24px; }}
    QMenu::item:selected {{ background-color: {C_PRIMARY}; color: {C_BG_MAIN}; }}

    /* ITEMS - FIX SHIFTING & ICON SPACE */
    QComboBox {{
        background-color: {C_BG_INPUT};
        border: 1px solid {C_BORDER};
        padding: 2px 5px;
        color: {C_TEXT_MAIN};
    }}

    QComboBox::item {{
        min-height: 16px;
        height: 16px;
        /* Padding: Top/Bottom 4px, Left/Right 10px 
           This overrides the default 'icon slot' space */
        padding: 4px 0px;
        padding-left: -12px; /* Remove extra space for icon */ 
        margin: 0px;
        border: none; /* Removing border prevents jumping on hover */
        color: {C_TEXT_MAIN};
    }}

    /* HOVER STATE */
    QComboBox::item:hover {{
        background-color: {C_PRIMARY};
        color: {C_BG_MAIN};
        border: none; /* Ensure no border here either */
        padding: 4px 0px; /* MUST match normal state exactly */
        padding-left: -12px; /* Remove extra space for icon */ 
    }}

    /* SELECTED STATE (Keyboard/Current) */
    QComboBox::item:selected {{
        background-color: {C_PRIMARY};
        color: {C_BG_MAIN};
        border: none; 
        padding: 4px 0px; /* MUST match normal state exactly */
        padding-left: -12px; /* Remove extra space for icon */ 
    }}

    /* SPLITTER */
    QSplitter::handle {{ background: {C_BORDER}; }}
    QSplitter::handle:horizontal {{ width: 1px; }}
    QSplitter::handle:vertical {{ height: 1px; }}

    /* SCROLLBARS */
    QScrollBar:vertical {{
        border: none;
        background: {C_BG_MAIN};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {C_BORDER};
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {C_SCROLL}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    
    /* UTILS */
    .text-primary {{ color: {C_PRIMARY}; }}
    .text-secondary {{ color: {C_SECONDARY}; }}
    .font-bold {{ font-weight: bold; }}
"""

def apply_class(widget: QWidget, class_names: str):
    widget.setProperty("class", class_names)
    widget.style().unpolish(widget)
    widget.style().polish(widget)