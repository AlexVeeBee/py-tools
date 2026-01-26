from components.plugin_system import PluginManager

# Import existing blocks
from .message import MessageBlock
from .file import FileBlock
from .tree import TreeBlock

# Import the new block
from .hello_world import HelloWorldBlock

def register_core_plugins():
    pm = PluginManager()
    
    # Register existing
    pm.register(MessageBlock)
    pm.register(FileBlock)
    pm.register(TreeBlock)
    
    # Register the new Hello World block
    # pm.register(HelloWorldBlock)