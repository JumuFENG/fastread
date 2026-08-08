import win32serviceutil
import win32service
import win32event
import subprocess
import sys
import os
import time

_service_name = "fastread"
_service_display_name = "FastRead"
_service_description = "FastRead 阅读后台服务"


class FastReadService(win32serviceutil.ServiceFramework):
    _svc_name_ = _service_name
    _svc_display_name_ = _service_display_name
    _svc_description_ = _service_description

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.process = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(10)
            except Exception:
                self.process.kill()

    def SvcDoRun(self):
        svc_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(svc_dir)
        os.chdir(project_dir)

        log_dir = os.path.join(project_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = open(os.path.join(log_dir, "service.log"), "a")

        while True:
            rc = win32event.WaitForSingleObject(self.hWaitStop, 1000)
            if rc == win32event.WAIT_OBJECT_0:
                break

            if self.process is None or self.process.poll() is not None:
                python_exe = sys.executable
                if os.path.basename(python_exe).lower() == "pythonservice.exe":
                    python_exe = os.path.join(sys.exec_prefix, "python.exe")
                self.process = subprocess.Popen(
                    [python_exe, "-u", os.path.join(project_dir, "main.py")],
                    cwd=project_dir,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
                time.sleep(5)

        if self.process and self.process.poll() is None:
            self.process.terminate()
        log_file.close()


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(FastReadService)
