import traceback
import sys
# Note: specific tools are imported later or lazily to allow dependency checking
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                             QWidget, QHBoxLayout, QStyle, QMenu, QLabel, QMessageBox)
from PyQt6.QtGui import QAction, QKeySequence, QCloseEvent
from PyQt6.QtCore import Qt

# Components
from components.styles import MAIN_THEME_DARK
from components.placeholder import PlaceholderWidget
from components.db_manager import DBManager
from components.dep_checker import DependencyChecker 

# Tools (Standard)
from tools.prompt_builder import PromptComposerTool
from tools.db_editor import DatabaseEditorTool
from tools.help import HelpViewerTool

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
        
        # Prompt Builder Tool
        act_prompts = QAction("Prompt Builder", self)
        act_prompts.triggered.connect(lambda: self.safe_launch_tool(PromptComposerTool, "PROMPT BUILDER"))
        tools_menu.addAction(act_prompts)

        # DB Editor Tool
        act_db = QAction("Database Editor", self)
        act_db.triggered.connect(lambda: self.safe_launch_tool(DatabaseEditorTool, "DB EDITOR"))
        tools_menu.addAction(act_db)

        tools_menu.addSeparator()

        act_other_menu = tools_menu.addMenu("Other Tools")

        # Audio Viz Tool
        act_viz = QAction("Audio Visualizer", self)
        # We connect to a specific method instead of a lambda with the class directly
        act_viz.triggered.connect(self.launch_audio_viz) 
        act_other_menu.addAction(act_viz)

        tools_menu.addSeparator()
        help_action = QAction("Help / Documentation", self)
        help_action.triggered.connect(lambda: self.safe_launch_tool(HelpViewerTool, "HELP"))
        tools_menu.addAction(help_action)

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

    def launch_audio_viz(self):
        """
        Lazy load the Audio Tool. 
        This ensures main.py doesn't crash on startup if libraries are missing.
        """
        try:
            # Import here so it happens AFTER the Dependency Check in main
            from tools.audio_viz import AudioVisualizerTool 
            self.safe_launch_tool(AudioVisualizerTool, "AUDIO VIZ")
        except ImportError as e:
            QMessageBox.critical(self, "Dependency Missing", 
                                 f"Could not load Audio Visualizer.\n\n"
                                 f"Please ensure you have installed requirements:\n{str(e)}")
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Error", str(e))

    def safe_launch_tool(self, tool_class, title):
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
            
            if hasattr(widget, 'statusMessage'):
                widget.statusMessage.connect(self.status_label.setText)
            if hasattr(widget, 'modificationChanged'):
                widget.modificationChanged.connect(lambda s, w=widget: self.update_tab_title(w, s))
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Tab Error", f"Failed to add tab:\n{str(e)}")
            if widget:
                widget.deleteLater()

    def update_tab_title(self, widget, is_modified):
        try:
            index = self.tabs.indexOf(widget)
            if index == -1: return
            txt = self.tabs.tabText(index).replace(" *", "")
            self.tabs.setTabText(index, f"{txt} *" if is_modified else txt)
        except Exception:
            pass 

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
            home_widget = PlaceholderWidget()
            # Connect the signal from the dashboard to the handler
            home_widget.toolRequested.connect(self.handle_home_request)
            self.add_tab(home_widget, "HOME")
        except Exception:
            traceback.print_exc()

    def handle_home_request(self, tool_key):
        """Handles button clicks from the Home Dashboard"""
        if tool_key == "prompt":
            self.safe_launch_tool(PromptComposerTool, "PROMPT BUILDER")
        elif tool_key == "db":
            self.safe_launch_tool(DatabaseEditorTool, "DB EDITOR")
        elif tool_key == "help":
            self.safe_launch_tool(HelpViewerTool, "HELP")

    def close_tab(self, index): 
        try:
            widget = self.tabs.widget(index)
            if not widget: return

            if hasattr(widget, 'handle_unsaved_changes'):
                if not widget.handle_unsaved_changes():
                    return 

            conn_name_to_remove = None
            if hasattr(widget, 'cleanup'):
                widget.cleanup()
                if hasattr(widget, 'db_conn_name'):
                    conn_name_to_remove = widget.db_conn_name

            self.tabs.removeTab(index)
            widget.deleteLater()
            
            if conn_name_to_remove:
                from PyQt6.QtSql import QSqlDatabase
                QSqlDatabase.removeDatabase(conn_name_to_remove)

            if self.tabs.count() == 0:
                self.add_home_tab()
        except Exception as e:
            traceback.print_exc()
            QMessageBox.critical(self, "Close Error", f"An error occurred while closing the tab:\n{str(e)}")

    def closeEvent(self, event: QCloseEvent):
        try:
            for i in range(self.tabs.count()):
                widget = self.tabs.widget(i)
                self.tabs.setCurrentIndex(i)
                
                if hasattr(widget, 'handle_unsaved_changes'):
                    if not widget.handle_unsaved_changes():
                        event.ignore()
                        return
            event.accept()
        except Exception as e:
            traceback.print_exc()
            reply = QMessageBox.question(self, "Error on Exit", 
                                         f"An error occurred while closing:\n{str(e)}\n\nForce close?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                event.accept()
            else:
                event.ignore()

if __name__ == "__main__":
    try:
        # 1. Initialize Application
        app = QApplication(sys.argv)
        app.setStyle("Fusion") 
        app.setStyleSheet(MAIN_THEME_DARK)

        # 2. Check Dependencies 
        # LOGIC CHANGE: We skip the check if we detect we are running in Pixi
        # Pixi sets the 'PIXI_PROJECT_MANIFEST' environment variable.
        import os
        if "PIXI_PROJECT_MANIFEST" not in os.environ:
            try:
                DependencyChecker.check(None, "requirements.txt")
            except Exception:
                pass
        else:
            print("Running in Pixi environment: Dependency check skipped.")

        # 3. Launch Window
        window = AppShell()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        traceback.print_exc()
        print("CRITICAL LAUNCH ERROR:", str(e))