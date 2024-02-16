import sys
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QTextEdit, QPushButton, QWidget
from PyQt5.QtCore import QProcess, Qt

class CmdTerminal(QWidget):
    def __init__(self):
        super().__init__()

        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.on_ready_read)

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)

        self.button = QPushButton('Execute', self)
        self.button.clicked.connect(self.execute_command)

        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        layout.addWidget(self.button)

    def execute_command(self):
        cmd = "your command here"  # 输入你的命令
        self.process.start('cmd.exe', [' /c', cmd])  # 在Windows系统下执行命令
        # 在Linux系统下执行命令，可以改为：self.process.start('bash', ['-c', cmd])

    def on_ready_read(self):
        text = str(self.process.readAllStandardOutput(), encoding='utf-8')
        self.text_edit.append(text)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    terminal = CmdTerminal()
    terminal.show()

    sys.exit(app.exec_())