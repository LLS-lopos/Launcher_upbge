from __future__ import annotations

import errno
import os
import shlex
import struct
import subprocess
import time
import uuid

from PySide6.QtCore import QObject, QSocketNotifier, QTimer, Signal

if os.name == "nt":
    import ctypes
    from ctypes import wintypes

    class COORD(ctypes.Structure):
        _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

    class STARTUPINFOW(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class STARTUPINFOEXW(ctypes.Structure):
        _fields_ = [
            ("StartupInfo", STARTUPINFOW),
            ("lpAttributeList", ctypes.c_void_p),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]
else:
    import fcntl
    import pty
    import termios

    COORD = None
    STARTUPINFOEXW = None
    PROCESS_INFORMATION = None


class PtyProcess(QObject):
    output = Signal(bytes)
    finished = Signal(int)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._process = None
        self._master_fd = None
        self._notifier = None
        self._cols = 80
        self._rows = 24
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(80)
        self._poll_timer.timeout.connect(self._poll)
        self._windows = {}
        self._eof = False

    @property
    def running(self):
        return self._running

    def start(self, command=None, cwd=None, env=None, cols=80, rows=24):
        if self._running or self._process is not None:
            self.stop()
        self._cols = int(cols)
        self._rows = int(rows)
        self._eof = False
        if command is None:
            command = self._default_command()
        environment = dict(os.environ)
        environment["TERM"] = "xterm-256color"
        environment["COLORTERM"] = "truecolor"
        environment.pop("NO_COLOR", None)
        if env:
            environment.update({str(k): str(v) for k, v in env.items()})
        argv = self._normalise_command(command)
        try:
            if os.name == "nt":
                self._start_windows(argv, cwd, environment)
            else:
                self._start_posix(argv, cwd, environment)
        except Exception as exc:
            self.error.emit(str(exc))
            self._running = False
            return False
        self._running = True
        self._poll_timer.start()
        return True

    def write(self, data):
        if not self._running or not data:
            return
        if isinstance(data, str):
            data = data.encode("utf-8")
        try:
            if os.name == "nt":
                self._write_windows(data)
            else:
                self._write_posix(data)
        except Exception as exc:
            self.error.emit(str(exc))

    def resize(self, cols, rows):
        cols = max(1, int(cols))
        rows = max(1, int(rows))
        if cols == self._cols and rows == self._rows:
            return
        self._cols = cols
        self._rows = rows
        if not self._running:
            return
        try:
            if os.name == "nt":
                self._resize_windows(cols, rows)
            else:
                self._set_winsize(self._master_fd, cols, rows)
        except Exception as exc:
            self.error.emit(str(exc))

    def terminate(self):
        if not self._running:
            return
        if os.name == "nt":
            self._terminate_windows()
        else:
            self._terminate_posix()

    def stop(self):
        if not self._running and self._process is None and not self._windows:
            return
        if os.name == "nt":
            kernel = self._windows.get("kernel")
            handle = self._windows.get("process")
            if kernel is not None and handle is not None:
                kernel.TerminateProcess(handle, 1)
                deadline = time.monotonic() + 2
                while time.monotonic() < deadline:
                    if kernel.WaitForSingleObject(handle, 50) != 0x00000102:
                        break
        else:
            process = self._process
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
        self._running = False
        self._poll_timer.stop()
        if os.name == "nt":
            self._cleanup_windows()
        else:
            self._cleanup_posix()
        self._process = None

    def close(self):
        self._poll_timer.stop()
        if os.name == "nt":
            self._cleanup_windows()
        else:
            self._cleanup_posix()

    def _normalise_command(self, command):
        if isinstance(command, str):
            if os.name == "nt":
                return command
            return shlex.split(command)
        return [str(part) for part in command]

    def _default_command(self):
        if os.name == "nt":
            return os.environ.get("COMSPEC", "cmd.exe")
        return os.environ.get("SHELL", "/bin/bash")

    def _set_winsize(self, fd, cols, rows):
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))

    def _start_posix(self, argv, cwd, environment):
        master_fd, slave_fd = pty.openpty()
        try:
            self._set_winsize(slave_fd, self._cols, self._rows)
            os.set_blocking(master_fd, False)
            self._process = subprocess.Popen(
                argv,
                stdin=slave_fd,
                stdout=slave_fd,
                stderr=slave_fd,
                cwd=cwd,
                env=environment,
                start_new_session=True,
                close_fds=True,
            )
        finally:
            os.close(slave_fd)
        self._master_fd = master_fd
        self._notifier = QSocketNotifier(master_fd, QSocketNotifier.Type.Read, self)
        self._notifier.activated.connect(self._read_posix)

    def _read_posix(self):
        chunks = []
        while True:
            try:
                data = os.read(self._master_fd, 65536)
            except BlockingIOError:
                break
            except OSError as exc:
                if exc.errno in (errno.EIO, errno.EBADF):
                    self._mark_eof()
                    break
                self.error.emit(str(exc))
                break
            if not data:
                self._mark_eof()
                break
            chunks.append(data)
        if chunks:
            self.output.emit(b"".join(chunks))

    def _mark_eof(self):
        if self._eof:
            return
        self._eof = True
        if self._notifier is not None:
            self._notifier.setEnabled(False)

    def _write_posix(self, data):
        view = memoryview(data)
        while view:
            written = os.write(self._master_fd, view)
            view = view[written:]

    def _terminate_posix(self):
        process = self._process
        if process is not None and process.poll() is None:
            process.terminate()
            QTimer.singleShot(1000, self._kill_posix)

    def _kill_posix(self):
        process = self._process
        if process is not None and process.poll() is None:
            process.kill()

    def _cleanup_posix(self):
        if self._notifier is not None:
            self._notifier.setEnabled(False)
            self._notifier.deleteLater()
            self._notifier = None
        if self._master_fd is not None:
            try:
                os.close(self._master_fd)
            except OSError:
                pass
            self._master_fd = None

    def _poll(self):
        if self._running and os.name != "nt":
            process = self._process
            if process is not None and process.poll() is not None:
                self._read_posix()
                code = process.returncode
                self._running = False
                self._poll_timer.stop()
                self._cleanup_posix()
                self._process = None
                self.finished.emit(code)
        elif self._running:
            self._poll_windows()
            self._read_windows()

    def _start_windows(self, command, cwd, environment):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_winapi(kernel)
        input_name = "\\\\.\\pipe\\upbge-conpty-in-" + uuid.uuid4().hex
        output_name = "\\\\.\\pipe\\upbge-conpty-out-" + uuid.uuid4().hex
        h_input_read = kernel.CreateNamedPipeW(
            input_name,
            0x00000001,
            0x00000000 | 0x00000000 | 0x00000000,
            1,
            4096,
            4096,
            0,
            None,
        )
        h_input_write = kernel.CreateFileW(input_name, 0x40000000, 0, None, 3, 0, None)
        h_output_read = kernel.CreateNamedPipeW(
            output_name,
            0x00000002,
            0x00000000 | 0x00000000 | 0x00000000,
            1,
            4096,
            4096,
            0,
            None,
        )
        h_output_write = kernel.CreateFileW(output_name, 0x40000000, 0, None, 3, 0, None)
        handles = [h_input_read, h_input_write, h_output_read, h_output_write]
        if any(handle in (None, ctypes.c_void_p(-1).value) for handle in handles):
            raise ctypes.WinError(ctypes.get_last_error())
        h_pc = ctypes.c_void_p()
        result = kernel.CreatePseudoConsole(
            self._coord(self._cols, self._rows),
            h_input_read,
            h_output_write,
            0,
            ctypes.byref(h_pc),
        )
        if result != 0:
            raise ctypes.WinError(result)
        attribute_size = ctypes.c_size_t()
        kernel.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(attribute_size))
        attribute_list = ctypes.create_string_buffer(attribute_size.value)
        if not kernel.InitializeProcThreadAttributeList(
            attribute_list, 1, 0, ctypes.byref(attribute_size)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.UpdateProcThreadAttribute(
            attribute_list,
            0,
            0x0002000A,
            h_pc,
            ctypes.sizeof(h_pc),
            None,
            None,
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        startup = self._startupinfo()
        startup.StartupInfo.cb = ctypes.sizeof(startup)
        startup.lpAttributeList = ctypes.cast(attribute_list, ctypes.c_void_p)
        process_info = self._processinfo()
        command_line = command if isinstance(command, str) else subprocess.list2cmdline(command)
        environment_text = "\0".join(f"{k}={v}" for k, v in environment.items()) + "\0\0"
        environment_buffer = ctypes.create_unicode_buffer(environment_text)
        created = kernel.CreateProcessW(
            None,
            command_line,
            None,
            None,
            False,
            0x00080000 | 0x00000400,
            ctypes.cast(environment_buffer, ctypes.c_void_p),
            cwd,
            ctypes.byref(startup.StartupInfo),
            ctypes.byref(process_info),
        )
        if not created:
            raise ctypes.WinError(ctypes.get_last_error())
        kernel.CloseHandle(h_input_read)
        kernel.CloseHandle(h_output_write)
        kernel.DeleteProcThreadAttributeList(attribute_list)
        kernel.CloseHandle(process_info.hThread)
        self._windows = {
            "kernel": kernel,
            "input": h_input_write,
            "output": h_output_read,
            "pc": h_pc,
            "process": process_info.hProcess,
            "pid": process_info.dwProcessId,
        }

    def _configure_winapi(self, kernel):
        kernel.CreateNamedPipeW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
        ]
        kernel.CreateNamedPipeW.restype = wintypes.HANDLE
        kernel.CreateFileW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        ]
        kernel.CreateFileW.restype = wintypes.HANDLE
        kernel.CreatePseudoConsole.argtypes = [
            self._coord_type(),
            wintypes.HANDLE,
            wintypes.HANDLE,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        kernel.CreatePseudoConsole.restype = ctypes.c_long
        kernel.InitializeProcThreadAttributeList.argtypes = [
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        kernel.InitializeProcThreadAttributeList.restype = wintypes.BOOL
        kernel.UpdateProcThreadAttribute.argtypes = [
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.c_size_t,
            wintypes.LPVOID,
            ctypes.c_size_t,
            wintypes.LPVOID,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        kernel.UpdateProcThreadAttribute.restype = wintypes.BOOL
        kernel.DeleteProcThreadAttributeList.argtypes = [wintypes.LPVOID]
        kernel.CreateProcessW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPWSTR,
            wintypes.LPVOID,
            wintypes.LPVOID,
            wintypes.BOOL,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.LPCWSTR,
            ctypes.POINTER(self._startupinfo_type()),
            ctypes.POINTER(self._processinfo_type()),
        ]
        kernel.CreateProcessW.restype = wintypes.BOOL
        kernel.PeekNamedPipe.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel.PeekNamedPipe.restype = wintypes.BOOL
        kernel.ReadFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        kernel.ReadFile.restype = wintypes.BOOL
        kernel.WriteFile.argtypes = [
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
        ]
        kernel.WriteFile.restype = wintypes.BOOL
        kernel.ResizePseudoConsole.argtypes = [ctypes.c_void_p, self._coord_type()]
        kernel.ResizePseudoConsole.restype = ctypes.c_long
        kernel.ClosePseudoConsole.argtypes = [ctypes.c_void_p]
        kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        kernel.WaitForSingleObject.restype = wintypes.DWORD
        kernel.GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel.GetExitCodeProcess.restype = wintypes.BOOL
        kernel.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel.TerminateProcess.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL

    def _coord_type(self):
        return COORD

    def _coord(self, cols, rows):
        return COORD(cols, rows)

    def _startupinfo_type(self):
        return STARTUPINFOEXW

    def _startupinfo(self):
        return STARTUPINFOEXW()

    def _processinfo_type(self):
        return PROCESS_INFORMATION

    def _processinfo(self):
        return PROCESS_INFORMATION()

    def _read_windows(self):
        kernel = self._windows.get("kernel")
        handle = self._windows.get("output")
        if kernel is None or handle is None:
            return
        while True:
            available = wintypes.DWORD()
            if not kernel.PeekNamedPipe(handle, None, 0, None, ctypes.byref(available), None):
                return
            if available.value == 0:
                return
            buffer = ctypes.create_string_buffer(available.value)
            read = wintypes.DWORD()
            if not kernel.ReadFile(handle, buffer, available.value, ctypes.byref(read), None):
                return
            self.output.emit(buffer.raw[: read.value])

    def _write_windows(self, data):
        kernel = self._windows.get("kernel")
        handle = self._windows.get("input")
        if kernel is None or handle is None:
            return
        view = memoryview(data)
        while view:
            written = wintypes.DWORD()
            chunk = bytes(view[:4096])
            if not kernel.WriteFile(handle, chunk, len(chunk), ctypes.byref(written), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if written.value == 0:
                break
            view = view[written.value :]

    def _resize_windows(self, cols, rows):
        kernel = self._windows.get("kernel")
        console = self._windows.get("pc")
        if kernel is not None and console is not None:
            kernel.ResizePseudoConsole(console, self._coord(cols, rows))

    def _poll_windows(self):
        kernel = self._windows.get("kernel")
        handle = self._windows.get("process")
        if kernel is None or handle is None:
            return
        if kernel.WaitForSingleObject(handle, 0) == 0x00000000:
            code = wintypes.DWORD()
            kernel.GetExitCodeProcess(handle, ctypes.byref(code))
            self._running = False
            self._poll_timer.stop()
            self._cleanup_windows()
            self.finished.emit(code.value)

    def _terminate_windows(self):
        kernel = self._windows.get("kernel")
        handle = self._windows.get("process")
        if kernel is not None and handle is not None:
            kernel.TerminateProcess(handle, 1)

    def _cleanup_windows(self):
        kernel = self._windows.get("kernel")
        if kernel is None:
            return
        for key in ("input", "output", "process"):
            handle = self._windows.get(key)
            if handle is not None:
                kernel.CloseHandle(handle)
        console = self._windows.get("pc")
        if console is not None:
            kernel.ClosePseudoConsole(console)
        self._windows = {}
