from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QTextEdit, QLabel, QMenu, QLineEdit, QFrame, QWidgetAction, QSystemTrayIcon,
    QStackedWidget, QWIDGETSIZE_MAX)
from PyQt6.QtGui import QIcon, QAction, QTextCursor, QGuiApplication, QFontDatabase
from widgets.sidebar_button import SidebarButtonWithMarker, SidebarButton
from tools.terminal_output_worker import TerminalOutputWorker
from PyQt6.QtCore import Qt, QTimer, QSize, QEvent, QThread
from widgets.confirm_dialogue import confirm_dialogue
from tools.instance_checker import SingleInstance
from startup import startup, change_shortcut
from widgets.whitelist import Whitelist
from server import Server
import json
import sys
import os

class ServerCopilot(QMainWindow):
    def __init__(self, window_width: int = 25, window_height: int = 25):
        print("Creating ServerCopilot instance ...")
        super().__init__()
        self.data = startup(self)
        self.shortcut_name = self.data["desktop_shortcut"]
        self.server = Server(self.data["filepath"])
        self.whitelist_type = self.data["whitelist"]
        self.setWindowTitle(self.server.name)
        self.icon_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "icon"))
        self.data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        self.font_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "fonts"))
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
        self.folded_in = True
        self.fold_after_exit = False
        self.terminate_thread = False
        self.terminal_thread = None
        self.terminal_worker = None
        self.terminal_worker_thread = None
        self.quit_after_startup = False
        self.custom_font_family = "Arial"
        font_id = QFontDatabase.addApplicationFont(os.path.join(self.font_folder, "Not-Bower-Bold.ttf"))
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                self.custom_font_family = font_families[0]
        else:
            print("Failed to load Not-Bower-Bold.ttf font file")

        self.lock_instance()
        self.init_ui()
        self.fold_in()
        print("ServerCopilot instance created successfully")

    def lock_instance(self):
        self.instance_locker = SingleInstance(self, "ServerCopilotMutex" + self.server.name.replace(" ", "_"))
        if not self.instance_locker.is_running():
            self.instance_locker.start_message_listener(self.check_for_instance_messages)
        else:
            print("Already running! Sending data ...")
            self.instance_locker.send_message_to_instance("new instance started")
            raise SystemExit
    
    def init_ui(self):
        print("Initialising UI ...")
        self.button_height = round(1.2 * self.height // 12)
        self.button_width = round((self.width - self.button_height) // 2 - 26)

        button_stylesheet = f"""
            QPushButton {{
                background-color: #262626;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-family: "{self.custom_font_family}", Arial, sans-serif;
            }}
            QPushButton:hover {{
                background-color: #3c3c3c;
            }}
        """
        
        central = QWidget()
        central.setStyleSheet("background-color: #1c1c1c;")
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar_widget = QWidget()
        sidebar_widget.setStyleSheet("background-color: #1c1c1c;")
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setSpacing(10)
        sidebar_layout.setContentsMargins(0, 4, 0, 0)
        sidebar_widget.setFixedWidth(self.button_height + 16)

        def set_selected_tab(selected_btn):
            for btn in [self.main_button, self.whitelist_button, self.settings_button]:
                btn.setSelected(btn is selected_btn)

        icon_size = int(self.button_height * 0.82)

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
        self.fold_button.clicked.connect(self.unfold)
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
            self.stacked_widget.setCurrentIndex(1)
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
            self.stacked_widget.setCurrentIndex(2)
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
            self.stacked_widget.setCurrentIndex(3)
        ])
        self.settings_button.setDisabled(True)  # Disable settings button for now TODO: Implement settings page
        sidebar_layout.addWidget(self.settings_button)
        main_layout.addWidget(sidebar_widget)

        # Seperator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setStyleSheet("color: #232326; background: #232326;")
        separator.setLineWidth(2)
        main_layout.addWidget(separator)

        # Create the stacked widget for main content
        self.stacked_widget = QStackedWidget()

        # Main page (folded)
        main_page_folded = QWidget()
        main_page_folded_layout = QHBoxLayout(main_page_folded)
        main_page_folded_layout.setContentsMargins(5, 5, 5, 5)
        main_page_folded_layout.setSpacing(5)
        self.stop_button_folded = QPushButton("Stop")
        self.stop_button_folded.setFixedSize(self.button_width, self.button_height)
        self.stop_button_folded.clicked.connect(self.stop_server)
        self.stop_button_folded.setStyleSheet(button_stylesheet)
        main_page_folded_layout.addWidget(self.stop_button_folded, alignment=Qt.AlignmentFlag.AlignTop)
        self.restart_button_folded = QPushButton("Restart")
        self.restart_button_folded.setFixedSize(self.button_width, self.button_height)
        self.restart_button_folded.setEnabled(False)
        self.restart_button_folded.clicked.connect(self.restart_server)
        self.restart_button_folded.setStyleSheet(button_stylesheet)
        main_page_folded_layout.addWidget(self.restart_button_folded, alignment=Qt.AlignmentFlag.AlignTop)

        # Main page (unfolded)
        main_page = QWidget()
        main_page_layout = QVBoxLayout(main_page)
        main_page_layout.setContentsMargins(5, 5, 5, 5)
        main_page_layout.setSpacing(5)
        # Terminal
        self.server_terminal = QTextEdit()
        self.server_terminal.setReadOnly(True)
        self.server_terminal.setFixedSize(self.width - self.button_height - 37, self.height - self.button_height - 25)
        self.server_terminal.setStyleSheet(f"""QTextEdit {{
                background-color: #262626;
                font-family: "{self.custom_font_family}", Arial, sans-serif; 
            }}""")
        main_page_layout.addWidget(self.server_terminal, alignment=Qt.AlignmentFlag.AlignTop)
        main_page_layout.addStretch()
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setFixedSize(self.button_width, self.button_height)
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setStyleSheet(button_stylesheet)
        button_layout.addWidget(self.stop_button)
        self.restart_button = QPushButton("Restart")
        self.restart_button.setFixedSize(self.button_width, self.button_height)
        self.restart_button.setEnabled(False)
        self.restart_button.clicked.connect(self.restart_server)
        self.restart_button.setStyleSheet(button_stylesheet)
        button_layout.addWidget(self.restart_button)
        main_page_layout.addLayout(button_layout)

        # Whitelist page
        whitelist_page = QWidget()
        whitelist_page_layout = QVBoxLayout(whitelist_page)
        whitelist_page_layout.setContentsMargins(5, 5, 5, 5)
        whitelist_page_layout.setSpacing(5)
        self.whitelist = Whitelist(self, height=self.height - self.button_height - 25)
        whitelist_page_layout.addWidget(self.whitelist, alignment=Qt.AlignmentFlag.AlignTop)
        self.whitelist.update_whitelist_buttons()
        # Entry field with + and - buttons
        entry_row = QWidget()
        entry_row_layout = QHBoxLayout(entry_row)
        entry_row_layout.setContentsMargins(0, 0, 0, 0)
        entry_row_layout.setSpacing(5)
        self.whitelist_entry = QLineEdit()
        self.whitelist_entry.setPlaceholderText("Enter player name or UUID")
        entry_row_layout.addWidget(self.whitelist_entry)
        add_btn = QPushButton("+")
        add_btn.setFixedWidth(32)
        add_btn.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-size: 18px; border-radius: 8px; } QPushButton:hover { background-color: #388e3c; }")
        add_btn.clicked.connect(self.add_player)
        entry_row_layout.addWidget(add_btn)
        remove_btn = QPushButton("-")
        remove_btn.setFixedWidth(32)
        remove_btn.setStyleSheet("QPushButton { background-color: #c62828; color: white; font-size: 18px; border-radius: 8px; } QPushButton:hover { background-color: #b71c1c; }")
        remove_btn.clicked.connect(self.remove_player)
        entry_row_layout.addWidget(remove_btn)
        whitelist_page_layout.addWidget(entry_row, alignment=Qt.AlignmentFlag.AlignTop)

        # Settings page
        settings_page = QLabel("Settings Page")
        self.stacked_widget.addWidget(main_page_folded)
        self.stacked_widget.addWidget(main_page)
        self.stacked_widget.addWidget(whitelist_page)
        self.stacked_widget.addWidget(settings_page)
        main_layout.addWidget(self.stacked_widget)

        # Set main tab as selected by default
        set_selected_tab(self.main_button)
        self.stacked_widget.setCurrentIndex(1)

        print("UI initialised successfully")

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

    def closeEvent(self, event):
        self.quit_window()
        event.ignore()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.minimize_to_tray()
        super().changeEvent(event)

    def update_terminal(self, line):
        if "[Server thread/INFO]: Done" in line:
            self.server.change_startup_state()
        self.terminal_content.append(line)
        self.server_terminal.setPlainText("".join(self.terminal_content))
        self.server_terminal.moveCursor(QTextCursor.MoveOperation.End)

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
        self.setFixedSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
        self.resize(self.width, self.height)
        self.setFixedSize(self.size())
        self.fold_button.setIcon(QIcon(os.path.join(self.icon_folder, "fold_in_icon_dark.png")))
        try:
            self.fold_button.clicked.disconnect()
        except TypeError:
            pass
        self.stacked_widget.setCurrentIndex(self.last_tab_index)
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
        self.last_tab_index = self.stacked_widget.currentIndex()
        self.stacked_widget.setCurrentIndex(0)
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

    def start_server(self):
        print("Starting server")
        self.update_terminal("[ServerCopilot]: Starting your Server\n")
        if not self.server.has_icon:
            change_shortcut(self.shortcut_name, "main_running.ico", "Stop " + self.server.name)
        else:
            change_shortcut(self.shortcut_name, "server.ico", "Stop " + self.server.name)
        print("└─ Sending Start signal")
        self.server.start_server(3000)
        self.terminate_thread = False
        if self.terminal_worker_thread:
            print("└─ Terminating previous terminal worker thread")
            self.terminate_thread = True
            self.terminal_worker_thread.quit()
            self.terminal_worker_thread.wait()
            self.terminal_worker_thread = None
            self.terminal_worker = None
        print("└─ Creating new terminal worker thread")
        self.terminate_thread = False
        self.terminal_worker = TerminalOutputWorker(self.server, lambda: self.terminate_thread)
        self.terminal_worker_thread = QThread()
        self.terminal_worker.moveToThread(self.terminal_worker_thread)
        self.terminal_worker.new_line.connect(self.update_terminal)
        self.terminal_worker.finished.connect(self.terminal_worker_thread.quit)
        self.terminal_worker_thread.started.connect(self.terminal_worker.run)
        self.terminal_worker_thread.start()
        self.stop_button.setText("Stop")
        self.stop_button_folded.setText("Stop")
        self.stop_button.clicked.disconnect()
        self.stop_button.clicked.connect(self.stop_server)
        self.restart_button.setEnabled(True)
        self.restart_button_folded.setEnabled(True)
        print("└─ Server started successfully")

    def stop_server(self):
        print("Stopping server...")
        if not self.server.in_startup:
            self.update_terminal("[ServerCopilot]: Stopped your Server\n")
            print("└─ Terminating terminal worker thread")
            self.terminate_thread = True
            if self.terminal_worker_thread:
                self.terminal_worker_thread.quit()
                if not self.terminal_worker_thread.wait(500):
                    print("Warning: terminal_worker_thread did not finish in time, terminating forcefully.")
                    self.terminal_worker_thread.terminate()
                    self.terminal_worker_thread.wait(1000)
                self.terminal_worker = None
            print("└─ Sending Stop signal")
            self.server.write_to_server("stop")
            if not self.server.has_icon:
                change_shortcut(self.shortcut_name, "main_dark.ico", "Start " + self.server.name)
            else:
                change_shortcut(self.shortcut_name, "server_dorment.ico", "Start " + self.server.name)
            self.setWindowIcon(QIcon(os.path.join(self.icon_folder, "main_dark.ico")) if not self.server.has_icon else QIcon(os.path.join(self.icon_folder, "server_dorment.ico")))
            self.stop_button.setText("Start")
            self.stop_button_folded.setText("Start")
            self.stop_button.clicked.disconnect()
            self.stop_button.clicked.connect(self.start_server)
            self.restart_button.setEnabled(False)
            self.restart_button_folded.setEnabled(False)
            print("└─ Server stopped successfully")
        else:
            QTimer.singleShot(500, self.stop_server)

    def restart_server(self):
        print("Restarting server...")
        if self.server.in_startup:
            QTimer.singleShot(500, self.restart_server)
        elif self.server.running:
            self.terminal_content.append("[ServerCopilot]: Restarting your Server\n")
            print("└─ Terminating terminal worker thread")
            self.terminate_thread = True
            if self.terminal_worker_thread:
                self.terminal_worker_thread.quit()
                if not self.terminal_worker_thread.wait(500):
                    print("Warning: terminal_worker_thread did not finish in time, terminating forcefully.")
                    self.terminal_worker_thread.terminate()
                    self.terminal_worker_thread.wait(1000)
                self.terminal_worker = None
            print("└─ Sending Stop signal")
            self.server.write_to_server("stop")
            print("└─ Server stopped, Sending Start signal")
            self.server.start_server(3000)
            print("└─ Creating new terminal worker thread")
            self.terminate_thread = False
            self.terminal_worker = TerminalOutputWorker(self.server, lambda: self.terminate_thread)
            self.terminal_worker_thread = QThread()
            self.terminal_worker.moveToThread(self.terminal_worker_thread)
            self.terminal_worker.new_line.connect(self.update_terminal)
            self.terminal_worker.finished.connect(self.terminal_worker_thread.quit)
            self.terminal_worker_thread.started.connect(self.terminal_worker.run)
            self.terminal_worker_thread.start()
            print("└─ Server restarted successfully")

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
        print("Quitting ServerCopilot...")
        if self.server.in_startup:
            if not confirm_dialogue(self.server, "Quit ServerCopilot?", "Your server is currently starting up. Do you want to quit as soon as the server has started?", QMessageBox.Icon.Warning):
                print("└─ User cancelled quit operation")
                return
            print("└─ Will quit as soon as the server has started.")
            def check_and_quit():
                print("└─ Checking if server has started...")
                if not self.server.in_startup:
                    print("└─ Server has started, quitting now.")
                    self.quit_after_startup = True
                    self.quit_window()
                    return
                else:
                    QTimer.singleShot(500, check_and_quit)
            QTimer.singleShot(500, check_and_quit)
            return
        elif self.server.running and not self.quit_after_startup:
            if not confirm_dialogue(self.server, "Quit ServerCopilot?", "Your server is currently running. Are you sure you want to quit?", QMessageBox.Icon.Warning):
                print("└─ User cancelled quit operation")
                return
            self.stop_server()
            change_shortcut(self.shortcut_name, "server_dorment.ico", "Start " + self.server.name)
        if self.tray_icon:
            print("└─ Quitting tray process")
            self.tray_icon.hide()
            self.tray_icon = None
        self.save_settings()
        self.instance_locker.release()
        print("└─ Quit process successful. Until next time, then.")
        QApplication.quit()
        raise SystemExit

if __name__ == "__main__":
    app = QApplication(sys.argv)
    copilot = ServerCopilot()
    copilot.start_server()
    copilot.minimize_to_tray()
    print("ServerCopilot started successfully")
    sys.exit(app.exec())