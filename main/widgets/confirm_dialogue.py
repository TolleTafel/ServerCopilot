from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from server import Server

def confirm_dialogue(server: Server, title: str, message: str, message_icon: QMessageBox.Icon) -> bool:
    """
    Pulls up a Confirm Dialogue window that asks the user to confirm or cancel. Blocks until the user interacts with it.

    :param title: The title of the widget
    :param message: The message the user gets asked
    :param message_icon: The icon type that gets displayed next to the message
    :return: True, if the user clicks the OK button, False otherwise
    """
    if not QApplication.instance():
        app = QApplication([])
    confirmation_dialog = QMessageBox()
    confirmation_dialog.setIcon(message_icon)
    confirmation_dialog.setWindowTitle(title)
    confirmation_dialog.setText(message)
    confirmation_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    confirmation_dialog.setDefaultButton(QMessageBox.StandardButton.No)
    if server.has_icon:
        icon = QIcon(r"icon\server.ico")
    else:
        icon = QIcon(r"icon\main_running.ico")
    confirmation_dialog.setWindowIcon(icon)
    response = confirmation_dialog.exec()
    return response == QMessageBox.StandardButton.Yes
