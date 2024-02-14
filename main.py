# coding:utf-8
import json
import os
import sys
import re
import time
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal, pyqtSlot, QSize, QEventLoop, QTimer
from PyQt5.QtGui import QIcon, QDesktopServices, QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QListWidgetItem, QWidget, QLabel
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont, SplashScreen,setThemeColor)
from qfluentwidgets import FluentIcon as FIF
from resources import main_rc
from interface import HomeActivity, RestartADB, FileActivity, Waiting
from datetime import datetime
import asyncio
from typing import Union
from mods import asyncadb, CommandExecuter
device_name_list = []



ifAdbOK = False

class ADBWaiter(QThread):
    sig = pyqtSignal(dict)
    error_sig = pyqtSignal(str)

    def __init__(self, parent=None):
        super(ADBWaiter, self).__init__(parent)

    async def wait_track_devices(self):
        waiter = asyncadb.AdbClient()
        try:
            async for event in waiter.track_devices():
                time.sleep(0.1)
                if not isinstance(event,str):
                    self.sig.emit({
                        "app":"working",
                        "serial":event.serial,
                        "status":event.status,
                        "present":event.present
                    })
                else:
                    self.error_sig.emit(event)
        except Exception as err:
            self.sig.emit({
                "app":"crash",
                "error":str(err)
            })
    def run(self):
        asyncio.run(self.wait_track_devices())

class HomeWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        # init HomeActivity object
        self.ui = HomeActivity.Ui_Frame()
        current_time = datetime.now()
        hour = current_time.hour

        # 调用setupUi()方法，将其内容应用到当前的QFrame上
        self.ui.setupUi(self)
        self.setObjectName("Home")
        if 5 <= hour < 12:
            self.ui.IconWidget.setIcon(QIcon(":/images/morning.png"))
            self.ui.LargeTitleLabel.setText(f"Good Mornning,Welcome Back.")
        elif 12 <= hour < 18:
            self.ui.IconWidget.setIcon(QIcon(":/images/afternoon.png"))
            self.ui.LargeTitleLabel.setText(f"Good Afternoon,Welcome Back.")
        elif 18 <= hour < 21:
            self.ui.IconWidget.setIcon(QIcon(":/images/night.png"))
            self.ui.LargeTitleLabel.setText(f"Good Evening,Welcome Back.")
        else:
            self.ui.IconWidget.setIcon(QIcon(":/images/night.png"))
            self.ui.LargeTitleLabel.setText(f"Good Night,Welcome Back.")
        self.ui.ComboBox.addItems(device_name_list)
        self.ui.ComboBox.setDisabled(True)
        self.ui.ComboBox.setText("(未连接)")
        self.ui.ComboBox.currentTextChanged.connect(self.onComboBoxTextChanged)



    def getModelThread_response(self,data:str):
        lines = data.split('\n')  # 将字符串按换行符分割成列表
        non_empty_lines = [line for line in lines if line.strip()]  # 使用列表推导式仅保留非空行
        result = '\n'.join(non_empty_lines)  # 用换行符重新连接非空行
        self.ui.StrongBodyLabel_4.setText(result)

    def getBatteryThread_response(self,data:str):
        self.ui.ProgressBar.setValue(int(data.replace("level:","")))
    def getManufacturerThread_response(self,data:str):
        lines = data.split('\n')  # 将字符串按换行符分割成列表
        non_empty_lines = [line for line in lines if line.strip()]  # 使用列表推导式仅保留非空行
        result = '\n'.join(non_empty_lines)  # 用换行符重新连接非空行
        self.ui.StrongBodyLabel_6.setText(result)
    def onComboBoxTextChanged(self):
        self.getModelThread = CommandExecuter.CommandExecuter(f".\\adb_executable\\adb -s {self.ui.ComboBox.currentText()} shell getprop ro.product.model")
        self.getModelThread.sig.connect(self.getModelThread_response)
        self.getModelThread.wait()
        self.getModelThread.start()
        self.getBatteryThread = CommandExecuter.CommandExecuter(f".\\adb_executable\\adb -s {self.ui.ComboBox.currentText()} shell dumpsys battery | findstr level")
        self.getBatteryThread.sig.connect(self.getBatteryThread_response)
        self.getBatteryThread.wait()
        self.getBatteryThread.start()
        self.getManufacturerThread = CommandExecuter.CommandExecuter(f".\\adb_executable\\adb -s {self.ui.ComboBox.currentText()} shell getprop ro.product.manufacturer")
        self.getManufacturerThread.sig.connect(self.getManufacturerThread_response)
        self.getManufacturerThread.wait()
        self.getManufacturerThread.start()


