import os
import pty
import subprocess
import asyncio
from typing import Callable

class TerminalManager:
    def __init__(self):
        self.master_fd = None
        self.shell_process = None
        self.loop = None

    def start_shell(self, output_callback: Callable[[str], None]):
        """Starts a bash shell in a pty and pipes output to callback using asyncio."""
        print("🐚 [Terminal] Starting shell process...")
        self.loop = asyncio.get_running_loop()
        
        try:
            # Create a pseudo-terminal
            self.master_fd, slave_fd = pty.openpty()
            print(f"🐚 [Terminal] PTY opened: master_fd={self.master_fd}")
            
            # Start bash in the pty
            self.shell_process = subprocess.Popen(
                ["/bin/bash"],
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                preexec_fn=os.setsid,
                env=os.environ.copy()
            )
            print(f"🐚 [Terminal] Shell PID: {self.shell_process.pid}")
            
            # Close slave_fd in parent
            os.close(slave_fd)
            
            # Set master_fd to non-blocking
            os.set_blocking(self.master_fd, False)
            
            # Register reader with asyncio loop
            self.loop.add_reader(self.master_fd, self._read_output, output_callback)
            print("🐚 [Terminal] Asyncio reader registered")
        except Exception as e:
            print(f"❌ [Terminal] Error starting shell: {e}")
            self.stop()

    def _read_output(self, callback):
        """Callback for asyncio reader."""
        try:
            data = os.read(self.master_fd, 1024).decode('utf-8', errors='ignore')
            if data:
                asyncio.create_task(callback(data))
        except (OSError, ValueError) as e:
            print(f"⚠️ [Terminal] Read error or EOF: {e}")
            self.stop()

    def write_input(self, data: str):
        """Writes input data to the master_fd."""
        if self.master_fd:
            try:
                os.write(self.master_fd, data.encode())
            except OSError as e:
                print(f"❌ [Terminal] Write error: {e}")

    def stop(self):
        """Kills the shell process and stops reading."""
        print("🐚 [Terminal] Stopping shell...")
        if self.master_fd and self.loop:
            self.loop.remove_reader(self.master_fd)
        
        if self.shell_process:
            self.shell_process.terminate()
            
        if self.master_fd:
            try:
                os.close(self.master_fd)
            except OSError:
                pass
        self.master_fd = None
        print("🐚 [Terminal] Shell stopped")

terminal_manager = TerminalManager()
