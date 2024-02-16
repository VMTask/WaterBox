# coding:utf-8
import json
import sys
import os
import time
from PyQt5.QtCore import Qt, QUrl, QThread, pyqtSignal, pyqtSlot, QSize, QEventLoop, QTimer
from PyQt5.QtGui import QIcon, QDesktopServices, QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QWidget
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow,
                            NavigationAvatarWidget, qrouter, SubtitleLabel, setFont, SplashScreen,setThemeColor,SimpleCardWidget)
from qfluentwidgets import FluentIcon as FIF
from resources import main_rc
from interface import HomeActivity, RestartADB
from datetime import datetime
import asyncio
from mods import asyncadb, CommandExecuter, getAPKInfo


device_name_list = []
from interface import ApplicationActivity


class getAPKInfo_thread(QThread):
    sig = pyqtSignal(dict)
    
    def __init__(self,file,parent=None):
        super(getAPKInfo_thread, self).__init__(parent)
        self.file = file
    def run(self):
        app = getAPKInfo.getAPKInfo(self.file,f"{os.getcwd()}\\adb_executable\\aapt.exe")
        result = {
            "name": app.getAppName(),
            "version": app.getAppVersion(),
            "packageName": app.getAppPackageName(),
            "minSDK":  app.getAppMinSDK(),
            "targetSDK": app.getAppTargetSDK(),
            "iconFile": app.getAppIcon()
        }
        self.sig.emit(result)


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

class ApplicationWidget(QFrame):
    def __init__(self, parent: None):
        super().__init__(parent)
        
        self.ui = ApplicationActivity.Ui_Frame()
        self.ui.setupUi(self)
        
        self.ui.SimpleCardWidget.setAcceptDrops(True)
        self.ui.SimpleCardWidget.dragEnterEvent = self.dragEnterEvent
        self.ui.SimpleCardWidget.dropEvent = self.dropEvent
        
        self.ui.ElevatedCardWidget.setAcceptDrops(True)
        self.ui.ElevatedCardWidget.dragEnterEvent = self.dragEnterEvent1
        self.ui.ElevatedCardWidget.dropEvent = self.dropEvent
        self.ui.IndeterminateProgressBar.hide()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def AppInfo_processor(self,result):
        self.ui.SubtitleLabel.setText(f"应用名称:{result['name']}")
        self.ui.SubtitleLabel_2.setText(f"应用版本:{result['version']}")
        self.ui.SubtitleLabel_4.setText(f"应用包名:{result['packageName']}")
        self.ui.SubtitleLabel_5.setText(f"应用minSDK:{result['minSDK']}")
        self.ui.SubtitleLabel_6.setText(f"应用targetSDK:{result['targetSDK']}")
        self.ui.IconWidget.setIcon(QIcon(result["iconFile"]))

    def dropEvent(self, event: QDropEvent):
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        if urls:
            if(os.path.splitext(', '.join(urls))[1].lower() == ".apk".lower()):
                self.getAppInfo_thread = getAPKInfo_thread(', '.join(urls))
                self.getAppInfo_thread.sig.connect(self.AppInfo_processor)
                self.getAppInfo_thread.start()
            else:
                w = MessageBox("提醒", "请拖入.apk格式文件", self)
                if(w.exec()):
                    pass
            
    def dragEnterEvent1(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent1(self, event: QDropEvent):
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        if urls:
            # 在此处处理拖入的文件
            print(f"Dropped files: {', '.join(urls)}")
            
    

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
        title = "请问是否关闭此窗口？"
        content = "关闭后会无法使用此程序"
        w = MessageBox(title, content, self)
        if w.exec():
            event.accept()
            self.waiterThread.quit()
            RestartADBWindow.close()
        else:
            event.ignore()
    def __init__(self):
        super().__init__()
        self.titleBar.maxBtn.hide()
        # create sub interface
        self.windowEffect.setAcrylicEffect(self.winId())
        self.homeInterface = HomeWidget(self)
        setThemeColor('#28afe9')
        self.appInterface = ApplicationWidget(self)
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
        self.addSubInterface(self.appInterface, FIF.APPLICATION, '应用')
        self.addSubInterface(self.videoInterface, FIF.VIDEO, '视频')
        self.navigationInterface.buttons()[1].setDisabled(True)

        self.addSubInterface(self.libraryInterface, FIF.SETTING, '库', FIF.SETTING, NavigationItemPosition.BOTTOM)
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
        if not isinstance(data,str):
            if(data['app'] != "crash"):
                if(data['present'] == True):
                    device_name_list.append(data['serial'])
                    self.homeInterface.ui.ComboBox.setDisabled(False)
                    self.homeInterface.ui.ComboBox.items.clear()
                    self.homeInterface.ui.ComboBox.addItems(device_name_list)
                    self.homeInterface.ui.ComboBox.setCurrentIndex(len(device_name_list)-1)
                    self.navigationInterface.buttons()[1].setDisabled(False)
                elif(data['present'] != True):
                    device_name_list.remove(data['serial'])
                    self.homeInterface.ui.ComboBox.items.clear()
                    self.homeInterface.ui.ComboBox.addItems(device_name_list)
                    self.homeInterface.ui.ProgressBar.setValue(0)
                    self.homeInterface.ui.ComboBox.setCurrentIndex(len(device_name_list)-1)
                    if(len(device_name_list) == 0):
                        self.homeInterface.ui.ComboBox.setDisabled(True)
                        self.homeInterface.ui.ComboBox.setText("(未连接)")
                        self.navigationInterface.buttons()[1].setDisabled(True)
                        self.homeInterface.ui.StrongBodyLabel_4.setText("(未连接)")
                        self.homeInterface.ui.StrongBodyLabel_6.setText("(未连接)")
                        self.homeInterface.ui.ProgressBar.setValue(0)
                        
                    else:
                        self.homeInterface.ui.ComboBox.setDisabled(False)
                        self.navigationInterface.buttons()[1].setDisabled(False)
                        self.homeInterface.ui.ComboBox.setCurrentIndex(len(device_name_list))
            else:
                w = MessageBox("ERROR", f"程序已崩溃,崩溃原因如下:{data['error']}", self)
                if w.exec():
                    sys.exit(1)
                else:
                    sys.exit(1)
        else:
            if(data == "adb connection is down"):
                RestartADBWindow.show()
            elif(data == "started"):
                RestartADBWindow.close()
            
        


if __name__ == '__main__':
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
    import os
    # setTheme(Theme.DARK)
    if(os.path.exists("cache") == False):
        os.mkdir("cache")
    app = QApplication(sys.argv)
    RestartADBWindow = RestartADB.RestartADBWindow()
    w = Window()
    w.show()
    app.exec_()