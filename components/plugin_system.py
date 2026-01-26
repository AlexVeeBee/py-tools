import os
import importlib.util
import inspect
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal, QObject

class BlockPluginInterface(QObject):
    """
    Base API for all Block Plugins.
    Inherit from this to create custom blocks.
    """
    # Signals must be defined in the class
    dataChanged = pyqtSignal()

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        """Name displayed in the Dropdown"""
        raise NotImplementedError

    @property
    def id(self) -> str:
        """Unique ID for saving/loading"""
        raise NotImplementedError

    @property
    def description(self) -> str:
        """Tooltip description"""
        return ""
    
    @property
    def drag_types(self) -> list:
        """
        Whether this block supports drag-and-drop reordering.
        Return a list of strings representing supported drag types.
        Example: ["file", "folder"]
        """
        return []

    def create_ui(self, parent_widget: QWidget, root_getter_func, **kwargs) -> QWidget:
        """
        Create and return the configuration widget.
        MUST emit self.dataChanged when inputs change.
        """
        raise NotImplementedError

    def get_state(self, widget: QWidget) -> dict:
        """Return a JSON-serializable dict of the current UI state."""
        raise NotImplementedError

    def set_state(self, widget: QWidget, state: dict):
        """Restore UI from state dict."""
        raise NotImplementedError
    
    # This should interact the prompt item to set the label tag
    def set_label_tag(self, widget: QWidget, tag: str):
        """Optional: Set a label tag on the block UI."""
        pass
    # =========================================================

    def compile(self, state: dict, project_root: str, **kwargs) -> str:
        """
        Return the final prompt text string.
        kwargs can contain 'global_ignore', etc.
        """
        raise NotImplementedError
    
    def get_min_height(self) -> int:
        """Return minimum height for resizing logic."""
        return 100


class PluginManager:
    _instance = None
    _plugins = {}  # {id: plugin_instance}
    _order = []    # [id, id, ...]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
        return cls._instance

    def register(self, plugin_cls):
        """Register a new plugin class."""
        try:
            instance = plugin_cls()
            if instance.id in self._plugins:
                print(f"[PluginManager] Warning: Overwriting plugin {instance.id}")
            
            self._plugins[instance.id] = instance
            if instance.id not in self._order:
                self._order.append(instance.id)
            print(f"[PluginManager] Registered: {instance.name} ({instance.id})")
        except Exception as e:
            print(f"[PluginManager] Failed to register plugin: {e}")

    def get_plugin(self, plugin_id):
        return self._plugins.get(plugin_id)

    def get_all_plugins(self):
        return [self._plugins[pid] for pid in self._order]

    def get_plugin_names(self):
        return [(p.name, p.id) for p in self.get_all_plugins()]
    
    def get_default_plugin_id(self):
        return self._order[0] if self._order else None
    
    def load_from_folder(self, folder_path):
        """Dynamic loader for user plugins"""
        if not os.path.exists(folder_path): return
        for f in os.listdir(folder_path):
            if f.endswith(".py") and not f.startswith("__"):
                path = os.path.join(folder_path, f)
                spec = importlib.util.spec_from_file_location(f[:-3], path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    self._scan_module(mod)

    def auto_load_plugins(self, plugins_dir):
        """Scans the plugins folder and imports .py files."""
        if not os.path.exists(plugins_dir):
            os.makedirs(plugins_dir)

        for filename in os.listdir(plugins_dir):
            if filename.endswith(".py") and not filename.startswith("__"):
                path = os.path.join(plugins_dir, filename)
                spec = importlib.util.spec_from_file_location(filename[:-3], path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Inspect module for subclasses of BlockPluginInterface
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) 
                            and issubclass(obj, BlockPluginInterface) 
                            and obj is not BlockPluginInterface):
                            self.register(obj)