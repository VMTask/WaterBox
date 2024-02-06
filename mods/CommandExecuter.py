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
        output = os.popen(self.command).read()
        self.sig.emit(output)