class FileWidget(QFrame):
    nowdir = ""
    nofirst = 0
    def __init__(self, parent=None):
        global ifAdbOK
        super().__init__(parent=parent)
        self.ui = FileActivity.Ui_Frame()
        self.ui.setupUi(self)
        self.setObjectName("App")
        self.loadFile()
        #if str(os.popen('adb shell').read().splitlines()) != "adb.exe: no devices/emulators found":
        self.ui.pushButton.clicked.connect(lambda: self.goBack())   # 返回按键
        self.ui.pushButton_2.clicked.connect(lambda: self.goRoot())     # 回根目录按键
        self.ui.pushButton_3.clicked.connect(lambda: self.goDir())    # 访问指定文件夹按键


    def loadFile(self):
        global nowdir
        nowdir = ""
        self.ui.lineEdit.setText("/")
        result = os.popen('adb shell ls 2>&1')
        res = result.buffer.read().decode("utf-8")
        result.close()
        if res.splitlines() == ['adb.exe: no devices/emulators found']:     # 判断ADB是否连接
            pass
        else:
            for line in res.splitlines():
                if line == "* daemon not running; starting now at tcp:5037" or line == "* daemon started successfully" or line == "adb.exe: no devices/emulators found":    # 过滤无效文件
                    pass
                else:
                    if line[0:4] == "ls: ":     # 修复某些要权限的文件夹
                        dir1 = line[4:str(line).rfind(": Permission denied")]
                        line = dir1[dir1.rfind("/") + 1:len(dir1)]
                    if str(line).rfind(" ") != -1:
                        line = line.replace(' ', r'\ ')
                    a = os.popen("adb shell cd " + "/" + line + " 2>&1")
                    b = a.buffer.read().decode('utf-8')
                    a.close()
                    if b == "" or b.rfind("/system/bin/sh: cd: /"+line+": Permission denied") != -1:
                        item = QListWidgetItem(QIcon('resources/icons/folder.png'), line)
                    else:
                        if line.rfind('.') != -1 and line.rfind('/') < line.rfind('.'):
                            suffix = line[line.rfind('.') + 1:len(line)].lower()
                            if suffix == "mp4" or suffix == "mpg" or suffix == "mpg" or suffix == "mpeg" or suffix == "avi" or suffix == "rm" or suffix == "dat" or suffix == "mpg" or suffix == "flv" or suffix == "mov" or suffix == "wmv":
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/video.png'), line)
                            elif suffix == "mp3" or suffix == "wma" or suffix == "wav" or suffix == "flac" or suffix == "ogg" or suffix == "aac" or suffix == "ape":
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/music.png'), line)
                            elif suffix == "apk":
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/apk.png'), line)
                            elif suffix == "txt" or suffix == "doc" or suffix == "docx" or suffix == "pdf" or suffix == "xml":
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/doc.png'), line)
                            else:
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                        else:
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                    self.ui.listWidget.addItem(item)
            # self.ui.listWidget.show()
            self.ui.listWidget.itemDoubleClicked.connect(self.show_select_item)


    def show_select_item(self, item):
        global nowdir
        # self.waiting()
        ls = item.text()
        if str(ls).rfind(" ") != -1:
            ls = ls.replace(' ', r'\ ')
        result = os.popen('adb shell ls \"' + nowdir +"/"+ ls +"\" 2>&1")
        print('adb shell ls \"' + nowdir +"/"+ ls +"\" 2>&1")
        res = result.buffer.read().decode("utf-8")
        result.close()
        print(res.splitlines())
        if res.splitlines() == ["ls: " + nowdir +"/"+ ls +": Permission denied"]:   # 权限不足，后续写获取root功能
            print("权限不足")
            title = "权限不足"
            content = "可能需要root权限"
            w = MessageBox(title, content, self)
            w.exec()
        elif res.splitlines() == ['adb.exe: no devices/emulators found']:   # ADB未连接
            title = "设备未连接"
            content = "请检查数据线是否插好或ADB是否开启"
            w = MessageBox(title, content, self)
            w.exec()
        else:
            if res.splitlines() == []:  # 空文件夹
                self.ui.listWidget.clear()
                nowdir = nowdir + "/" + ls
                if str(nowdir).rfind(r"\ ") != -1:
                    nowdir = nowdir.replace('\ ', ' ')
                self.ui.lineEdit.setText(nowdir)
            else:
                tmp = res.splitlines()[0]
                if str(tmp).rfind(" ") != -1:
                    tmp = tmp.replace(' ', r'\ ')
                print(nowdir + "/" + ls)
                if tmp == nowdir + "/" + ls or res.splitlines() == ['ls: '+nowdir + "/" + ls+': No such file or directory']:
                    getdir = nowdir + "/" + ls
                    if str(getdir).rfind(r'\ ') != -1:
                        getdir = getdir.replace(r'\ ', ' ')
                    suffix = getdir[getdir.rfind('.') + 1:len(getdir)].lower()
                    if suffix == "apk":
                        title = "apk安装"
                        content = "您要在设备上安装这个apk吗"
                        w = MessageBox(title, content, self)
                        if w.exec():
                            window = Waiting.WaitingWindow()
                            window.TitleLabel.setText("安装中...")
                            window.show()
                            QApplication.processEvents()
                            if str(getdir).rfind(' ') != -1:
                                getdir = getdir.replace(' ', r'\ ')
                            result = os.popen("adb shell pm install -r " + getdir +' 2>&1')
                            res = result.buffer.read().decode("utf-8")
                            result.close()
                            if res.splitlines() == ["Success"]:
                                window.close()
                                title = "安装成功"
                                content = "apk已安装"
                                w = MessageBox(title, content, self)
                                w.exec()
                            else:
                                window.close()
                                title = "安装失败"
                                content = "失败原因:" + str(res.splitlines())
                                w = MessageBox(title, content, self)
                                w.exec()
                    elif suffix == "txt":
                        folder_name = 'temp'
                        if not os.path.exists(folder_name):
                            os.makedirs(folder_name)
                        print("adb pull " + getdir + ' ' + os.path.split(os.path.realpath(sys.argv[0]))[
                            0] + '\\temp\\ 2>&1')
                        result = os.popen("adb pull " + getdir + ' ' + os.path.split(os.path.realpath(sys.argv[0]))[
                            0] + '\\temp\\ 2>&1')
                        res = result.buffer.read().decode("utf-8")
                        result.close()
                        print(res.splitlines())
                        if str(res.splitlines()).rfind("1 file pulled, 0 skipped.") != -1:
                            originalFile = open(os.path.split(os.path.realpath(sys.argv[0]))[0] + "\\temp\\" + ls,
                                                encoding = "utf-8")
                            original = []
                            for line in originalFile:
                                original.append(line.strip())
                            print(original)
                            exec = os.popen(
                                "notepad.exe " + os.path.split(os.path.realpath(sys.argv[0]))[0] + "\\temp\\" + ls)
                            exec.buffer.read().decode("utf-8")
                            exec.close()
                            print("程序关闭")
                            nowFile = open(os.path.split(os.path.realpath(sys.argv[0]))[0] + "\\temp\\" + ls,
                                           encoding="utf-8")
                            now = []
                            for line in nowFile:
                                now.append(line.strip())
                            print(now)
                            if original != now:
                                title = "检测到文件更改"
                                content = "是否将修改保存到设备"
                                w = MessageBox(title, content, self)
                                if w.exec():
                                    pushFile = os.popen(
                                        "adb push " + os.path.split(os.path.realpath(sys.argv[0]))[
                                            0] + '\\temp\\' + ls + ' ' + nowdir + ' 2>&1')
                                    getResult = pushFile.buffer.read().decode("utf-8")
                                    pushFile.close()
                                    if str(getResult.splitlines()).rfind("1 file pushed, 0 skipped.") != -1:
                                        title = "保存成功"
                                        content = "文件已保存到设备"
                                        w = MessageBox(title, content, self)
                                        w.exec()
                                    else:
                                        title = "保存失败"
                                        content = "失败原因:" + str(getResult.splitlines())
                                        w = MessageBox(title, content, self)
                                        w.exec()
                            else:
                                pass
                        else:
                            title = "下载文件失败"
                            content = "失败原因:" + str(res.splitlines())
                            w = MessageBox(title, content, self)
                            w.exec()
                    elif suffix == "mp3" or suffix == "wma" or suffix == "wav" or suffix == "flac" or suffix == "ogg" or suffix == "aac" or suffix == "ape" or suffix == "mp4" or suffix == "mpg" or suffix == "mpg" or suffix == "mpeg" or suffix == "avi" or suffix == "rm" or suffix == "dat" or suffix == "mpg" or suffix == "flv" or suffix == "mov" or suffix == "wmv":
                        folder_name = 'temp'
                        if not os.path.exists(folder_name):
                            os.makedirs(folder_name)
                        window = Waiting.WaitingWindow()
                        window.TitleLabel.setText("下载中...")
                        window.show()
                        QApplication.processEvents()
                        print("adb pull " + getdir + ' ' + os.path.split(os.path.realpath(sys.argv[0]))[
                            0] + '\\temp\\ 2>&1')
                        result = os.popen("adb pull " + getdir + ' ' + os.path.split(os.path.realpath(sys.argv[0]))[
                            0] + '\\temp\\ 2>&1')
                        res = result.buffer.read().decode("utf-8")
                        result.close()
                        print(res.splitlines())
                        window.close()
                        if str(res.splitlines()).rfind("1 file pulled, 0 skipped.") != -1:
                            os.system("start "+os.path.split(os.path.realpath(sys.argv[0]))[
                            0] + '\\temp\\' + ls)
                        else:
                            title = "下载文件失败"
                            content = "失败原因:" + str(res.splitlines())
                            w = MessageBox(title, content, self)
                            w.exec()
                else:
                    window = Waiting.WaitingWindow()
                    window.show()
                    QApplication.processEvents()
                    self.ui.listWidget.clear()
                    for line in res.splitlines():
                        if line[0:4] == "ls: ":
                            dir1 = line[4:str(line).rfind(": Permission denied")]
                            line = dir1[dir1.rfind("/")+1:len(dir1)]
                        print(line)
                        if str(line).rfind(" ") != -1:
                            line = line.replace(' ', r'\ ')
                        print(line)
                        a = os.popen("adb shell cd "+nowdir+"/"+ls+"/"+line+" 2>&1")
                        b = a.buffer.read().decode('utf-8', "ignore")
                        a.close()
                        # print("/system/bin/sh: cd: "+nowdir+"/"+ls+"/"+line+": Permission denied")
                        if b == "" or b.rfind("/system/bin/sh: cd: "+nowdir+"/"+ls+"/"+line+": Permission denied") != -1:
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/folder.png'), line)
                        else:
                            if line.rfind('.') != -1 and line.rfind('/') < line.rfind('.'):
                                suffix = line[line.rfind('.')+1:len(line)].lower()
                                if suffix == "mp4" or suffix == "mpg" or suffix == "mpg" or suffix == "mpeg" or suffix == "avi" or suffix == "rm" or suffix == "dat" or suffix == "mpg" or suffix == "flv" or suffix == "mov" or suffix == "wmv":
                                    if str(line).rfind(r"\ ") != -1:
                                        line = line.replace(r'\ ', ' ')
                                    item = QListWidgetItem(QIcon('resources/icons/video.png'), line)
                                elif suffix == "mp3" or suffix == "wma" or suffix == "wav" or suffix == "flac" or suffix == "ogg" or suffix == "aac" or suffix == "ape":
                                    if str(line).rfind(r"\ ") != -1:
                                        line = line.replace(r'\ ', ' ')
                                    item = QListWidgetItem(QIcon('resources/icons/music.png'), line)
                                elif suffix == "apk":
                                    if str(line).rfind(r"\ ") != -1:
                                        line = line.replace(r'\ ', ' ')
                                    item = QListWidgetItem(QIcon('resources/icons/apk.png'), line)
                                elif suffix == "txt" or suffix == "doc" or suffix == "docx" or suffix == "pdf" or suffix == "xml":
                                    if str(line).rfind(r"\ ") != -1:
                                        line = line.replace(r'\ ', ' ')
                                    item = QListWidgetItem(QIcon('resources/icons/doc.png'), line)
                                else:
                                    if str(line).rfind(r"\ ") != -1:
                                        line = line.replace(r'\ ', ' ')
                                    item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                            else:
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                        self.ui.listWidget.addItem(item)
                    nowdir = nowdir + "/" + ls
                    if str(nowdir).rfind(r"\ ") != -1:
                        nowdir = nowdir.replace(r'\ ', ' ')
                    self.ui.lineEdit.setText(nowdir)
                    window.close()

    def goBack(self):
        global nowdir
        if str(nowdir).rfind("/") == -1:
            pass
        elif str(nowdir).rfind("/") == 0:
            window = Waiting.WaitingWindow()
            window.show()
            QApplication.processEvents()
            nowdir = ""
            result = os.popen('adb shell ls ' + nowdir +' 2>&1')
            res = result.buffer.read().decode("utf-8")
            result.close()
            self.ui.listWidget.clear()
            for line in res.splitlines():
                if line[0:4] == "ls: ":
                    dir1 = line[4:str(line).rfind(": Permission denied")]
                    line = dir1[dir1.rfind("/") + 1:len(dir1)]
                if str(line).rfind(" ") != -1:
                    line = line.replace(' ', r'\ ')
                a = os.popen("adb shell cd " + "/" + line + " 2>&1")
                b = a.buffer.read().decode('utf-8')
                a.close()
                if b == "" or b.rfind("/system/bin/sh: cd: /"+line+": Permission denied") != -1:
                    if str(line).rfind(r"\ ") != -1:
                        line = line.replace(r'\ ', ' ')
                    item = QListWidgetItem(QIcon('resources/icons/folder.png'), line)
                else:
                    if line.rfind('.') != -1 and line.rfind('/') < line.rfind('.'):
                        suffix = line[line.rfind('.') + 1:len(line)].lower()
                        if suffix == "mp4" or suffix == "mpg" or suffix == "mpg" or suffix == "mpeg" or suffix == "avi" or suffix == "rm" or suffix == "dat" or suffix == "mpg" or suffix == "flv" or suffix == "mov" or suffix == "wmv":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/video.png'), line)
                        elif suffix == "mp3" or suffix == "wma" or suffix == "wav" or suffix == "flac" or suffix == "ogg" or suffix == "aac" or suffix == "ape":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/music.png'), line)
                        elif suffix == "apk":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/apk.png'), line)
                        elif suffix == "txt" or suffix == "doc" or suffix == "docx" or suffix == "pdf" or suffix == "xml":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/doc.png'), line)
                        else:
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                    else:
                        if str(line).rfind(r"\ ") != -1:
                            line = line.replace(r'\ ', ' ')
                        item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                self.ui.listWidget.addItem(item)
            self.ui.lineEdit.setText("/")
            window.close()
        else:
            window = Waiting.WaitingWindow()
            window.show()
            QApplication.processEvents()
            nowdir = nowdir[0: str(nowdir).rfind("/")]
            result = os.popen('adb shell ls ' + nowdir +" 2>&1")
            res = result.buffer.read().decode("utf-8")
            result.close()
            self.ui.listWidget.clear()
            for line in res.splitlines():
                if line[0:4] == "ls: ":
                    dir1 = line[4:str(line).rfind(": Permission denied")]
                    line = dir1[dir1.rfind("/") + 1:len(dir1)]
                if str(line).rfind(" ") != -1:
                    line = line.replace(' ', r'\ ')
                a = os.popen("adb shell cd " + nowdir + "/" + line + " 2>&1")
                b = a.buffer.read().decode('utf-8')
                a.close()
                if b == "" or b.rfind("/system/bin/sh: cd: /"+ nowdir + "/" + line +": Permission denied") != -1:
                    if str(line).rfind(r"\ ") != -1:
                        line = line.replace(r'\ ', ' ')
                    item = QListWidgetItem(QIcon('resources/icons/folder.png'), line)
                else:
                    if line.rfind('.') != -1 and line.rfind('/') < line.rfind('.'):
                        suffix = line[line.rfind('.') + 1:len(line)].lower()
                        if suffix == "mp4" or suffix == "mpg" or suffix == "mpg" or suffix == "mpeg" or suffix == "avi" or suffix == "rm" or suffix == "dat" or suffix == "mpg" or suffix == "flv" or suffix == "mov" or suffix == "wmv":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/video.png'), line)
                        elif suffix == "mp3" or suffix == "wma" or suffix == "wav" or suffix == "flac" or suffix == "ogg" or suffix == "aac" or suffix == "ape":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/music.png'), line)
                        elif suffix == "apk":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/apk.png'), line)
                        elif suffix == "txt" or suffix == "doc" or suffix == "docx" or suffix == "pdf" or suffix == "xml":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/doc.png'), line)
                        else:
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                    else:
                        if str(line).rfind(r"\ ") != -1:
                            line = line.replace(r'\ ', ' ')
                        item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                self.ui.listWidget.addItem(item)
            self.ui.lineEdit.setText(nowdir)
            window.close()


    def goRoot(self):
        global nowdir
        self.ui.listWidget.clear()
        nowdir = ""
        result = os.popen('adb shell ls 2>&1')
        res = result.buffer.read().decode("utf-8")
        result.close()
        if res.splitlines() == ['adb.exe: no devices/emulators found']:
            title = "设备未连接"
            content = "请检查数据线是否插好或ADB是否开启"
            w = MessageBox(title, content, self)
            w.exec()
        else:
            window = Waiting.WaitingWindow()
            window.show()
            QApplication.processEvents()
            for line in res.splitlines():
                if str(line).rfind(" ") != -1:
                    line = line.replace(' ', r'\ ')
                a = os.popen("adb shell cd " + "/" + line + " 2>&1")
                b = a.buffer.read().decode('utf-8')
                a.close()
                if b == "" or b.rfind("/system/bin/sh: cd: /"+line+": Permission denied") != -1:
                    item = QListWidgetItem(QIcon('resources/icons/folder.png'), line)
                else:
                    if line.rfind('.') != -1 and line.rfind('/') < line.rfind('.'):
                        suffix = line[line.rfind('.') + 1:len(line)].lower()
                        if suffix == "mp4" or suffix == "mpg" or suffix == "mpg" or suffix == "mpeg" or suffix == "avi" or suffix == "rm" or suffix == "dat" or suffix == "mpg" or suffix == "flv" or suffix == "mov" or suffix == "wmv":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/video.png'), line)
                        elif suffix == "mp3" or suffix == "wma" or suffix == "wav" or suffix == "flac" or suffix == "ogg" or suffix == "aac" or suffix == "ape":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/music.png'), line)
                        elif suffix == "apk":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/apk.png'), line)
                        elif suffix == "txt" or suffix == "doc" or suffix == "docx" or suffix == "pdf" or suffix == "xml":
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/doc.png'), line)
                        else:
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                    else:
                        if str(line).rfind(r"\ ") != -1:
                            line = line.replace(r'\ ', ' ')
                        item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                self.ui.listWidget.addItem(item)
            self.ui.lineEdit.setText("/")
            window.close()

    def goDir(self):
        global nowdir
        getdir = self.ui.lineEdit.text()
        if str(getdir).rfind(" ") != -1:
            getdir = getdir.replace(' ', r'\ ')
        result = os.popen('adb shell ls \"' + getdir +"\" 2>&1")
        res = result.buffer.read().decode("utf-8")
        result.close()
        if res.splitlines() == ["ls: " + getdir + ": No such file or directory"]:
            print("目录不存在")
            title = "目录不存在"
            content = "请检查输入是否正确"
            w = MessageBox(title, content, self)
            w.exec()
        elif res.splitlines() == ["ls: " + getdir + ": Permission denied"]:
            print("权限不足")
            title = "权限不足"
            content = "可能需要root权限"
            w = MessageBox(title, content, self)
            w.exec()
        elif res.splitlines() == ['adb.exe: no devices/emulators found']:
            title = "设备未连接"
            content = "请检查数据线是否插好或ADB是否开启"
            w = MessageBox(title, content, self)
            w.exec()
        else:
            if res.splitlines() == []:   # 空文件夹
                self.ui.listWidget.clear()
                nowdir = getdir
                self.ui.lineEdit.setText(nowdir)
            elif res.splitlines() == [getdir]:   # 打开文件
                pass
            else:
                window = Waiting.WaitingWindow()
                window.show()
                QApplication.processEvents()
                self.ui.listWidget.clear()
                for line in res.splitlines():
                    if line[0:4] == "ls: ":
                        dir1 = line[4:str(line).rfind(": Permission denied")]
                        line = dir1[dir1.rfind("/") + 1:len(dir1)]
                    if str(line).rfind(" ") != -1:
                        line = line.replace(' ', r'\ ')
                    a = os.popen("adb shell cd " + getdir + "/" + line + " 2>&1")
                    b = a.buffer.read().decode('utf-8')
                    a.close()
                    if b == "":
                        item = QListWidgetItem(QIcon('resources/icons/folder.png'), line)
                    else:
                        if line.rfind('.') != -1 and line.rfind('/') < line.rfind('.'):
                            suffix = line[line.rfind('.') + 1:len(line)].lower()
                            if suffix == "mp4" or suffix == "mpg" or suffix == "mpg" or suffix == "mpeg" or suffix == "avi" or suffix == "rm" or suffix == "dat" or suffix == "mpg" or suffix == "flv" or suffix == "mov" or suffix == "wmv":
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/video.png'), line)
                            elif suffix == "mp3" or suffix == "wma" or suffix == "wav" or suffix == "flac" or suffix == "ogg" or suffix == "aac" or suffix == "ape":
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/music.png'), line)
                            elif suffix == "apk":
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/apk.png'), line)
                            elif suffix == "txt" or suffix == "doc" or suffix == "docx" or suffix == "pdf" or suffix == "xml":
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/doc.png'), line)
                            else:
                                if str(line).rfind(r"\ ") != -1:
                                    line = line.replace(r'\ ', ' ')
                                item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                        else:
                            if str(line).rfind(r"\ ") != -1:
                                line = line.replace(r'\ ', ' ')
                            item = QListWidgetItem(QIcon('resources/icons/file.png'), line)
                    self.ui.listWidget.addItem(item)
                nowdir = getdir
                self.ui.lineEdit.setText(nowdir)
                window.close()


