import traceback
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                             QWidget, QHBoxLayout, QStyle, QMenu, QLabel, QMessageBox)
from PyQt6.QtGui import QAction, QKeySequence, QCloseEvent
from PyQt6.QtCore import Qt

# Components
from components.styles import MAIN_THEME_DARK
from components.placeholder import PlaceholderWidget
from components.db_manager import DBManager
from tools.prompt_builder import PromptComposerTool

class AppShell(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PROMPT BUILDER")
        self.resize(1200, 800)
        
        # Initialize DB
        try:
            DBManager.init_db()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to initialize database:\n{str(e)}")

        # Status Bar
        self.status_label = QLabel("SYSTEM READY.")
        self.statusBar().addWidget(self.status_label)

        # --- MENU ---
        menubar = self.menuBar()
        file_menu = menubar.addMenu("FILE")
        
        save_action = QAction("Save Tab", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.trigger_save)
        file_menu.addAction(save_action)

        load_action = QAction("Load to Tab", self)
        load_action.setShortcut(QKeySequence.StandardKey.Open)
        load_action.triggered.connect(self.trigger_load)
        file_menu.addAction(load_action)

        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        tools_menu = menubar.addMenu("TOOLS")
        act_prompts = QAction("Prompt Builder", self)
        # We use a wrapper to catch errors during tool instantiation
        act_prompts.triggered.connect(lambda: self.safe_launch_tool(PromptComposerTool, "PROMPT BUILDER"))
        tools_menu.addAction(act_prompts)

        # --- CENTRAL ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        layout.addWidget(self.tabs)
        
        self.add_home_tab()

    def safe_launch_tool(self, tool_class, title):
        """
        Safely instantiates a tool widget and adds it to a tab.
        Catches errors during the __init__ of the tool.
        """
        try:
            widget = tool_class()
            self.add_tab(widget, title)
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Launch Error", f"Failed to launch {title}:\n{str(e)}")

    def add_tab(self, widget, title):
        try:
            index = self.tabs.addTab(widget, title)
            self.tabs.setCurrentIndex(index)
            
            # Connect signals if they exist
            if hasattr(widget, 'statusMessage'):
                widget.statusMessage.connect(self.status_label.setText)
            if hasattr(widget, 'modificationChanged'):
                widget.modificationChanged.connect(lambda s, w=widget: self.update_tab_title(w, s))
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Tab Error", f"Failed to add tab:\n{str(e)}")
            # Attempt to clean up widget if adding failed
            if widget:
                widget.deleteLater()

    def update_tab_title(self, widget, is_modified):
        try:
            index = self.tabs.indexOf(widget)
            if index == -1: return
            txt = self.tabs.tabText(index).replace(" *", "")
            self.tabs.setTabText(index, f"{txt} *" if is_modified else txt)
        except Exception:
            pass # benign error, mostly UI glitch

    def trigger_save(self):
        try:
            current_widget = self.tabs.currentWidget()
            if not current_widget: return
            
            if hasattr(current_widget, 'save_content'):
                current_widget.save_content()
            else:
                self.status_label.setText("This tab cannot be saved.")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Save Error", f"An error occurred while saving:\n{str(e)}")

    def trigger_load(self):
        try:
            current_widget = self.tabs.currentWidget()
            if not current_widget: return

            if hasattr(current_widget, 'load_content'):
                current_widget.load_content()
            else:
                self.status_label.setText("This tab cannot load data.")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Load Error", f"An error occurred while loading:\n{str(e)}")

    def add_home_tab(self):
        try:
            self.add_tab(PlaceholderWidget(), "HOME")
        except Exception:
            pass

    def close_tab(self, index):
        try:
            widget = self.tabs.widget(index)
            if not widget: return

            # Check for unsaved changes before closing
            if hasattr(widget, 'handle_unsaved_changes'):
                if not widget.handle_unsaved_changes():
                    return # User cancelled

            self.tabs.removeTab(index)
            widget.deleteLater()
            
            # If all tabs closed, show home
            if self.tabs.count() == 0:
                self.add_home_tab()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Close Error", f"An error occurred while closing the tab:\n{str(e)}")

    def closeEvent(self, event: QCloseEvent):
        """Intercepts app closing to check all tabs."""
        try:
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                # Switch to the tab being checked so user sees it
                self.tabs.setCurrentIndex(i)
                
                if hasattr(widget, 'handle_unsaved_changes'):
                    if not widget.handle_unsaved_changes():
                        event.ignore()
                        return
            
            event.accept()
        except Exception as e:
            traceback.print_exc()
            # In a close event, if something crashes, we usually want to force close
            # to prevent the app from getting stuck open.
            reply = QMessageBox.question(self, "Error on Exit", 
                                         f"An error occurred while closing:\n{str(e)}\n\nForce close?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        app.setStyle("Fusion") 
        app.setStyleSheet(MAIN_THEME_DARK)
        window = AppShell()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        traceback.print_exc()
        print("CRITICAL LAUNCH ERROR:", str(e))