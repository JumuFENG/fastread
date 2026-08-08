import sys
import os
import re
import subprocess
import shutil

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QProgressBar, QTextEdit, QCheckBox,
    QFileDialog, QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QFont

SERVICE_NAME = "fastread"
SHORTCUT_NAME = "FastRead.lnk"


def resource_path(path):
    try:
        base = sys._MEIPASS
    except AttributeError:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, path)


def app_version():
    try:
        sys.path.insert(0, os.path.join(resource_path("."), "app"))
        from lofig import VERSION
        return VERSION
    except Exception:
        return "1.0.0"


def default_install_dir():
    la = os.environ.get("LOCALAPPDATA",
                        os.path.join(os.path.expanduser("~"), "AppData", "Local"))
    return os.path.join(la, "fastread")


def detect_installed():
    r = subprocess.run(
        ["sc", "qc", SERVICE_NAME],
        capture_output=True, text=True,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    if r.returncode != 0:
        return None

    svc_exe = None
    for line in (r.stdout or "").splitlines():
        if not line.strip().startswith("BINARY_PATH_NAME"):
            continue
        quoted = re.findall(r'"([^"]*pythonservice\.exe)"', line.partition(":")[2].strip(), re.IGNORECASE)
        if quoted:
            svc_exe = quoted[0]

    if svc_exe:
        python_exe = os.path.join(os.path.dirname(svc_exe), "python.exe")
        ps = subprocess.run(
            ["powershell", "-NoProfile",
             "-Command",
              'Get-CimInstance Win32_Process -Filter "name=\'python.exe\'" | Select-Object -ExpandProperty CommandLine'],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if ps.returncode == 0:
            for cmdline in (ps.stdout or "").splitlines():
                m = re.search(r'-u\s+"?([^"\s]+\\main\.py)', cmdline.strip())
                if m and os.path.isfile(m.group(1)):
                    return os.path.dirname(m.group(1))

    default = default_install_dir()
    if os.path.isdir(os.path.join(default, "scripts")):
        return default
    return None


class _RunMixin:
    @staticmethod
    def _run(*args, **kwargs):
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
        kwargs.setdefault("capture_output", True)
        kwargs.setdefault("text", True)
        return subprocess.run(*args, **kwargs)


class InstallWorker(QThread, _RunMixin):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, install_dir, with_service):
        super().__init__()
        self.install_dir = install_dir
        self.with_service = with_service
        self.python_path = None

    def run(self):
        try:
            self.progress_signal.emit(5)
            self.log_signal.emit("检查 Python...")
            self.python_path = self._ensure_python()

            self.progress_signal.emit(20)
            self.log_signal.emit("部署程序文件...")
            self._deploy_files()

            self.progress_signal.emit(40)
            self.log_signal.emit("安装 Python 依赖...")
            self._install_deps(self.python_path)

            if self.with_service:
                self.progress_signal.emit(60)
                self.log_signal.emit("注册开机启动服务...")
                self._install_service(self.python_path)
                self._start_service()
            else:
                self.progress_signal.emit(60)
                self.log_signal.emit("已跳过后台服务注册（未勾选开机自启）")

            self.progress_signal.emit(85)
            self.log_signal.emit("创建桌面快捷方式...")
            self._create_shortcut(self.python_path)

            self.progress_signal.emit(100)
            self.log_signal.emit("安装完成！")
            self.finished_signal.emit(True, "安装完成")
        except Exception as e:
            self.log_signal.emit(f"错误: {e}")
            self.finished_signal.emit(False, str(e))

    def _ensure_python(self):
        r = self._run(["python", "-c",
                       "import sys; print(sys.executable);"
                       " exit(0 if sys.version_info >= (3,10) else 1)"])
        if r.returncode != 0:
            raise RuntimeError(
                "未找到 Python 3.10+（或版本过低）。\n"
                "请到 https://www.python.org/downloads/ 安装并勾选 Add to PATH 后重试。"
            )
        return r.stdout.strip()

    def _deploy_files(self):
        dst = self.install_dir
        os.makedirs(dst, exist_ok=True)

        src = resource_path(".")
        shutil.copy2(os.path.join(src, "main.py"), os.path.join(dst, "main.py"))
        shutil.copy2(os.path.join(src, "desktop.py"), os.path.join(dst, "desktop.py"))

        for d in ("app", "templates", "static"):
            s = os.path.join(src, d)
            if os.path.isdir(s):
                shutil.copytree(s, os.path.join(dst, d), dirs_exist_ok=True)

        scripts_dst = os.path.join(dst, "scripts")
        os.makedirs(scripts_dst, exist_ok=True)
        shutil.copy2(os.path.join(src, "scripts", "win_service.py"),
                     os.path.join(scripts_dst, "win_service.py"))

        res_dst = os.path.join(dst, "res")
        os.makedirs(res_dst, exist_ok=True)
        for icon in ("icon.ico", "icon.png"):
            icon_src = os.path.join(src, "res", icon)
            if os.path.isfile(icon_src):
                shutil.copy2(icon_src, os.path.join(res_dst, icon))

        req_src = os.path.join(src, "requirements.txt")
        if os.path.isfile(req_src):
            shutil.copy2(req_src, os.path.join(dst, "requirements.txt"))

        for d in ("config", "logs", "data", "sources"):
            os.makedirs(os.path.join(dst, d), exist_ok=True)
        self.log_signal.emit(f"  已部署到 {dst}")

    def _install_deps(self, python_path):
        self._run(
            [python_path, "-m", "pip", "install",
             "-r", os.path.join(self.install_dir, "requirements.txt")],
            check=True,
        )
        self.log_signal.emit("  requirements.txt ✓")

        self._run([python_path, "-m", "pip", "install", "pywin32"], check=True)
        self.log_signal.emit("  pywin32 ✓")

        self._run([python_path, "-m", "pip", "install", "PyQt6", "PyQt6-WebEngine"],
                  check=True)
        self.log_signal.emit("  PyQt6 / PyQt6-WebEngine ✓（桌面界面）")

    def _install_service(self, python_path):
        svc = os.path.join(self.install_dir, "scripts", "win_service.py")
        self._run([python_path, svc, "install"],
                  cwd=self.install_dir, check=True)
        self._run(["sc", "config", SERVICE_NAME, "start=auto"], check=True)
        self.log_signal.emit("  服务已注册 (开机自启)")

    def _start_service(self):
        r = self._run(["net", "start", SERVICE_NAME])
        if r.returncode != 0 and "already" not in (r.stdout + r.stderr).lower():
            raise RuntimeError(f"服务启动失败:\n{(r.stdout or '') + (r.stderr or '')}")
        self.log_signal.emit("  服务已启动")

    def _create_shortcut(self, python_path):
        pythonw = os.path.join(os.path.dirname(python_path), "pythonw.exe")
        script = os.path.join(self.install_dir, "desktop.py")
        ps = (
            "$ws = New-Object -ComObject WScript.Shell;"
            "$s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\\" + SHORTCUT_NAME + "');"
            f"$s.TargetPath = '{pythonw}';"
            f"$s.Arguments = '{script}';"
            f"$s.WorkingDirectory = '{self.install_dir}';"
            f"$s.IconLocation = '{os.path.join(self.install_dir, 'res', 'icon.ico')}';"
            "$s.Save()"
        )
        self._run(["powershell", "-NoProfile", "-Command", ps], check=True)
        self.log_signal.emit("  桌面快捷方式已创建")


class UninstallWorker(QThread, _RunMixin):
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, install_dir):
        super().__init__()
        self.install_dir = install_dir

    def run(self):
        try:
            self.progress_signal.emit(10)
            self.log_signal.emit("停止服务...")
            self._stop_service()

            self.progress_signal.emit(40)
            self.log_signal.emit("删除服务...")
            self._delete_service()

            self.progress_signal.emit(60)
            self.log_signal.emit("删除桌面快捷方式...")
            self._delete_shortcut()

            self.progress_signal.emit(80)
            self.log_signal.emit("删除程序文件...")
            self._delete_files()

            self.progress_signal.emit(100)
            self.log_signal.emit("卸载完成！")
            self.finished_signal.emit(True, "卸载完成")
        except Exception as e:
            self.log_signal.emit(f"错误: {e}")
            self.finished_signal.emit(False, str(e))

    def _stop_service(self):
        r = self._run(["sc", "query", SERVICE_NAME])
        if "running" in (r.stdout or "").lower():
            self._run(["net", "stop", SERVICE_NAME])
            self.log_signal.emit("  服务已停止")
        else:
            self.log_signal.emit("  服务未运行")

    def _delete_service(self):
        self._run(["sc", "delete", SERVICE_NAME])
        self.log_signal.emit("  服务已删除")

    def _delete_shortcut(self):
        ps = (
            "$s = [Environment]::GetFolderPath('Desktop') + '\\" + SHORTCUT_NAME + "';"
            "if (Test-Path $s) { Remove-Item $s }"
        )
        self._run(["powershell", "-NoProfile", "-Command", ps])
        self.log_signal.emit("  桌面快捷方式已删除")

    def _delete_files(self):
        if os.path.isdir(self.install_dir):
            shutil.rmtree(self.install_dir)
            self.log_signal.emit(f"  {self.install_dir} 已删除")
        else:
            self.log_signal.emit("  目录不存在，跳过")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.installed_dir = detect_installed()
        self.worker = None
        self.mode = "uninstall" if self.installed_dir else "install"

        self.setWindowTitle(f"FastRead 卸载 v{app_version()}" if self.installed_dir else f"FastRead 安装程序 v{app_version()}")
        self.setFixedSize(600, 460)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("FastRead 卸载" if self.installed_dir else "FastRead 安装")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        if self.installed_dir:
            desc_text = (
                f"检测到已安装在：\n{self.installed_dir}\n\n"
                "将停止并删除服务、删除程序文件和桌面快捷方式。"
            )
        else:
            desc_text = (
                "将程序文件部署到本地，并在桌面创建指向 FastRead 的快捷方式。\n"
                "双击桌面快捷方式即可使用。"
            )
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        hl = QHBoxLayout()
        hl.addWidget(QLabel("安装目录:" if not self.installed_dir else "安装位置:"))
        self.path_edit = QLineEdit(self.installed_dir or default_install_dir())
        if self.installed_dir:
            self.path_edit.setReadOnly(True)
        hl.addWidget(self.path_edit)
        if not self.installed_dir:
            browse_btn = QPushButton("浏览...")
            browse_btn.clicked.connect(self._browse)
            hl.addWidget(browse_btn)
        layout.addLayout(hl)

        self.auto_service = QCheckBox("注册开机启动服务")
        self.auto_service.setChecked(False)
        layout.addWidget(self.auto_service)

        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_area)

        self.btn = QPushButton("卸载" if self.installed_dir else "安装")
        self.btn.setFixedHeight(36)
        if self.installed_dir:
            self.btn.setStyleSheet("background-color: #c0392b; color: white;")
        self.btn.clicked.connect(self._start)
        layout.addWidget(self.btn)

        self.setCentralWidget(central)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "选择安装目录")
        if d:
            self.path_edit.setText(os.path.join(d, "fastread"))

    def _start(self):
        if self.mode == "uninstall":
            self._start_uninstall()
        else:
            self._start_install()

    def _start_install(self):
        install_dir = self.path_edit.text().strip()
        if not install_dir:
            QMessageBox.warning(self, "提示", "请选择安装目录")
            return
        if os.path.basename(install_dir).lower() != "fastread":
            install_dir = os.path.join(install_dir, "fastread")
            self.path_edit.setText(install_dir)

        self._begin(InstallWorker(install_dir, self.auto_service.isChecked()))

    def _start_uninstall(self):
        reply = QMessageBox.question(
            self, "确认卸载",
            f"确定要卸载 FastRead 吗？\n\n{self.installed_dir}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._begin(UninstallWorker(self.installed_dir))

    def _begin(self, worker):
        self.btn.setEnabled(False)
        self.btn.setText("处理中...")
        self.log_area.clear()
        self.progress.setValue(0)

        self.worker = worker
        self.worker.log_signal.connect(self.log_area.append)
        self.worker.progress_signal.connect(self.progress.setValue)
        self.worker.finished_signal.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, success, msg):
        self.btn.setEnabled(True)
        if success:
            if self.mode == "uninstall":
                self.btn.setText("完成")
                self.btn.setStyleSheet("")
                self.btn.clicked.disconnect()
                self.btn.clicked.connect(QApplication.quit)
            else:
                self.btn.setText("打开 FastRead")
                self.btn.clicked.disconnect()
                pythonw = os.path.join(os.path.dirname(self.worker.python_path), "pythonw.exe")
                script = os.path.join(self.path_edit.text().strip(), "desktop.py")
                self.btn.clicked.connect(
                    lambda: (subprocess.Popen([pythonw, script], cwd=self.path_edit.text().strip()),
                             QApplication.quit()))
        else:
            self.btn.setText("重试")
            self.btn.clicked.disconnect()
            self.btn.clicked.connect(self._start)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
