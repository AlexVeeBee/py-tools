import sys
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableView, 
                             QComboBox, QPushButton, QMessageBox, QHeaderView,
                             QTabWidget, QTextEdit, QLabel, QSplitter)
from PyQt6.QtSql import QSqlDatabase, QSqlTableModel, QSqlQueryModel, QSqlQuery
from PyQt6.QtCore import Qt
from components.db_selector import DBSelector
from components.db_manager import DBManager
from components.styles import apply_class, C_PRIMARY, C_DANGER

class DatabaseEditorTool(QWidget):
    def __init__(self):
        super().__init__()
        # Unique connection name to avoid conflicts if multiple tabs open
        self.db_conn_name = f"editor_connection_{id(self)}"
        self.model = None 
        self.setup_ui()
        self.connect_to_db()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Top: DB Selector ---
        self.db_selector = DBSelector()
        self.db_selector.db_changed.connect(self.on_db_changed)
        layout.addWidget(self.db_selector)

        # --- Tabs for Modes ---
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Table Editor
        self.tab_editor = QWidget()
        self.setup_editor_tab()
        self.tabs.addTab(self.tab_editor, "Table Editor")

        # Tab 2: SQL Query
        self.tab_query = QWidget()
        self.setup_query_tab()
        self.tabs.addTab(self.tab_query, "SQL Query")

    def setup_editor_tab(self):
        layout = QVBoxLayout(self.tab_editor)
        
        # Controls
        h_layout = QHBoxLayout()
        self.combo_tables = QComboBox()
        self.combo_tables.currentTextChanged.connect(self.load_table)
        
        btn_refresh = QPushButton("Refresh Tables")
        btn_refresh.clicked.connect(self.refresh_tables_list)
        
        h_layout.addWidget(QLabel("Table:"))
        h_layout.addWidget(self.combo_tables)
        h_layout.addWidget(btn_refresh)
        h_layout.addStretch()
        
        # Edit Actions
        btn_add = QPushButton("+ Add Row")
        btn_add.clicked.connect(self.add_row)
        
        btn_del = QPushButton("- Delete Row")
        btn_del.clicked.connect(self.delete_row)
        
        # Drop Table Button
        btn_drop = QPushButton("DROP TABLE")
        btn_drop.setStyleSheet(f"background-color: {C_DANGER}; color: #ffffff; font-weight: bold;")
        btn_drop.clicked.connect(self.drop_table)

        h_layout.addWidget(btn_add)
        h_layout.addWidget(btn_del)
        h_layout.addSpacing(20) # Spacer
        h_layout.addWidget(btn_drop)
        
        layout.addLayout(h_layout)

        # Table View
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.setAlternatingRowColors(True)
        layout.addWidget(self.table_view)

    def setup_query_tab(self):
        layout = QVBoxLayout(self.tab_query)
        
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Query Input
        input_container = QWidget()
        l_in = QVBoxLayout(input_container)
        l_in.setContentsMargins(0,0,0,0)
        l_in.addWidget(QLabel("SQL Query:"))
        
        self.txt_query = QTextEdit()
        self.txt_query.setPlaceholderText("SELECT * FROM ...")
        l_in.addWidget(self.txt_query)
        
        btn_exec = QPushButton("Execute")
        btn_exec.setStyleSheet(f"background-color: {C_PRIMARY}; color: black; font-weight: bold;")
        btn_exec.clicked.connect(self.execute_query)
        l_in.addWidget(btn_exec)
        
        splitter.addWidget(input_container)
        
        # Result Output
        output_container = QWidget()
        l_out = QVBoxLayout(output_container)
        l_out.setContentsMargins(0,0,0,0)
        l_out.addWidget(QLabel("Results:"))
        
        self.query_view = QTableView()
        self.query_view.setAlternatingRowColors(True)
        l_out.addWidget(self.query_view)
        
        splitter.addWidget(output_container)
        layout.addWidget(splitter)

    # --- Logic ---

    def connect_to_db(self):
        path = DBManager.get_db_path()
        if not path: return

        if QSqlDatabase.contains(self.db_conn_name):
            db = QSqlDatabase.database(self.db_conn_name)
        else:
            db = QSqlDatabase.addDatabase("QSQLITE", self.db_conn_name)
            
        db.setDatabaseName(path)
        
        if not db.open():
            QMessageBox.critical(self, "Error", f"Could not open database: {db.lastError().text()}")
            return

        self.refresh_tables_list()

    def on_db_changed(self, new_path):
        # Clean up existing models before switching
        self.table_view.setModel(None)
        self.model = None
        
        db = QSqlDatabase.database(self.db_conn_name)
        if db.isOpen():
            db.close()
        
        self.connect_to_db()

    def refresh_tables_list(self):
        current_table = self.combo_tables.currentText()
        self.combo_tables.blockSignals(True)
        self.combo_tables.clear()
        
        db = QSqlDatabase.database(self.db_conn_name)
        if db.isOpen():
            tables = db.tables()
            self.combo_tables.addItems(tables)
        
        # Restore selection if it still exists
        index = self.combo_tables.findText(current_table)
        if index >= 0:
            self.combo_tables.setCurrentIndex(index)
            
        self.combo_tables.blockSignals(False)
        
        # Trigger load if nothing was selected but items exist
        if self.combo_tables.count() > 0 and not current_table:
            self.load_table(self.combo_tables.currentText())

    def load_table(self, table_name):
        if not table_name: 
            self.table_view.setModel(None)
            return
        
        # Create new model
        self.model = QSqlTableModel(self, QSqlDatabase.database(self.db_conn_name))
        self.model.setTable(table_name)
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.model.select()
        
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def add_row(self):
        if self.model:
            self.model.insertRow(self.model.rowCount())

    def delete_row(self):
        if not self.model: return
        
        selection = self.table_view.selectionModel().selectedRows()
        if not selection: return
        
        for index in selection:
            self.model.removeRow(index.row())
        self.model.select()

    def drop_table(self):
        table_name = self.combo_tables.currentText()
        if not table_name: return

        reply = QMessageBox.warning(
            self, 
            "DROP TABLE WARNING", 
            f"Are you sure you want to PERMANENTLY DELETE table '{table_name}'?\n\n"
            "This action cannot be undone and data will be lost.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # We must clear the model referencing the table before dropping it
            self.table_view.setModel(None)
            self.model = None
            
            db = QSqlDatabase.database(self.db_conn_name)
            query = QSqlQuery(db)
            if query.exec(f"DROP TABLE {table_name}"):
                QMessageBox.information(self, "Success", f"Table '{table_name}' dropped.")
                self.refresh_tables_list()
            else:
                QMessageBox.critical(self, "Error", f"Failed to drop table:\n{query.lastError().text()}")
                # Reload previous table view attempt
                self.load_table(table_name)

    def execute_query(self):
        query_str = self.txt_query.toPlainText()
        if not query_str: return
        
        db = QSqlDatabase.database(self.db_conn_name)
        if not db.isOpen(): return

        q_model = QSqlQueryModel()
        q_model.setQuery(query_str, db)
        
        if q_model.lastError().isValid():
            QMessageBox.warning(self, "Query Error", q_model.lastError().text())
        else:
            self.query_view.setModel(q_model)
            self.query_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

    def cleanup(self):
        """
        Manually release resources to ensure the database connection can be removed.
        Called by the main window before closing the tab.
        """
        # 1. Detach models from Views
        self.table_view.setModel(None)
        self.query_view.setModel(None)
        
        # 2. Delete the Python object references to the models
        if hasattr(self, 'model'):
            del self.model
            
        # 3. Close the DB connection
        db = QSqlDatabase.database(self.db_conn_name)
        if db.isOpen():
            db.close()