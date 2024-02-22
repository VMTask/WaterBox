import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
import os

class realtime_CommandExecuter(QThread):
    sig = pyqtSignal(str)
    
    def __init__(self, command, parent=None):
        super(realtime_CommandExecuter, self).__init__(parent)
        self.command = command
    
    def run(self):
        output=""
        p = subprocess.Popen(self.command, stdout=subprocess.PIPE,encoding="utf-8",stderr=subprocess.STDOUT)
        for line in iter(p.stdout.readline, ""):
            output += line
            self.sig.emit(output)
        self.sig.emit("finished")
        
class CommandExecuter(QThread):
    sig = pyqtSignal(str)
    def __init__(self, command, parent=None):
        super(CommandExecuter, self).__init__(parent)
        self.command = command
    
    def run(self):
        proc = subprocess.Popen(self.command, stdout=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
        output, _ = proc.communicate()
        decoded_output = output.decode()  # 假设输出为UTF-8编码，根据实际情况选择解码方式

        self.sig.emit(decoded_output)
        
class InstallApp(QThread):
    sig = pyqtSignal(str)
    int_sig = pyqtSignal(int)
    def __init__(self,urls,parent=None):
        super(InstallApp,self).__init__(parent)
        self.urls = urls
    
    def run(self):
        self.sig.emit("Start Installing......")
        count = 0
        for url in self.urls:
            count += 1
            self.int_sig.emit(count)
            self.sig.emit("Processing......")
            output=""
            command = f'{os.getcwd()}/adb_executable/adb.exe install -r {url}'
            p = subprocess.Popen(command, stdout=subprocess.PIPE,encoding="utf-8",stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
            for line in iter(p.stdout.readline, ""):
                output += line
                self.sig.emit(output)
        self.sig.emit("Installed")