from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox, QFrame, QMessageBox, QScrollArea, QSizePolicy)
from mojang import API
from .confirm_dialogue import confirm_dialogue
from collections import namedtuple
import json
import os

button_element = namedtuple("button_element", ["frame", "switch", "button", "type"])

api = API()

class Whitelist(QWidget):
    def __init__(self, master, main_button_height=72, width=200, height=200, **kwargs):
        super().__init__(master)
        self.app = master
        self.width = width
        self.height = height
        self.main_button_height = main_button_height
        self.default_whitelist = self.read_whitelist(r".\data\default.json")
        self.guest_whitelist = self.read_whitelist(r".\data\guest.json")
        self.whitelist = self.read_whitelist(r".\data\all_players.json")
        self.button_elements = []
        self.init_ui()
        self.change_server_whitelist()

    def init_ui(self):
        layout = QVBoxLayout(self)
        button_row = QHBoxLayout()

        self.whitelist_default_button = QPushButton("Default")
        self.whitelist_default_button.setFixedHeight(self.main_button_height)
        self.whitelist_default_button.setStyleSheet(f"font-size: 16px; padding: 8px 18px; font-family: '{self.app.custom_font_family}', Arial, sans-serif;")
        self.whitelist_default_button.clicked.connect(self.toggle_whitelist)
        button_row.addWidget(self.whitelist_default_button)

        self.whitelist_guest_button = QPushButton("Guest")
        self.whitelist_guest_button.setFixedHeight(self.main_button_height)
        self.whitelist_guest_button.setStyleSheet(f"font-size: 16px; padding: 8px 18px; font-family: '{self.app.custom_font_family}', Arial, sans-serif;")
        self.whitelist_guest_button.clicked.connect(self.toggle_whitelist)
        button_row.addWidget(self.whitelist_guest_button)

        layout.addLayout(button_row)

        # Scroll areas for player lists
        self.whitelist_default_list = QScrollArea()
        self.whitelist_default_list.setWidgetResizable(True)
        self.whitelist_default_list.setFixedHeight(self.height - self.main_button_height)
        self.default_list_widget = QWidget()
        self.default_list_layout = QVBoxLayout(self.default_list_widget)
        self.default_list_layout.setSpacing(0)
        self.default_list_layout.setContentsMargins(0, 0, 0, 0)
        self.whitelist_default_list.setWidget(self.default_list_widget)

        self.whitelist_guest_list = QScrollArea()
        self.whitelist_guest_list.setWidgetResizable(True)
        self.whitelist_guest_list.setFixedHeight(self.height - self.main_button_height)
        self.guest_list_widget = QWidget()
        self.guest_list_layout = QVBoxLayout(self.guest_list_widget)
        self.guest_list_layout.setSpacing(0)
        self.guest_list_layout.setContentsMargins(0, 0, 0, 0)
        self.whitelist_guest_list.setWidget(self.guest_list_widget)

        lists_row = QHBoxLayout()
        lists_row.addWidget(self.whitelist_default_list)
        lists_row.addWidget(self.whitelist_guest_list)
        layout.addLayout(lists_row)

        self.update_whitelist_buttons()

    def update_whitelist_buttons(self):
        # Clear previous
        while self.default_list_layout.count():
            item = self.default_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        while self.guest_list_layout.count():
            item = self.guest_list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.button_elements.clear()

        def fill_with_entries(layout, entries, make_widget):
            if not entries:
                layout.addStretch(1)
                return
            for entry in entries:
                w = make_widget(entry)
                w.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
                layout.addWidget(w)
            layout.addStretch(1)

        if self.whitelist:
            players = list(self.whitelist.keys())

            def make_default_widget(player):
                def button_click_action(p=player):
                    self.highlight_buttons(p)
                    if hasattr(self.app, "whitelist_entry"):
                        self.app.whitelist_entry.setText(p)
                default_frame = QFrame()
                default_layout = QHBoxLayout(default_frame)
                default_layout.setContentsMargins(0, 0, 0, 0)
                switch_default = QCheckBox()
                switch_default.setChecked(player in self.default_whitelist)
                switch_default.stateChanged.connect(lambda state, p=player, t="default": self.toggle_player(p, t))
                button_default = QPushButton(player)
                button_default.clicked.connect(button_click_action)
                button_default.setStyleSheet("font-size: 14px; padding: 8px 18px; text-align: left;")
                default_layout.addWidget(switch_default)
                default_layout.addWidget(button_default)
                default_layout.addStretch(1)
                self.button_elements.append(button_element(default_frame, switch_default, button_default, "default"))
                return default_frame

            def make_guest_widget(player):
                def button_click_action(p=player):
                    self.highlight_buttons(p)
                    if hasattr(self.app, "whitelist_entry"):
                        self.app.whitelist_entry.setText(p)
                guest_frame = QFrame()
                guest_layout = QHBoxLayout(guest_frame)
                guest_layout.setContentsMargins(0, 0, 0, 0)
                switch_guest = QCheckBox()
                switch_guest.setChecked(player in self.guest_whitelist)
                switch_guest.stateChanged.connect(lambda state, p=player, t="guest": self.toggle_player(p, t))
                button_guest = QPushButton(player)
                button_guest.clicked.connect(button_click_action)
                button_guest.setStyleSheet("font-size: 14px; padding: 8px 18px; text-align: left;")
                guest_layout.addWidget(switch_guest)
                guest_layout.addWidget(button_guest)
                guest_layout.addStretch(1)
                self.button_elements.append(button_element(guest_frame, switch_guest, button_guest, "guest"))
                return guest_frame

            fill_with_entries(self.default_list_layout, players, make_default_widget)
            fill_with_entries(self.guest_list_layout, players, make_guest_widget)
        else:
            self.default_list_layout.addStretch(1)
            self.default_list_layout.addWidget(QLabel("No players"))
            self.default_list_layout.addStretch(1)
            self.guest_list_layout.addStretch(1)
            self.guest_list_layout.addWidget(QLabel("No players"))
            self.guest_list_layout.addStretch(1)

    def highlight_buttons(self, player_name: str):
        for element in self.button_elements:
            if element.button.text() == player_name:
                element.frame.setStyleSheet("border: 2px solid #1e1f22;")
            else:
                element.frame.setStyleSheet("border: 0px solid #2b2d31;")

    def toggle_whitelist(self):
        minimize = False
        if getattr(self.app, "tray_icon", None):
            self.app.maximize_from_tray()
            minimize = True
        if self.app.server.running and confirm_dialogue(
            self.app.server, "Restart your Server?",
            "Your server is currently running. Do you want to restart to apply the new whitelist?",
            QMessageBox.Icon.Warning
        ):
            if not minimize:
                self.app.close_whitelist_menu()
            if self.app.whitelist_type == "default":
                self.app.whitelist_type = "guest"
            else:
                self.app.whitelist_type = "default"
            self.change_server_whitelist()
            if self.app.server.running:
                self.app.restart_server()
            if minimize:
                self.app.minimize_to_tray()
        elif not self.app.server.running:
            if not getattr(self.app, "tray_icon", None):
                self.app.close_whitelist_menu()
            if self.app.whitelist_type == "default":
                self.app.whitelist_type = "guest"
            else:
                self.app.whitelist_type = "default"
            self.change_server_whitelist()
        self.update_whitelist_buttons()

    def format_uuid(self, uuid: str) -> str:
        if len(uuid) == 32 and all(c in "0123456789abcdef" for c in uuid.lower()):
            return f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}"
        return uuid

    def change_server_whitelist(self):
        if not os.path.isfile(r".\data\default.json") or not os.path.isfile(r".\data\guest.json"):
            return
        if self.app.whitelist_type == "default":
            with open(r".\data\default.json", "r") as file:
                data = json.load(file)
        elif self.app.whitelist_type == "guest":
            with open(r".\data\guest.json", "r") as file:
                data = json.load(file)
        for player in data:
            player["uuid"] = self.format_uuid(player["uuid"])
        server_whitelist_path = os.path.join(os.path.dirname(self.app.data["filepath"]), "whitelist.json")
        with open(server_whitelist_path, "w") as server_whitelist_file:
            json.dump(data, server_whitelist_file, indent=4)
        self.app.save_settings()

    def read_whitelist(self, filepath: str) -> dict:
        whitelist = dict()
        if os.path.isfile(filepath):
            with open(filepath, "r") as file:
                data = json.load(file)
            for player in data:
                uuid = player["uuid"]
                name = player["name"]
                whitelist[name] = uuid
        return whitelist

    def name(self, id: str) -> str:
        if len(id) == 32 and all(c in "0123456789abcdef" for c in id.lower()):
            uuid = id
            try:
                name = api.get_username(uuid)
            except Exception:
                return None
        else:
            name = id
        return name

    def toggle_player(self, player_name: str, list_type: str):
        if list_type == "default":
            if player_name in self.default_whitelist:
                self.update_whitelist(r".\data\default.json", remove=[player_name])
            else:
                self.update_whitelist(r".\data\default.json", add=[player_name])
        elif list_type == "guest":
            if player_name in self.guest_whitelist:
                self.update_whitelist(r".\data\guest.json", remove=[player_name])
            else:
                self.update_whitelist(r".\data\guest.json", add=[player_name])
        self.default_whitelist = self.read_whitelist(r".\data\default.json")
        self.guest_whitelist = self.read_whitelist(r".\data\guest.json")
        self.update_whitelist_buttons()

    def update_whitelist(self, filepath: str, add: list[str] = None, remove: list[str] = None):
        whitelist = dict()
        if os.path.isfile(filepath):
            with open(filepath, "r") as file:
                data = json.load(file)
            for player in data:
                uuid = player["uuid"]
                name = player["name"]
                whitelist[name] = uuid
        if add:
            for name in add:
                whitelist[name] = api.get_uuid(name)
        if remove:
            for name in remove:
                if name in whitelist:
                    whitelist.pop(name)
        if "all_players.json" in filepath:
            self.whitelist = whitelist
        elif "default.json" in filepath:
            self.default_whitelist = whitelist
        elif "guest.json" in filepath:
            self.guest_whitelist = whitelist
        updated_data = [{"uuid": uuid, "name": name} for name, uuid in whitelist.items()]
        with open(filepath, "w") as file:
            json.dump(updated_data, file)

    def remove_from_all(self, remove: list[str]):
        filepaths = [r".\data\all_players.json", r".\data\default.json", r".\data\guest.json"]
        for filepath in filepaths:
            whitelist = dict()
            with open(filepath, "r") as file:
                data = json.load(file)
            for player in data:
                uuid = player["uuid"]
                name = player["name"]
                whitelist[name] = uuid
            for name in remove:
                if name in whitelist:
                    whitelist.pop(name)
            if "all_players.json" in filepath:
                self.whitelist = whitelist
            elif "default.json" in filepath:
                self.default_whitelist = whitelist
            elif "guest.json" in filepath:
                self.guest_whitelist = whitelist
            updated_data = [{"uuid": uuid, "name": name} for name, uuid in whitelist.items()]
            with open(filepath, "w") as file:
                json.dump(updated_data, file)

def manual_update_whitelist(filepath: str, add: list[str] = None, remove: list[str] = None):
    whitelist = dict()
    if os.path.isfile(filepath):
        with open(filepath, "r") as file:
            data = json.load(file)
        for player in data:
            uuid = player["uuid"]
            name = player["name"]
            whitelist[name] = uuid
    if add:
        for name in add:
            whitelist[name] = api.get_uuid(name)
    if remove:
        for name in remove:
            whitelist.pop(name)
    updated_data = [{"uuid": uuid, "name": name} for name, uuid in whitelist.items()]
    with open(filepath, "w") as file:
        json.dump(updated_data, file)

if __name__ == "__main__":
    manual_update_whitelist(r".\data\guest.json", ["TolleTafel"])