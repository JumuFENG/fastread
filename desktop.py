#!/usr/bin/env python3
"""
FastRead 桌面版: 若服务未启动则自带启动 FastAPI 服务, 再用 Qt WebView 打开界面。
"""

import os
import socket
import sys
import threading

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtGui import QDesktopServices, QIcon

from main import app
from app.lofig import Config

PORT = Config.client_config().get("port", 8777)
LOCAL_ORIGIN = f"http://127.0.0.1:{PORT}/"


def load_icon() -> QIcon:
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'res', 'icon.png')
    return QIcon(p) if os.path.isfile(p) else QIcon()


def server_running():
    try:
        with socket.create_connection(("127.0.0.1", PORT), timeout=0.5):
            return True
    except OSError:
        return False


def run_server():
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_config=None, access_log=False)


class AppPage(QWebEnginePage):
    def __init__(self, view):
        super().__init__(view)
        self._view = view

    def acceptNavigationRequest(self, url, _type, _isMainFrame):
        if not url.toString().startswith(LOCAL_ORIGIN):
            QDesktopServices.openUrl(url)
            return False
        return True

    def createWindow(self, _type):
        page = AppPage(self._view)
        page.urlChanged.connect(lambda u: QDesktopServices.openUrl(u))
        return page


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastRead")
        self.setWindowIcon(load_icon())
        self.setGeometry(100, 100, 1200, 800)
        view = QWebEngineView()
        page = AppPage(view)
        view.setPage(page)
        self.setCentralWidget(view)
        if not server_running():
            threading.Thread(target=run_server, daemon=True).start()
        view.setUrl(QUrl(f"http://127.0.0.1:{PORT}/"))


def main():
    qt_app = QApplication(sys.argv)
    qt_app.setWindowIcon(load_icon())
    window = MainWindow()
    window.show()
    handle = window.windowHandle()
    if handle is not None:
        handle.setIcon(qt_app.windowIcon())
    qt_app.exec()


if __name__ == "__main__":
    main()
