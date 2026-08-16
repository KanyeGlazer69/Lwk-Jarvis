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
    from PIL import Image, ImageDraw, ImageOps, ImageTk
except ImportError:
    pystray = None


ROOT = pathlib.Path(os.environ["LOCALAPPDATA"]) / "Jarvis"
RUNNER = ROOT / "Phase4" / "Run-Jarvis-Phase4.ps1"
MUTEX_NAME = "Local\\JarvisDesktopApp-Adrian"
MARBLE = pathlib.Path(__file__).resolve().parent / "assets" / "black-gold-marble.png"
BLACK = "#050505"
PANEL = "#0b0b0d"
GOLD = "#c9a24b"
GOLD_BRIGHT = "#e4c56a"
IVORY = "#f5f1e8"
MUTED = "#aaa49a"


class JarvisApp:
    def __init__(self, start_hidden: bool = False) -> None:
        self.root = tk.Tk()
        self.root.title("Jarvis")
        monitor = self._smallest_monitor()
        width, height, margin = 760, 520, 28
        x = monitor["left"] + monitor["width"] - width - margin
        y = monitor["top"] + monitor["height"] - height - margin
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(620, 420)
        self.root.configure(bg=BLACK)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
        self.process: subprocess.Popen[str] | None = None
        self.events: queue.Queue[tuple[str, str]] = queue.Queue()
        self.exiting = False
        self.tray = None
        self.resize_job = None
        self._build()
        self._build_transcript_popup()
        self._create_tray()
        self.root.after(100, self._drain_events)
        self.root.after(350, self.start)

    def _build(self) -> None:
        if MARBLE.is_file():
            self.marble_source = Image.open(MARBLE).convert("RGB")
            texture = ImageOps.fit(self.marble_source, (760, 520), Image.Resampling.LANCZOS)
            self.marble_photo = ImageTk.PhotoImage(texture)
            self.background = tk.Label(self.root, image=self.marble_photo, borderwidth=0)
            self.background.place(x=0, y=0, relwidth=1, relheight=1)
            self.root.bind("<Configure>", self._schedule_responsive_layout)
        title = tk.Label(self.root, text="J  A  R  V  I  S", font=("Georgia", 27, "bold"),
                         fg=GOLD_BRIGHT, bg=BLACK)
        title.pack(pady=(20, 1))
        tk.Label(self.root, text="P E R S O N A L   I N T E L L I G E N C E", font=("Segoe UI", 7),
                 fg=IVORY, bg=BLACK).pack(pady=(0, 4))
        self.status = tk.StringVar(value="OFFLINE")
        tk.Label(self.root, textvariable=self.status, font=("Segoe UI Semibold", 9),
                 fg=MUTED, bg=BLACK).pack(pady=(0, 13))

        card = tk.Frame(self.root, bg=PANEL, padx=22, pady=16, highlightthickness=1,
                        highlightbackground=GOLD)
        card.pack(fill="x", padx=28)
        tk.Label(card, text="YOU", font=("Segoe UI Semibold", 8), fg=GOLD, bg=PANEL).pack(anchor="w")
        self.heard = tk.StringVar(value="Say “Hey Jarvis” when the status is Ready.")
        self.heard_label = tk.Label(card, textvariable=self.heard, wraplength=675, justify="left",
                                    font=("Segoe UI", 12), fg=IVORY, bg=PANEL)
        self.heard_label.pack(anchor="w", pady=(4, 13))
        tk.Frame(card, bg="#332b1b", height=1).pack(fill="x", pady=(0, 12))
        tk.Label(card, text="JARVIS", font=("Segoe UI Semibold", 8), fg=GOLD_BRIGHT, bg=PANEL).pack(anchor="w")
        self.answer = tk.StringVar(value="Starting up…")
        self.answer_label = tk.Label(card, textvariable=self.answer, wraplength=675, justify="left",
                                     font=("Segoe UI", 12), fg=IVORY, bg=PANEL)
        self.answer_label.pack(anchor="w", pady=(4, 0))

        buttons = tk.Frame(self.root, bg=BLACK)
        buttons.pack(pady=14)
        self.start_button = tk.Button(buttons, text="Start", width=12, command=self.start,
                                      bg=GOLD, fg=BLACK, activebackground=GOLD_BRIGHT,
                                      relief="flat", font=("Segoe UI Semibold", 9), cursor="hand2")
        self.start_button.pack(side="left", padx=6)
        self.stop_button = tk.Button(buttons, text="Stop", width=12, command=self.stop,
                                     bg=BLACK, fg=IVORY, activebackground="#201b12",
                                     highlightthickness=1, highlightbackground=GOLD,
                                     relief="flat", font=("Segoe UI", 9), cursor="hand2")
        self.stop_button.pack(side="left", padx=6)
        tk.Button(buttons, text="Hide to tray", width=12, command=self.hide_window,
                  bg=BLACK, fg=IVORY, activebackground="#201b12",
                  highlightthickness=1, highlightbackground=GOLD,
                  relief="flat", font=("Segoe UI", 9), cursor="hand2").pack(side="left", padx=6)

        self.log = tk.Text(self.root, height=7, bg="#080808", fg=MUTED, insertbackground=GOLD,
                           highlightthickness=1, highlightbackground="#3a3020",
                           relief="flat", font=("Consolas", 9), state="disabled", padx=12, pady=9)
        self.log.pack(fill="both", expand=True, padx=28, pady=(0, 20))

    def _schedule_responsive_layout(self, event) -> None:
        if event.widget is not self.root:
            return
        if self.resize_job is not None:
            self.root.after_cancel(self.resize_job)
        self.resize_job = self.root.after(90, self._apply_responsive_layout)

    def _apply_responsive_layout(self) -> None:
        self.resize_job = None
        width = max(1, self.root.winfo_width())
        height = max(1, self.root.winfo_height())
        if hasattr(self, "marble_source"):
            texture = ImageOps.fit(self.marble_source, (width, height), Image.Resampling.LANCZOS)
            self.marble_photo = ImageTk.PhotoImage(texture)
            self.background.configure(image=self.marble_photo)
        wrap = max(500, width - 85)
        self.heard_label.configure(wraplength=wrap)
        self.answer_label.configure(wraplength=wrap)

    @staticmethod
    def _smallest_monitor() -> dict:
        with mss.mss() as capture:
            monitors = list(capture.monitors[1:])
        return min(monitors, key=lambda item: item["width"] * item["height"])

    def _build_transcript_popup(self) -> None:
        """Pin a clean transcript overlay to the smallest connected display."""
        monitor = self._smallest_monitor()
        width, height, margin = 390, 118, 18
        x = monitor["left"] + monitor["width"] - width - margin
        y = monitor["top"] + monitor["height"] - height - margin

        self.popup = tk.Toplevel(self.root)
        self.popup.title("Jarvis transcript")
        self.popup.geometry(f"{width}x{height}+{x}+{y}")
        self.popup.configure(bg=BLACK)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)
        self.popup.attributes("-alpha", 0.94)
        tk.Frame(self.popup, bg=GOLD, width=4).pack(side="left", fill="y")
        body = tk.Frame(self.popup, bg=BLACK, padx=14, pady=11,
                        highlightthickness=1, highlightbackground="#3a3020")
        body.pack(side="left", fill="both", expand=True)
        self.popup_status = tk.StringVar(value="JARVIS · STARTING")
        tk.Label(body, textvariable=self.popup_status, font=("Segoe UI Semibold", 9),
                 fg=GOLD_BRIGHT, bg=BLACK).pack(anchor="w")
        self.popup_text = tk.StringVar(value="Waiting for “Hey Jarvis”…")
        tk.Label(body, textvariable=self.popup_text, wraplength=345, justify="left",
                 font=("Segoe UI", 12), fg=IVORY, bg=BLACK).pack(anchor="w", pady=(7, 0))
        self.popup.bind("<Button-1>", lambda _event: self.show_window())

    def _create_tray(self) -> None:
        if pystray is None:
            return
        image = Image.new("RGBA", (64, 64), BLACK)
        draw = ImageDraw.Draw(image)
        draw.ellipse((5, 5, 59, 59), outline=GOLD, width=5)
        draw.ellipse((25, 25, 39, 39), fill=GOLD_BRIGHT)
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
        colors = {"READY": GOLD_BRIGHT, "LISTENING": IVORY, "THINKING": GOLD,
                  "STARTING": GOLD, "OFFLINE": MUTED}
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("textvariable") == str(self.status):
                widget.configure(fg=colors.get(value, GOLD))

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
