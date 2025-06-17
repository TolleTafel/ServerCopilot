from PIL import Image
from PyQt6.QtWidgets import QFileDialog, QWidget
import winshell
import json
import os

def edit_json_file(filepath: str, key: str, new_value):
    """
    Edit a specific part of a JSON file.
    """
    if not os.path.isfile(filepath):
        print(f"File {filepath} not found.")
        return

    with open(filepath, 'r') as file:
        data = json.load(file)

    if key in data:
        data[key] = new_value
    else:
        print(f"Key {key} not found in the JSON file.")
        return

    with open(filepath, 'w') as file:
        json.dump(data, file, indent=4)

def startup(app: QWidget) -> dict:
    """
    Main start for the ServerCopilot. Load saved data, check for new server name/icon and updates.
    """
    filepath = os.path.join(os.path.dirname(__file__), "data", "saved.json")
    with open(filepath, 'r') as file:
        data = json.load(file)
    server_filepath = data["filepath"]
    if server_filepath:
        icon_path = os.path.join(os.path.dirname(server_filepath), "world", "icon.png")
        if os.path.isfile(icon_path):
            icon = Image.open(icon_path)
            icon.save(os.path.join("icon", "server.ico"), format='ICO')
            grayscale_icon = icon.convert("L")
            if "icc_profile" in grayscale_icon.info:
                grayscale_icon.info.pop("icc_profile")
            grayscale_icon.save(os.path.join("icon", "server_dorment.ico"), format='ICO')
            return data
        else:
            return setup(app, "Couldn't find the saved server! Please reselect the server.jar", delete_previous=True)
    else:
        return setup(app, "Select server.jar")

def setup(app: QWidget, filedialog_title: str, delete_previous: bool = False) -> dict:
    """
    Initialize the ServerCopilot when starting without a saved server filepath.
    """
    filepath = os.path.join(os.path.dirname(__file__), "data", "saved.json")
    # Use PyQt6 file dialog
    if app is not None:
        server_filepath, _ = QFileDialog.getOpenFileName(
            parent=app,
            caption=filedialog_title,
            filter="Java archive (*.jar)"
        )
    else:
        # Fallback for headless/test mode
        server_filepath = input("Enter path to server.jar: ")

    if os.path.isfile(server_filepath):
        edit_json_file(filepath, "filepath", server_filepath)
        server_name = os.path.dirname(server_filepath)
        icon_path = os.path.join(server_name, "world", "icon.png")
        if os.path.isfile(icon_path):
            icon = Image.open(icon_path)
            icon.save(os.path.join("icon", "server.ico"), format='ICO')
            grayscale_icon = icon.convert("L")
            if "icc_profile" in grayscale_icon.info:
                grayscale_icon.info.pop("icc_profile")
            grayscale_icon.save(os.path.join("icon", "server_dorment.ico"), format='ICO')
        if delete_previous:
            print("Changing")
            with open(filepath, 'r') as file:
                data = json.load(file)
            desktop_shortcut = data["desktop_shortcut"]
            change_shortcut(desktop_shortcut, "server_dorment.ico", os.path.basename(server_name))
        else:
            create_shortcut(os.path.basename(server_name), "server_dorment.ico")
        with open(filepath, 'r') as file:
            data = json.load(file)
        return data
    else:
        exit(0)

def create_shortcut(name: str, icon_name: str):
    """
    Create a new shortcut on the Desktop
    """
    desktop = winshell.desktop()
    path = os.path.join(desktop, name + ".lnk")
    directory = os.path.dirname(__file__)
    target = os.path.join(directory, "start_without_terminal.vbs")
    icon = os.path.join(directory, "icon", icon_name)
    
    with winshell.shortcut(path) as shortcut:
        shortcut.path = target
        shortcut.working_directory = directory
        shortcut.description = "Stop " + name
        shortcut.icon_location = (icon, 0)
    edit_json_file(os.path.join(directory, "data", "saved.json"), "desktop_shortcut", name + ".lnk")

def change_shortcut(old_name: str, icon_name: str, description: str, new_name: str = None):
    """
    Change the existing shortcut icon and optionally the name.
    """
    desktop = winshell.desktop()
    old_path = os.path.join(desktop, old_name)
    if new_name:
        new_path = os.path.join(desktop, new_name + ".lnk")
        edit_json_file(os.path.join(os.path.dirname(__file__), "data", "saved.json"), "desktop_shortcut", new_name + ".lnk")
    else:
        new_path = old_path
    icon = os.path.join(os.path.dirname(__file__), "icon", icon_name)
    
    if os.path.exists(old_path):
        with winshell.shortcut(old_path) as shortcut:
            shortcut.path = shortcut.path
            shortcut.description = description
            shortcut.icon_location = (icon, 0)
        
        if old_path != new_path:
            os.rename(old_path, new_path)
    else:
        print(f"Shortcut {old_name} not found.")

if __name__ == "__main__":
    create_shortcut("fabric_test_server", "server_dorment.ico")
    # For testing setup without a GUI, pass None
    # setup(None, "1", True)