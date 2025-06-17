from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QPropertyAnimation, QRect, QEasingCurve, QParallelAnimationGroup, pyqtSlot
from server import Server

def left_right_sgn(x: str) -> int:
    """
    Checks whether the input is "left" or "right" and returns 1, 0 or -1

    :param x: String
    :return: 1 if x equals "right", -1 if x equals "left" and 0 otherwise
    """
    return (x == "right") - (x == "left")

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

def widget_swap(parent, stacked_widget, new_index, duration=400, direction="right"):
    """
    Animates the transition between widgets in a QStackedWidget.
    Slides the new widget in from the right (or left), pushing the old one out.
    :param parent: The parent widget (usually self)
    :param stacked_widget: The QStackedWidget containing the widgets
    :param new_index: The index of the widget to show
    :param duration: Animation duration in ms
    :param direction: "right" or "left"
    """
    current_index = stacked_widget.currentIndex()
    if current_index == new_index:
        return

    current_widget = stacked_widget.widget(current_index)
    next_widget = stacked_widget.widget(new_index)
    stacked_widget.setCurrentIndex(new_index)
    stacked_widget.resize(stacked_widget.size())  # Ensure correct geometry

    w = stacked_widget.width()
    h = stacked_widget.height()

    # Set up start/end positions
    if direction == "right":
        start_rect = QRect(w, 0, w, h)
        end_rect = QRect(0, 0, w, h)
        old_end_rect = QRect(-w, 0, w, h)
    else:
        start_rect = QRect(-w, 0, w, h)
        end_rect = QRect(0, 0, w, h)
        old_end_rect = QRect(w, 0, w, h)

    next_widget.setGeometry(start_rect)
    next_widget.show()

    anim_in = QPropertyAnimation(next_widget, b"geometry")
    anim_in.setDuration(duration)
    anim_in.setStartValue(start_rect)
    anim_in.setEndValue(end_rect)
    anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)

    anim_out = QPropertyAnimation(current_widget, b"geometry")
    anim_out.setDuration(duration)
    anim_out.setStartValue(QRect(0, 0, w, h))
    anim_out.setEndValue(old_end_rect)
    anim_out.setEasingCurve(QEasingCurve.Type.OutCubic)

    group = QParallelAnimationGroup(parent)
    group.addAnimation(anim_in)
    group.addAnimation(anim_out)

    @pyqtSlot()
    def on_finished():
        current_widget.hide()
        next_widget.setGeometry(0, 0, w, h)

    group.finished.connect(on_finished)
    group.start()

# Example usage for testing confirm_dialogue
if __name__ == "__main__":
    import sys
    class DummyServer:
        has_icon = False
    app = QApplication(sys.argv)
    result = confirm_dialogue(DummyServer(), "Confirm", "Do you want to continue?", QMessageBox.Icon.Question)
    print("User confirmed:", result)