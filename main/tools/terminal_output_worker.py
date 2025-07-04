from PyQt6.QtCore import QObject, pyqtSignal

class TerminalOutputWorker(QObject):
    """Worker to handle terminal output in a separate thread."""
    new_line = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, server, should_terminate_func):
        """
        Initialize the worker with a server and a termination condition.
        
        :param server: The server instance to read terminal output from.
        :param should_terminate_func: A callable that returns True if the worker should stop.
        """
        super().__init__()
        self.server = server
        self.should_terminate_func = should_terminate_func
        self._running = True

    def run(self):
        """Run the worker to process terminal output."""
        if self.server.server:
            with self.server.server as terminal:
                for line in terminal.stdout:
                    if self.should_terminate_func():
                        break
                    if line:
                        self.new_line.emit(line)
        self.finished.emit()