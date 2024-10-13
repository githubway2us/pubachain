import win32serviceutil
import win32service
import win32event
import servicemanager
import subprocess
import time
import logging

# ตั้งค่าการบันทึก log
logging.basicConfig(filename='E:\\job\\geo\\daemon.log', level=logging.INFO)


class PythonService(win32serviceutil.ServiceFramework):
    _svc_name_ = "MyPythonService"
    _svc_display_name_ = "My Python Service"
    _svc_description_ = "This service runs blockchain.py, app.py, and database.py."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ''))
        self.main()

    def main(self):
        # เปิดโหนด
        logging.info('Starting nodes...')
        subprocess.Popen(['python', 'blockchain.py'])
        subprocess.Popen(['python', 'app.py'])
        subprocess.Popen(['python', 'database.py'])

        while self.running:
            logging.info('Service is running...')
            time.sleep(10)  # รอ 10 วินาทีก่อนที่จะทำงานซ้ำ

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(PythonService)
