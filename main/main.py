from widgets.confirm_dialogue import confirm_dialogue
from widgets.sidebar_button import SidebarButtonWithMarker, SidebarButton
from startup import startup, change_shortcut
from instance_checker import SingleInstance
from whitelist import Whitelist
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QTextEdit, QLabel, QMenu, QGridLayout, QLineEdit, QFrame, QWidgetAction, QSystemTrayIcon,
    QStackedWidget, QWIDGETSIZE_MAX
)
from PyQt6.QtGui import QIcon, QPixmap, QAction, QTextCursor, QGuiApplication
from PyQt6.QtCore import Qt, QTimer, QSize
from server import Server
import threading
import json
import sys
import os

class ServerCopilot(QMainWindow):
    def __init__(self, window_width: int = 25, window_height: int = 25):
        super().__init__()
        self.message = None
        self.instance_locker = SingleInstance(self, "ServerCopilotMutex")
        if not self.instance_locker.is_running():
            self.instance_locker.start_message_listener(self.check_for_instance_messages)
        else:
            print("Already running! Sending data ...")
            self.instance_locker.send_message_to_instance("new instance started")
            raise SystemExit
        self.data = startup(self)
        self.shortcut_name = self.data["desktop_shortcut"]
        self.server = Server(self.data["filepath"])
        self.whitelist_type = self.data["whitelist"]
        self.setWindowTitle(self.server.name)
        self.icon_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "icon"))
        self.data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        self.setWindowIcon(QIcon(os.path.join(self.icon_folder, "server.ico")) if self.server.has_icon else QIcon(os.path.join(self.icon_folder, "main_dark.ico")))
        self.width = round(window_width/100 * QGuiApplication.primaryScreen().geometry().width())
        self.height = round(window_height/100 * QGuiApplication.primaryScreen().geometry().height())
        self.resize(self.width, self.height)
        self.setFixedSize(self.width, self.height)
        self.tray = None
        self.new_content = []
        self.terminal_content = []
        self.scrollbar_guardian = True
        self.minimize_guardian = False
        self.folded_in = True  # Start folded
        self.fold_after_exit = False
        self.terminate_thread = False
        self.terminal_thread = None

        self.init_ui()
        self.fold_in()  # Start in folded state
        self.show()

    def init_ui(self):
        self.button_height = round(1.2 * self.height // 12)

        central = QWidget()
        central.setStyleSheet("background-color: #121214;")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)

        # Sidebar (vertical) with gray background
        sidebar_widget = QWidget()
        sidebar_widget.setStyleSheet("background-color: #121214;")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setSpacing(10)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_widget.setFixedWidth(self.button_height + 16)

        def set_selected_tab(selected_btn):
            for btn in [self.main_button, self.whitelist_button, self.settings_button]:
                btn.setSelected(btn is selected_btn)

        icon_size = int(self.button_height * 0.75)

        # Fold button
        self.fold_button = QPushButton()
        self.fold_button.setIcon(QIcon(os.path.join(self.icon_folder, "unfold_icon_dark.png")))
        self.fold_button.setFixedSize(self.button_height, self.button_height)
        self.fold_button.setIconSize(QSize(icon_size, icon_size))
        self.fold_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.fold_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #29292b;
            }
        """)
        self.fold_button.clicked.connect(self.unfold)  # Connect to unfold by default
        sidebar_layout.addWidget(self.fold_button)

        fold_container = QWidget()
        fold_layout = QHBoxLayout(fold_container)
        fold_layout.setContentsMargins(0, 0, 0, 0)
        fold_layout.setSpacing(0)
        fold_layout.addWidget(self.fold_button)
        sidebar_layout.addWidget(fold_container)

        # Main tab button (server icon)
        self.main_button = SidebarButtonWithMarker(SidebarButton())
        self.main_button.button.setIcon(QIcon(os.path.join(self.icon_folder, "terminal_icon_dark.png")))
        self.main_button.setFixedSize(self.button_height, self.button_height)
        self.main_button.button.setIconSize(QSize(icon_size, icon_size))
        self.main_button.button.clicked.connect(lambda: [
            set_selected_tab(self.main_button),
            self.stacked_widget.setCurrentIndex(0)
        ])
        sidebar_layout.addWidget(self.main_button)

        # Whitelist tab button
        self.whitelist_button = SidebarButtonWithMarker(SidebarButton())
        if self.whitelist_type == "default":
            self.whitelist_button.button.setIcon(QIcon(os.path.join(self.icon_folder, "whitelist_off_icon_dark.png")))
        else:
            self.whitelist_button.button.setIcon(QIcon(os.path.join(self.icon_folder, "whitelist_on_icon_dark.png")))
        self.whitelist_button.setFixedSize(self.button_height, self.button_height)
        self.whitelist_button.button.setIconSize(QSize(icon_size, icon_size))
        self.whitelist_button.button.clicked.connect(lambda: [
            set_selected_tab(self.whitelist_button),
            self.stacked_widget.setCurrentIndex(1)
        ])
        sidebar_layout.addWidget(self.whitelist_button)

        sidebar_layout.addStretch()  # Pushes the settings button to the bottom

        # Settings tab button
        self.settings_button = SidebarButtonWithMarker(SidebarButton())
        self.settings_button.button.setIcon(QIcon(os.path.join(self.icon_folder, "settings_icon_dark.png")))
        self.settings_button.setFixedSize(self.button_height, self.button_height)
        self.settings_button.button.setIconSize(QSize(icon_size, icon_size))
        self.settings_button.button.clicked.connect(lambda: [
            set_selected_tab(self.settings_button),
            self.stacked_widget.setCurrentIndex(2)
        ])
        sidebar_layout.addWidget(self.settings_button)
        main_layout.addWidget(sidebar_widget)

        # Seperator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #232326; background: #232326;")
        separator.setLineWidth(2)
        main_layout.addWidget(separator)

        # Create the stacked widget for main content
        self.stacked_widget = QStackedWidget()
        main_page = QLabel("Main Page")
        whitelist_page = QLabel("Whitelist Page")
        settings_page = QLabel("Settings Page")
        self.stacked_widget.addWidget(main_page)
        self.stacked_widget.addWidget(whitelist_page)
        self.stacked_widget.addWidget(settings_page)
        main_layout.addWidget(self.stacked_widget)

        # Set main tab as selected by default
        set_selected_tab(self.main_button)
        self.stacked_widget.setCurrentIndex(0)

    def change_player(self):
        id = self.whitelist_entry.text().strip()
        player = self.whitelist.name(id)
        if player in self.whitelist.whitelist:
            self.remove_player(player)
        else:
            self.add_player(player)

    def add_player(self, player=None):
        if not player:
            id = self.whitelist_entry.text().strip()
            player = self.whitelist.name(id)
        if player:
            self.whitelist.update_whitelist(os.path.join(self.data_folder, "all_players.json"), add=[player])
            self.whitelist.update_whitelist(os.path.join(self.data_folder, "guest.json"), add=[player])
            self.whitelist.update_whitelist_buttons()
        self.whitelist_entry.clear()

    def remove_player(self, player=None):
        if not player:
            id = self.whitelist_entry.text().strip()
            player = self.whitelist.name(id)
        if player:
            self.whitelist.remove_from_all([player])
            self.whitelist.update_whitelist_buttons()
        self.whitelist_entry.clear()

    def open_whitelist_menu(self):
        self.whitelist_button.setIcon(QIcon(os.path.join(self.icon_folder, "back_icon_dark.png")))
        self.whitelist_button.clicked.disconnect()
        self.whitelist_button.clicked.connect(self.close_whitelist_menu)
        # widget_swap(self, self.stacked_widget, 1, direction="right")

    def close_whitelist_menu(self):
        self.whitelist_button.setIcon(QIcon(os.path.join(self.icon_folder, "whitelist_on_icon_dark.png")))
        self.whitelist_button.clicked.disconnect()
        self.whitelist_button.clicked.connect(self.open_whitelist_menu)
        # widget_swap(self, self.stacked_widget, 0, direction="left")

    def update_terminal(self):
        if any(line.strip() for line in self.new_content):
            for line in self.new_content:
                if "[Server thread/INFO]: Done" in line:
                    self.server.change_startup_state()
            self.terminal_content.extend(self.new_content)
            self.new_content.clear()
            self.server_terminal.setPlainText("".join(self.terminal_content))
            self.server_terminal.moveCursor(QTextCursor.MoveOperation.End)
        QTimer.singleShot(1000, self.update_terminal)

    def save_settings(self):
        settings = {
            "filepath": self.data["filepath"],
            "desktop_shortcut": self.shortcut_name,
            "view_mode": "black",
            "whitelist": self.whitelist_type
        }
        with open(os.path.join(self.data_folder, "saved.json"), "w") as file:
            json.dump(settings, file, indent=4)

    def unfold(self):
        screen_height = QGuiApplication.primaryScreen().geometry().height()
        self.setFixedSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
        self.resize(self.width, self.height)
        self.setFixedSize(self.size())
        self.fold_button.setIcon(QIcon(os.path.join(self.icon_folder, "fold_in_icon_dark.png")))
        try:
            self.fold_button.clicked.disconnect()
        except TypeError:
            pass
        self.fold_button.clicked.connect(self.fold_in)
        self.folded_in = False
        self.main_button.show()
        self.whitelist_button.show()
        self.settings_button.show()

    def fold_in(self):
        self.setFixedSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
        fold_height = self.fold_button.height() + 16  # 16 for padding/margin
        self.resize(self.width, fold_height)
        self.setFixedSize(self.size())
        self.fold_button.setIcon(QIcon(os.path.join(self.icon_folder, "unfold_icon_dark.png")))
        try:
            self.fold_button.clicked.disconnect()
        except TypeError:
            pass
        self.fold_button.clicked.connect(self.unfold)
        self.folded_in = True
        self.main_button.hide()
        self.whitelist_button.hide()
        self.settings_button.hide()
        # Optionally hide other widgets if needed

    def start_server(self):
        self.new_content.append("[ServerCopilot]: Starting your Server\n")
        if not self.server.has_icon:
            change_shortcut(self.shortcut_name, "main_running.ico", "Stop " + self.server.name)
        else:
            change_shortcut(self.shortcut_name, "server.ico", "Stop " + self.server.name)
        self.server.start_server(3000)
        self.terminate_thread = False
        self.terminal_thread = threading.Thread(target=lambda: get_terminal_output(self), daemon=True)
        self.terminal_thread.start()
        self.stop_button.setText("Stop")
        self.stop_button.clicked.disconnect()
        self.stop_button.clicked.connect(self.stop_server)
        self.restart_button.setEnabled(True)
        QTimer.singleShot(500, self.update_terminal)

    def stop_server(self):
        if not self.server.in_startup:
            self.new_content.append("[ServerCopilot]: Stopped your Server\n")
            self.terminate_thread = True
            if self.terminal_thread:
                self.terminal_thread.join(1)
            self.server.write_to_server("stop")
            if not self.server.has_icon:
                change_shortcut(self.shortcut_name, "main_dark.ico", "Start " + self.server.name)
            else:
                change_shortcut(self.shortcut_name, "server_dorment.ico", "Start " + self.server.name)
            self.setWindowIcon(QIcon(os.path.join(self.icon_folder, "main_dark.ico")) if not self.server.has_icon else QIcon(os.path.join(self.icon_folder, "server_dorment.ico")))
            self.stop_button.setText("Start")
            self.stop_button.clicked.disconnect()
            self.stop_button.clicked.connect(self.start_server)
            self.restart_button.setEnabled(False)
        else:
            QTimer.singleShot(500, self.stop_server)

    def restart_server(self):
        if self.server.in_startup:
            QTimer.singleShot(500, self.restart_server)
        elif self.server.running:
            self.new_content.append("[ServerCopilot]: Restarting your Server\n")
            self.terminate_thread = True
            if self.terminal_thread:
                self.terminal_thread.join(1)
            self.server.write_to_server("stop")
            self.server.start_server(3000)
            self.terminate_thread = False
            self.terminal_thread = threading.Thread(target=lambda: get_terminal_output(self), daemon=True)
            self.terminal_thread.start()

    def minimize_to_tray(self):
        self.hide()
        if self.server.has_icon:
            icon = QIcon(os.path.join(self.icon_folder, "server.ico")) if self.server.running else QIcon(os.path.join(self.icon_folder, "server_dorment.ico"))
        else:
            icon = QIcon(os.path.join(self.icon_folder, "main_running.ico")) if self.server.running else QIcon(os.path.join(self.icon_folder, "main_dark.ico"))
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip(self.server.name)
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu::separator {
                height: 2px;
                background: #252526;
                margin: 4px 8px;
            }""")

        widget = QWidget()
        layout = QHBoxLayout()
        image_label = QLabel()
        image_label.setPixmap(icon.pixmap(16, 16))
        text_label = QLabel(self.server.name)
        layout.addWidget(image_label)
        layout.addWidget(text_label)
        widget.setLayout(layout)
        widget_action = QWidgetAction(menu)
        widget_action.setDefaultWidget(widget)
        menu.addAction(widget_action)
        menu.addSeparator()

        maximize_icon = QIcon(os.path.join(self.icon_folder, "maximize_icon_dark.png"))
        maximize_action = QAction(maximize_icon, "Maximize", self)
        maximize_action.triggered.connect(self.maximize_from_tray)
        menu.addAction(maximize_action)
        if self.whitelist_type == "default":
            whitelist_icon = QIcon(os.path.join(self.icon_folder, "whitelist_off_icon_dark.png"))
        else:
            whitelist_icon = QIcon(os.path.join(self.icon_folder, "whitelist_on_icon_dark.png"))
        whitelist_action = QAction(whitelist_icon, "Whitelist", self)
        whitelist_action.triggered.connect(self.whitelist.toggle_whitelist)
        menu.addAction(whitelist_action)
        menu.addSeparator()

        quit_icon = QIcon(os.path.join(self.icon_folder, "quit_icon_dark.png"))
        quit_action = QAction(quit_icon, "Quit", self)
        quit_action.triggered.connect(self.quit_window)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.maximize_from_tray()

    def maximize_from_tray(self):
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        self.showNormal()
        self.raise_()
        self.activateWindow()
        if self.server.running:
            self.setWindowIcon(QIcon(os.path.join(self.icon_folder, "main_running.ico")) if not self.server.has_icon else QIcon(os.path.join(self.icon_folder, "server.ico")))
            self.stop_button.setText("Stop")
            self.stop_button.clicked.disconnect()
            self.stop_button.clicked.connect(self.stop_server)
            self.restart_button.setEnabled(True)
            QTimer.singleShot(500, self.update_terminal)
        else:
            self.setWindowIcon(QIcon(os.path.join(self.icon_folder, "main_dark.ico")) if not self.server.has_icon else QIcon(os.path.join(self.icon_folder, "server_dorment.ico")))
            self.stop_button.setText("Start")
            self.stop_button.clicked.disconnect()
            self.stop_button.clicked.connect(self.start_server)
            self.restart_button.setEnabled(False)

    def check_for_instance_messages(self, message):
        if message == "new instance started":
            message = None
            if self.server.running:
                if self.tray_icon:
                    self.quit_window()
                else:
                    self.stop_server()
            else:
                self.start_server()

    def quit_window(self):
        if self.server.running:
            if not confirm_dialogue(self.server, "Quit ServerCopilot?", "Your server is currently running. Are you sure you want to quit?", QMessageBox.Icon.Warning):
                return
            self.terminate_thread = True
            if self.terminal_thread:
                self.terminal_thread.join(1)
            self.server.write_to_server("stop")
            change_shortcut(self.shortcut_name, "server_dorment.ico", "Start " + self.server.name)
        if self.tray_icon:
            self.tray_icon.hide()
            self.tray_icon = None
        self.save_settings()
        self.instance_locker.release()
        QApplication.quit()
        raise SystemExit

def get_terminal_output(app):
    if app.server.server:
        with app.server.server as terminal:
            for line in terminal.stdout:
                if app.terminate_thread:
                    break
                if line:
                    app.new_content.append(line)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    copilot = ServerCopilot()
    # copilot.start_server()
    sys.exit(app.exec())