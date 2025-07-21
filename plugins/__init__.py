import importlib
import os

def load_plugins(dispatcher, bot):
    plugin_folder = os.path.dirname(__file__)
    for filename in os.listdir(plugin_folder):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = f"plugins.{filename[:-3]}"
            module = importlib.import_module(module_name)
            if hasattr(module, "register"):
                module.register(dispatcher, bot)
