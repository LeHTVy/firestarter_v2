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
        self.loop = asyncio.get_running_loop()
        
        # Create a pseudo-terminal
        self.master_fd, slave_fd = pty.openpty()
        
        # Start bash in the pty
        self.shell_process = subprocess.Popen(
            ["/bin/bash"],
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid,
            env=os.environ.copy()
        )
        
        # Close slave_fd in parent
        os.close(slave_fd)
        
        # Set master_fd to non-blocking
        os.set_blocking(self.master_fd, False)
        
        # Register reader with asyncio loop
        self.loop.add_reader(self.master_fd, self._read_output, output_callback)

    def _read_output(self, callback):
        """Callback for asyncio reader."""
        try:
            data = os.read(self.master_fd, 1024).decode('utf-8', errors='ignore')
            if data:
                asyncio.create_task(callback(data))
        except (OSError, ValueError):
            self.stop()

    def write_input(self, data: str):
        """Writes input data to the master_fd."""
        if self.master_fd:
            try:
                os.write(self.master_fd, data.encode())
            except OSError:
                pass

    def stop(self):
        """Kills the shell process and stops reading."""
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

terminal_manager = TerminalManager()