class Widget(QFrame):

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.label = SubtitleLabel(text, self)
        self.hBoxLayout = QHBoxLayout(self)

        setFont(self.label, 24)
        self.label.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self.label, 1, Qt.AlignCenter)
        self.setObjectName(text.replace(' ', '-'))


class Window(MSFluentWindow):
    def closeEvent(self, event):
        title = "确认要关闭窗口吗？"
        content = "关闭后会退出程序"
        w = MessageBox(title, content, self)
        w.yesButton.setText('狠心退出')
        w.cancelButton.setText('手滑了')
        if w.exec():
            event.accept()
            self.waiterThread.quit()
            RestartADBWindow.close()
            # os.system("taskkill /f /im adb.exe>nul")      可能要用
        else:
            event.ignore()
    def __init__(self):
        super().__init__()
        self.titleBar.maxBtn.hide()
        # create sub interface
        self.windowEffect.setAcrylicEffect(self.winId())
        self.homeInterface = HomeWidget(self)
        setThemeColor('#28afe9')
        self.fileInterface = FileWidget(self)
        self.appInterface = Widget('Application Interface', self)
        self.videoInterface = Widget('Video Interface', self)
        self.libraryInterface = Widget('library Interface', self)
        self.waiterThread = ADBWaiter()
        self.waiterThread.sig.connect(self.waiterProcessor)
        self.waiterThread.error_sig.connect(self.waiterProcessor)
        self.waiterThread.start()
        self.initNavigation()
        self.initWindow()

    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页', FIF.HOME_FILL)
        self.addSubInterface(self.fileInterface, FIF.FOLDER, '文件')
        self.addSubInterface(self.appInterface, FIF.APPLICATION, '应用')
        self.addSubInterface(self.videoInterface, FIF.VIDEO, '视频')

        self.addSubInterface(self.libraryInterface, FIF.SETTING, '设置', FIF.SETTING, NavigationItemPosition.BOTTOM)
        self.navigationInterface.addItem(
            routeKey='Help',
            icon=FIF.HELP,
            text='帮助',
            onClick=self.showMessageBox,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())

    def initWindow(self):
        self.resize(1000, 700)
        self.setFixedSize(1000,700)
        self.setWindowIcon(QIcon(':/images/icon.png'))
        self.setWindowTitle('WaterBox')
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

    def showMessageBox(self):
        w = MessageBox(
            '支持作者🥰',
            '个人开发不易，如果这个项目帮助到了您，可以考虑请作者喝一瓶快乐水🥤。您的支持就是作者开发和维护项目的动力🚀',
            self
        )
        w.yesButton.setText('来啦老弟')
        w.cancelButton.setText('下次一定')

        if w.exec():
            self.close()

    def waiterProcessor(self,data: dict):
        global ifAdbOK
        if not isinstance(data,str):
            if(data['app'] != "crash"):
                if(data['present'] == True):
                    ifAdbOK = True
                    device_name_list.append(data['serial'])
                    self.homeInterface.ui.ComboBox.setDisabled(False)
                    self.homeInterface.ui.ComboBox.items.clear()
                    self.homeInterface.ui.ComboBox.addItems(device_name_list)
                    self.homeInterface.ui.ComboBox.setCurrentIndex(len(device_name_list)-1)
                elif(data['present'] != True):
                    device_name_list.remove(data['serial'])
                    self.homeInterface.ui.ComboBox.items.clear()
                    self.homeInterface.ui.ComboBox.addItems(device_name_list)
                    self.homeInterface.ui.StrongBodyLabel_4.setText("(未连接)")
                    self.homeInterface.ui.ProgressBar.setValue(0)
                    self.homeInterface.ui.ComboBox.setCurrentIndex(len(device_name_list)-1)
                    if(len(device_name_list) == 0):
                        ifAdbOK = False
                        self.homeInterface.ui.ComboBox.setDisabled(True)
                        self.homeInterface.ui.ComboBox.setText("(未连接)")
                        self.homeInterface.ui.StrongBodyLabel_4.setText("(未连接)")
                        self.homeInterface.ui.StrongBodyLabel_6.setText("(未连接)")
                        self.homeInterface.ui.ProgressBar.setValue(0)

                    else:
                        self.homeInterface.ui.ComboBox.setDisabled(False)
                        self.homeInterface.ui.ComboBox.setCurrentIndex(len(device_name_list))
            else:
                w = MessageBox("ERROR", f"程序已崩溃,崩溃原因如下:{data['error']}", self)
                if w.exec():
                    sys.exit(1)
                else:
                    sys.exit(1)
        else:
            if(data == "adb connection is down"):
                ifAdbOK = False
                RestartADBWindow.show()
            elif(data == "started"):
                RestartADBWindow.close()




if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    # setTheme(Theme.DARK)

    app = QApplication(sys.argv)
    RestartADBWindow = RestartADB.RestartADBWindow()
    w = Window()
    w.show()
    app.exec_()