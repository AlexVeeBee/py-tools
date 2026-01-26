from PyQt6.QtWidgets import QPlainTextEdit
from components.plugin_system import BlockPluginInterface
from components.styles import C_TEXT_MAIN

class MessageBlock(BlockPluginInterface):
    @property
    def name(self): return "Message"
    @property
    def id(self): return "core.message"

    def create_ui(self, parent, root_getter, **kwargs):
        # Matches original Text Area style
        widget = QPlainTextEdit(parent)
        widget.setPlaceholderText("// Enter instructions...")
        widget.setStyleSheet(f"color: {C_TEXT_MAIN}; border: none;")
        widget.textChanged.connect(self.dataChanged.emit)
        return widget

    def get_state(self, widget):
        return {"text": widget.toPlainText()}

    def set_state(self, widget, state):
        widget.setPlainText(state.get("text", ""))

    def compile(self, state, root, **kwargs):
        return state.get("text", "") + "\n"