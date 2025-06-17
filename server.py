import subprocess
import time
import os

class Server:
    """
    A minecraft server API that allows Python to interact with the server.

    :ivar server_filepath: The filepath to the server.jar file
    :ivar server_folder_filepath: The filepath to the folder in which the server.jar file lies.
    :ivar name: Server name.
    :ivar has_icon: Whether the server has an icon or not.
    :ivar server: The subprocess.Popen that controls the server.
    :ivar running: True when the server is currently running, False otherwise.
    """

    def __init__(self, filepath: str):
        self.server_filepath = filepath
        self.server_folder_filepath = os.path.dirname(filepath)
        self.name = os.path.basename(self.server_folder_filepath)
        icon_path = os.path.join(self.server_folder_filepath, "world", "icon.png")
        self.has_icon = os.path.isfile(icon_path)
        self.running = False
        self.in_startup = False
        self.server = None

    def start_server(self, memory: int, gui: bool = False):
        """
        Starts the server at the saved filepath with the given arguments.

        :param memory: The amount of memory that gets allocated to the server in MB.
        :param gui: Whether or not the server is supposed to have a gui.
        """
        if not self.running:
            self.in_startup = True
            memory_arg = f"-Xmx{memory}M"
            gui_arg = [] if gui else ["nogui"]
            self.server = subprocess.Popen(
                ["java", memory_arg, "-jar", self.server_filepath] + gui_arg,
                cwd=self.server_folder_filepath,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            self.running = True
        else:
            print("Couldn't start the server, because it's already running!")

    def write_to_server(self, text: str) -> bool:
        """
        Writes the given message to the server console. If the text is "stop", it terminates the server process.

        :param text: The text that gets written to the console.
        """
        if self.in_startup:
            return False
        elif self.running and self.server and self.server.stdin:
            try:
                self.server.stdin.write(text.strip() + "\n")
                self.server.stdin.flush()
                if text.strip().lower() == "stop":
                    self.running = False
                    self.server.stdin.close()
                    self.server.wait(timeout=30)
            except Exception as e:
                print(f"Error writing to server: {e}")
                return False
            return True
        else:
            return False
        
    def change_startup_state(self):
        """
        Changes the in_startup state from True to False and stops the server if a stop command is buffered
        """
        self.in_startup = False

if __name__ == "__main__":
    filepath = r"C:\Users\bened\OneDrive\Desktop\fabric_test_server\fabric-server-mc.1.21.4-loader.0.16.9-launcher.1.0.1.jar"
    example_server = Server(filepath)
    print("Starting server")
    example_server.start_server(4000, True)
    time.sleep(15)
    print("Writing to server")
    example_server.write_to_server("say Hello")
    time.sleep(15)
    print("Stopping server")
    example_server.write_to_server("stop")
    time.sleep(15)