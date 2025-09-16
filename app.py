# app.py — Windows only
import os
import sys
import ctypes
from ctypes import wintypes
import requests
from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from dotenv import load_dotenv
import webbrowser



# WinAPI constants
user32 = ctypes.windll.user32
MOD_NONE = 0
VK_F9 = 0x78  # F9 key
WM_HOTKEY = 0x0312
HOTKEY_ID = 1  # arbitrary id for the hotkey


def resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# --- Flask app setup ---
if getattr(sys, 'frozen', False):
    exe_dir = os.path.dirname(sys.executable)
else:
    exe_dir = os.path.abspath(".")

# Ensure .env file path
env_path = resource_path(os.path.join(exe_dir, ".env"))

# Load the environment variables from the .env file
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    print(f"[WARN] .env file not found at {env_path}")

backend_host = os.getenv("BACKEND_HOST", "http://127.0.0.1:5000")


# ctypes structs to read native MSG
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd",    wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam",  wintypes.WPARAM),
        ("lParam",  wintypes.LPARAM),
        ("time",    wintypes.DWORD),
        ("pt",      POINT),
    ]


class WinHotkeyFilter(QtCore.QAbstractNativeEventFilter):
    """Catch the F9 hotkey and toggle the input window."""
    def __init__(self, window):
        super().__init__()
        self.window = window

    def nativeEventFilter(self, event_type, message):
        if event_type == b"windows_generic_MSG":
            try:
                msg = ctypes.cast(int(message), ctypes.POINTER(MSG)).contents
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:

                    QtCore.QMetaObject.invokeMethod(
                        self.window, "toggle_visibility", QtCore.Qt.ConnectionType.QueuedConnection
                    )
                    return True, 0
            except Exception as e:
                print("nativeEventFilter error:", e)
        return False, 0


class DescriptionTextEdit(QtWidgets.QTextEdit):
    enterPressed = QtCore.Signal()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            if event.modifiers() == QtCore.Qt.NoModifier:
                # Enter → submit
                self.enterPressed.emit()
                # Stop propagation so a newline is not inserted
                return
        super().keyPressEvent(event)


class InputWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hotkey Input")
        self.setGeometry(600, 300, 400, 250)

        layout = QtWidgets.QVBoxLayout(self)

        # Category input (single-line)
        self.input1 = QtWidgets.QLineEdit(self)
        self.input1.setPlaceholderText("Category")
        self.input1.returnPressed.connect(self.submit)

        # Description input (multiline)
        self.input2 = DescriptionTextEdit(self)
        self.input2.setPlaceholderText("Description (multiline)")
        self.input2.enterPressed.connect(self.submit)

        # Submit button
        self.submit_btn = QtWidgets.QPushButton("Submit", self)
        self.submit_btn.clicked.connect(self.submit)

        layout.addWidget(self.input1)
        layout.addWidget(self.input2)
        layout.addWidget(self.submit_btn)

    @QtCore.Slot()
    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

            # Force focus with WinAPI
            hwnd = int(self.winId())
            user32.ShowWindow(hwnd, 9)          # SW_RESTORE
            user32.SetForegroundWindow(hwnd)

            self.input1.setFocus()

    def keyPressEvent(self, event):
        # Only handle Escape globally
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    @QtCore.Slot()
    def submit(self):
        text1 = self.input1.text()
        text2 = self.input2.toPlainText()
        print(f"Submitted: {text1}, {text2}")

        try:
            req = requests.post(f"{backend_host}/submit", json={
                "category": text1,
                "description": text2
            })
            print(req.status_code, req.text)
        except Exception as e:
            print("POST request failed:", e)

            # Show an error message box
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Error")
            msg.setText("Failed to submit data to the backend!")
            msg.setInformativeText(str(e))  # optional: show exception details
            msg.exec()

        # Clear fields and hide
        self.input1.clear()
        self.input2.clear()
        self.hide()


def open_backend():
    webbrowser.open(backend_host)


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    icon_path = resource_path("tray_icon.png")
    icon = QIcon(icon_path)

    # Create the tray
    tray = QSystemTrayIcon()
    tray.setIcon(icon)
    tray.setVisible(True)

    # Show balloon tip after startup
    tray.showMessage(
        "App Started",
        f"Backend: {backend_host}",
        QSystemTrayIcon.MessageIcon.Information,
        5000  # duration in ms
    )

    # Create the menu
    menu = QMenu()

    backend_info_action = QAction(f"{backend_host}")
    backend_info_action.setDisabled(True)
    menu.addAction(backend_info_action)

    backend_open_action = QAction(f"Open Backend")
    backend_open_action.triggered.connect(open_backend)
    menu.addAction(backend_open_action)

    menu.addSeparator()

    # Add a Quit option to the menu.
    quit_action = QAction("Quit")
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    # Add the menu to the tray
    tray.setContextMenu(menu)

    window = InputWindow()
    window.hide()

    window.toggle_visibility()

    # Ensure a native handle exists for the widget
    hwnd = int(window.winId())

    # Register F9 hotkey (no modifiers)
    if not user32.RegisterHotKey(hwnd, HOTKEY_ID, MOD_NONE, VK_F9):
        err = ctypes.GetLastError()
        print(f"[ERROR] RegisterHotKey failed (error code: {err}).")
    else:
        filt = WinHotkeyFilter(window)
        app.installNativeEventFilter(filt)
        print("[OK] Hotkey F9 registered. Press to toggle the input window.")

        # Cleanup on exit
        def cleanup():
            user32.UnregisterHotKey(hwnd, HOTKEY_ID)
        app.aboutToQuit.connect(cleanup)

    try:
        test = requests.head(url=backend_host)
    except Exception as e:
        print("POST request failed:", e)

        # Show an error message box
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Error")
        msg.setText("Failed to submit data to the backend!")
        msg.setInformativeText(str(e))  # optional: show exception details
        msg.exec()
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
