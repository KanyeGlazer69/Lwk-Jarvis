"""Small desktop shell for the verified Jarvis voice-assistant process."""

from __future__ import annotations

import os
import argparse
import ctypes
import pathlib
import queue
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
from ctypes import wintypes

import mss

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    pystray = None


ROOT = pathlib.Path(os.environ["LOCALAPPDATA"]) / "Jarvis"
RUNNER = ROOT / "Phase4" / "Run-Jarvis-Phase4.ps1"
MUTEX_NAME = "Local\\JarvisDesktopApp-Adrian"


class JarvisApp:
    def __init__(self, start_hidden: bool = False) -> None:
        self.root = tk.Tk()
        self.root.title("Jarvis")
        self.root.geometry("760x520")
        self.root.minsize(620, 420)
        self.root.configure(bg="#09111f")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.process: subprocess.Popen[str] | None = None
        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        self.exiting = False
        self.tray = None
        self._build()
        self._build_transcript_popup()
        self._create_tray()
        if start_hidden:
            self.root.after(50, self.root.withdraw)
        self.root.after(100, self._drain_events)
        self.root.after(350, self.start)

    def _build(self) -> None:
        title = tk.Label(self.root, text="J A R V I S", font=("Segoe UI Semibold", 26),
                         fg="#71e8ff", bg="#09111f")
        title.pack(pady=(24, 4))
        self.status = tk.StringVar(value="OFFLINE")
        tk.Label(self.root, textvariable=self.status, font=("Segoe UI", 11),
                 fg="#8a9ab5", bg="#09111f").pack(pady=(0, 20))

        card = tk.Frame(self.root, bg="#111d30", padx=20, pady=16)
        card.pack(fill="x", padx=28)
        tk.Label(card, text="YOU", font=("Segoe UI Semibold", 9), fg="#7188a8",
                 bg="#111d30").pack(anchor="w")
        self.heard = tk.StringVar(value="Say “Hey Jarvis” when the status is Ready.")
        tk.Label(card, textvariable=self.heard, wraplength=675, justify="left",
                 font=("Segoe UI", 13), fg="#eef6ff", bg="#111d30").pack(anchor="w", pady=(4, 14))
        tk.Label(card, text="JARVIS", font=("Segoe UI Semibold", 9), fg="#71e8ff",
                 bg="#111d30").pack(anchor="w")
        self.answer = tk.StringVar(value="Starting up…")
        tk.Label(card, textvariable=self.answer, wraplength=675, justify="left",
                 font=("Segoe UI", 13), fg="#eef6ff", bg="#111d30").pack(anchor="w", pady=(4, 0))

        buttons = tk.Frame(self.root, bg="#09111f")
        buttons.pack(pady=18)
        self.start_button = tk.Button(buttons, text="Start", width=12, command=self.start,
                                      bg="#167d91", fg="white", relief="flat", font=("Segoe UI", 10))
        self.start_button.pack(side="left", padx=6)
        self.stop_button = tk.Button(buttons, text="Stop", width=12, command=self.stop,
                                     bg="#25344d", fg="white", relief="flat", font=("Segoe UI", 10))
        self.stop_button.pack(side="left", padx=6)
        tk.Button(buttons, text="Hide to tray", width=12, command=self.hide_window,
                  bg="#25344d", fg="white", relief="flat", font=("Segoe UI", 10)).pack(side="left", padx=6)

        self.log = tk.Text(self.root, height=8, bg="#070d17", fg="#7990ad", insertbackground="white",
                           relief="flat", font=("Consolas", 9), state="disabled", padx=12, pady=10)
        self.log.pack(fill="both", expand=True, padx=28, pady=(0, 24))

    def _build_transcript_popup(self) -> None:
        """Pin a clean transcript overlay to the smallest connected display."""
        with mss.mss() as capture:
            monitors = list(capture.monitors[1:])
        monitor = min(monitors, key=lambda item: item["width"] * item["height"])
        width, height, margin = 390, 118, 18
        x = monitor["left"] + monitor["width"] - width - margin
        y = monitor["top"] + monitor["height"] - height - margin

        self.popup = tk.Toplevel(self.root)
        self.popup.title("Jarvis transcript")
        self.popup.geometry(f"{width}x{height}+{x}+{y}")
        self.popup.configure(bg="#0b1626")
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)
        self.popup.attributes("-alpha", 0.94)
        tk.Frame(self.popup, bg="#71e8ff", width=4).pack(side="left", fill="y")
        body = tk.Frame(self.popup, bg="#0b1626", padx=14, pady=11)
        body.pack(side="left", fill="both", expand=True)
        self.popup_status = tk.StringVar(value="JARVIS · STARTING")
        tk.Label(body, textvariable=self.popup_status, font=("Segoe UI Semibold", 9),
                 fg="#71e8ff", bg="#0b1626").pack(anchor="w")
        self.popup_text = tk.StringVar(value="Waiting for “Hey Jarvis”…")
        tk.Label(body, textvariable=self.popup_text, wraplength=345, justify="left",
                 font=("Segoe UI", 12), fg="#f1f7ff", bg="#0b1626").pack(anchor="w", pady=(7, 0))
        self.popup.bind("<Button-1>", lambda _event: self.show_window())

    def _create_tray(self) -> None:
        if pystray is None:
            return
        image = Image.new("RGBA", (64, 64), "#09111f")
        draw = ImageDraw.Draw(image)
        draw.ellipse((5, 5, 59, 59), outline="#71e8ff", width=5)
        draw.ellipse((25, 25, 39, 39), fill="#71e8ff")
        menu = pystray.Menu(
            pystray.MenuItem("Show Jarvis", lambda: self.root.after(0, self.show_window), default=True),
            pystray.MenuItem("Start", lambda: self.root.after(0, self.start)),
            pystray.MenuItem("Stop", lambda: self.root.after(0, self.stop)),
            pystray.MenuItem("Exit", lambda: self.root.after(0, self.exit_app)),
        )
        self.tray = pystray.Icon("Jarvis", image, "Jarvis", menu)
        threading.Thread(target=self.tray.run, daemon=True).start()

    def _set_status(self, value: str) -> None:
        self.status.set(value)
        self.popup_status.set(f"JARVIS · {value}")
        colors = {"READY": "#69f0ae", "THINKING": "#ffd166", "STARTING": "#71e8ff", "OFFLINE": "#8a9ab5"}
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("textvariable") == str(self.status):
                widget.configure(fg=colors.get(value, "#71e8ff"))

    def _append_log(self, line: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", line + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start(self) -> None:
        if self.process and self.process.poll() is None:
            self.show_window()
            return
        if not RUNNER.is_file():
            messagebox.showerror("Jarvis", "The verified Jarvis runner is missing.")
            return
        self._set_status("STARTING")
        self.answer.set("Loading voice recognition and memory…")
        self.popup_text.set("Loading…")
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.process = subprocess.Popen(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(RUNNER)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
            errors="replace", bufsize=1, creationflags=flags,
        )
        threading.Thread(target=self._read_output, args=(self.process,), daemon=True).start()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def _read_output(self, process: subprocess.Popen[str]) -> None:
        assert process.stdout is not None
        for raw in process.stdout:
            self.events.put(("line", raw.rstrip()))
        self.events.put(("exit", str(process.wait())))

    def _drain_events(self) -> None:
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "exit":
                    self._set_status("OFFLINE")
                    self.start_button.configure(state="normal")
                    self.stop_button.configure(state="disabled")
                    if not self.exiting:
                        self.answer.set("Jarvis stopped. Press Start to run it again.")
                    continue
                self._append_log(value)
                if value.startswith("TRANSCRIPT:"):
                    transcript = value.partition(":")[2].strip()
                    self.heard.set(transcript)
                    self.popup_text.set(transcript)
                elif value.startswith("JARVIS:"):
                    self.answer.set(value.partition(":")[2].strip())
                elif value == "Jarvis is thinking...":
                    self._set_status("THINKING")
                    self.answer.set("Thinking…")
                elif value.startswith("Ready"):
                    self._set_status("READY")
                    if self.popup_text.get() in ("Loading…", "Listening…"):
                        self.popup_text.set("Waiting for “Hey Jarvis”…")
                elif value.startswith("Speak now"):
                    self._set_status("LISTENING")
                    self.popup_text.set("Listening…")
                elif value.startswith("Spoken response") or value.endswith("PASSED"):
                    self._set_status("READY")
        except queue.Empty:
            pass
        if not self.exiting:
            self.root.after(100, self._drain_events)

    def stop(self) -> None:
        process = self.process
        if not process or process.poll() is not None:
            return
        subprocess.run(["taskkill.exe", "/PID", str(process.pid), "/T", "/F"],
                       capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        self._set_status("OFFLINE")

    def hide_window(self) -> None:
        if self.tray:
            self.root.withdraw()
        else:
            self.root.iconify()

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def exit_app(self) -> None:
        self.exiting = True
        self.stop()
        if self.tray:
            self.tray.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def acquire_single_instance():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR)
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if not handle or ctypes.get_last_error() == 183:
        if handle:
            kernel32.CloseHandle(handle)
        return None
    return handle


def release_single_instance(handle) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    kernel32.CloseHandle(handle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--startup", action="store_true")
    args = parser.parse_args()
    mutex = acquire_single_instance()
    if mutex is not None:
        try:
            JarvisApp(start_hidden=args.startup).run()
        finally:
            release_single_instance(mutex)
