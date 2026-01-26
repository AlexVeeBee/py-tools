from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit
from components.plugin_system import BlockPluginInterface
from components.styles import C_TEXT_MAIN

class HelloWorldBlock(BlockPluginInterface):
    @property
    def name(self): 
        return "Hello World"

    @property
    def id(self): 
        return "core.hello_world"

    # @property
    # def drag_types(self):
    #     return ['file', 'folder']

    def create_ui(self, parent, root_getter, **kwargs):
        # 1. Create Container
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 2. Add a Label
        lbl = QLabel("👋 Who do you want to greet?")
        lbl.setStyleSheet(f"color: {C_TEXT_MAIN}; font-weight: bold;")
        layout.addWidget(lbl)

        # 3. Add Input Field
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("World")
        # Important: Connect changes to self.dataChanged so the app knows to save
        self.input_field.textChanged.connect(self.dataChanged.emit) 
        layout.addWidget(self.input_field)

        # 4. Store references on the container so get/set_state can access them
        container.refs = {
            "input": self.input_field
        }
        
        return container

    def get_state(self, widget):
        # Save the text from the input field
        return {"who": widget.refs["input"].text()}

    def set_state(self, widget, state):
        # Restore the text to the input field
        widget.refs["input"].setText(state.get("who", ""))

    def compile(self, state, root, **kwargs):
        # Generate the final string for the LLM
        who = state.get("who", "World")
        if not who: 
            who = "World"
        return f"Hello, {who}!\n"

    def get_min_height(self):
        return 120