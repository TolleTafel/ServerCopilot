import ctypes
from ctypes import wintypes
import threading
import socket

class SingleInstance:
    """
    Ensures only a single instance of the application is running.
    Uses a named mutex and a localhost socket for inter-process communication.
    """

    def __init__(self, app, mutex_name, port=65432):
        self.app = app
        self.mutex_name = mutex_name
        self.port = port
        self.mutex = ctypes.windll.kernel32.CreateMutexW(None, wintypes.BOOL(True), self.mutex_name)
        self.last_error = ctypes.windll.kernel32.GetLastError()

    def is_running(self):
        """
        Returns True if another instance is running, False otherwise.
        """
        ERROR_ALREADY_EXISTS = 183
        return self.last_error == ERROR_ALREADY_EXISTS

    def send_message_to_instance(self, message):
        """
        Sends a message to the running instance via localhost socket.
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
                client_socket.connect(("localhost", self.port))
                client_socket.sendall(message.encode("utf-8"))
        except ConnectionRefusedError:
            print("Failed to send message. No instance is listening.")

    def start_message_listener(self, on_message_callback):
        """
        Starts a socket server to listen for messages from other instances.
        Calls on_message_callback(message) when a message is received.
        """
        def listen():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind(("localhost", self.port))
                server_socket.listen(1)
                while True:
                    conn, _ = server_socket.accept()
                    with conn:
                        data = conn.recv(1024)
                        if data:
                            on_message_callback(data.decode("utf-8"))

        self.listener_thread = threading.Thread(target=listen, daemon=True)
        self.listener_thread.start()

    def release(self):
        """
        Releases the mutex to allow future instances of the application to run.
        Should be called when the application exits.
        """
        if self.mutex:
            ctypes.windll.kernel32.ReleaseMutex(self.mutex)

if __name__ == "__main__":
    # Example usage for testing
    data = []
    locker = SingleInstance(None, "ServerCopilotMutex")
    if not locker.is_running():
        print("Start listening")
        locker.start_message_listener(lambda x: data.append(x))
        while not data:
            pass
        print(data)
        locker.release()
    else:
        print("Already running! Sending data ...")
        locker.send_message_to_instance("Hallo")
        locker.release()