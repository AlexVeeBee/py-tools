from PyQt6.QtWidgets import QWidget

# --- RETRO ORANGE PALETTE ---
C_BG_MAIN    = "#120d03"            # --bg
C_BG_SURFACE = "#1a1305"            # --header-bg
C_BG_INPUT   = "#261b07"            # --button-bg (used for inputs/list items)
C_BORDER     = "#44320D"            # --border
C_PRIMARY    = "#ff9800"            # --primary
C_SECONDARY  = "#e65100"            # --keyword (Deep Orange)
C_TEXT_MAIN  = "#ffb74d"            # --text
C_TEXT_ACTIVE= "#ffffff"            # --text-active
C_TEXT_MUTED = "#7c5826"            # --line-number / comment
C_DANGER     = "#bf360c"            # --error-color
C_SCROLL     = "#ff9800"            # --scroll-thumb
C_CHECKBOX_BG = "#261b07"           # --checkbox-bg (Matches Input)
C_CHECKBOX_BORDER = "#7c5826"       # --checkbox-border (Muted Text color for visibility)
C_SUCCESS    = "#388e3c"            # --success-color

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

    /* --- CHECKBOXES (FIXED) --- */
    
    QCheckBox {{
        spacing: 6px;
        color: {C_TEXT_MAIN};
        background: transparent; /* Fixes blocky background on label */
    }}

    /* Style the actual box (indicator) for Checkboxes AND TreeViews */
    QCheckBox::indicator, QTreeView::indicator {{
        width: 14px;
        height: 14px;
        border: 1px solid {C_CHECKBOX_BORDER}; /* Muted orange border */
        background-color: {C_BG_MAIN};         /* Dark background for contrast */
        border-radius: 2px;
    }}

    /* Hover State */
    QCheckBox::indicator:hover, QTreeView::indicator:hover {{
        border: 1px solid {C_PRIMARY};
        background-color: {C_BG_SURFACE};
    }}

    /* Checked State - Solid Orange Box */
    QCheckBox::indicator:checked, QTreeView::indicator:checked {{
        border: 1px solid {C_PRIMARY};
        background-color: {C_PRIMARY}; /* Bright orange fill */
        image: none;
    }}
    
    /* Indeterminate State (if used) */
    QCheckBox::indicator:indeterminate, QTreeView::indicator:indeterminate {{
        border: 1px solid {C_PRIMARY};
        background-color: {C_TEXT_MUTED};
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

    /* COMBO BOX */
    QComboBox {{
        background-color: {C_BG_INPUT};
        border: 1px solid {C_BORDER};
        padding: 2px 5px;
        color: {C_TEXT_MAIN};
    }}

    QComboBox QAbstractItemView {{
        background-color: {C_BG_SURFACE};
        border: 1px solid {C_BORDER};
        selection-background-color: {C_PRIMARY};
        selection-color: {C_BG_MAIN};
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