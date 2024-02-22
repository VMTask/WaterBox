# coding:utf-8
import json
import shutil
import sys
import os
import time
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QRegExp
from PyQt5.QtGui import QIcon, QDragEnterEvent, QDropEvent, QRegExpValidator
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout,  QFileDialog
from qfluentwidgets import (NavigationItemPosition, MessageBox, setTheme, Theme, MSFluentWindow,
                            SubtitleLabel, setFont,setThemeColor)
from qfluentwidgets import FluentIcon as FIF
from resources import main_rc
import subprocess
from interface import HomeActivity, RestartADB, SettingsActivity, About
from datetime import datetime
import asyncio
from mods import asyncadb, CommandExecuter, getAPKInfo

now_device = ""
device_name_list = []
widget_dark_style = ""
widget_light_style = "FluentLabelBase {\n    color: black;\n	background-color: rgb(244, 247, 252);\n}\nSimpleCardWidget {\n	background-color: rgb(223, 232, 245);\n}"
terminal_dark_style = 'PlainTextEdit {\n    color: green;\n    background-color: black;\n    border: 1px solid rgba(0, 0, 0, 13);\n    border-bottom: 1px solid rgba(0, 0, 0, 100);\n    border-radius: 5px;\n    /* font: 14px "Segoe UI", "Microsoft YaHei"; */\n    padding: 0px 10px;\n}\n'
from interface import ApplicationActivity


class getAPKInfo_thread(QThread):
    sig = pyqtSignal(dict)
    
    def __init__(self,file,parent=None):
        super(getAPKInfo_thread, self).__init__(parent)
        self.file = file
    def run(self):
        try:
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
        except Exception as err:
            with open("test.log","w") as f:
                f.write("error")
            self.sig.emit({
                "status": "error",
                "error_info": err
            })


class ADBWaiter(QThread):
    sig = pyqtSignal(dict)
    error_sig = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
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

class AboutWidget(QFrame):
    def __init__(self,parent=None):
        super().__init__(parent)
        
        self.ui = About.Ui_Frame()
        self.ui.setupUi(self)
        self.setObjectName("About")
        self.ui.IconWidget.setIcon(QIcon(":/images/icon.png"))
        self.ui.ToolButton.setIcon(FIF.RETURN)

class ApplicationWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.ui = ApplicationActivity.Ui_Frame()
        self.ui.setupUi(self)
        
        self.ui.SimpleCardWidget.setAcceptDrops(True)
        self.ui.SimpleCardWidget.dragEnterEvent = self.dragEnterEvent
        self.ui.SimpleCardWidget.dropEvent = self.dropEvent
        
        self.ui.ElevatedCardWidget.setAcceptDrops(True)
        self.ui.ElevatedCardWidget.dragEnterEvent = self.dragEnterEvent1
        self.ui.ElevatedCardWidget.dropEvent = self.dropEvent1
        self.ui.IndeterminateProgressBar.hide()
        self.ui.PrimaryPushButton_2.clicked.connect(self.chooseAPKFile_info)
        self.ui.PushButton.clicked.connect(self.chooseAPKFile_install)
        self.ui.SubtitleLabel_8.hide()
        self.ui.PrimaryPushButton.clicked.connect(self.install_application)
        
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def AppInfo_processor(self,result):
        if(result.get("status") == "error"):
            w = MessageBox("错误",f"APK解析错误,错误如下:\n{result.get('error_info')}",self)
            w.exec()
        else:
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
                w.exec()
    def chooseAPKFile_info(self):
        fileInfo ,filetype= QFileDialog.getOpenFileName(self, "选择文件", os.getcwd(), "应用安装包(*.apk)")
        if(fileInfo != ""):
            self.getAppInfo_thread = getAPKInfo_thread(fileInfo)
            self.getAppInfo_thread.sig.connect(self.AppInfo_processor)
            self.getAppInfo_thread.start()
    def chooseAPKFile_install(self):
        fileInfo ,filetype= QFileDialog.getOpenFileNames(self, "选择文件", os.getcwd(), "应用安装包(*.apk)")
        if(fileInfo != ""):
            self.ui.LineEdit.setText(json.dumps(fileInfo))
            
    def dragEnterEvent1(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent1(self, event: QDropEvent):
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        if urls:
            if(os.path.splitext(', '.join(urls))[1].lower() == ".apk".lower()):
                self.ui.LineEdit.setText(json.dumps(', '.join(urls)))
            else:
                w = MessageBox("提醒", "请拖入.apk格式文件", self)
                w.exec()
    
    def install_application_info_processor(self,data):
        if("failed" in data or "Failure" in data):
            w = MessageBox("错误",f"安装时出现错误,错误如下:\n{data}",self)
            w.exec()
        elif(data == "Installed"):
            self.ui.IndeterminateProgressBar.hide()
            self.ui.SubtitleLabel_8.hide()
            self.ui.PlainTextEdit.appendPlainText(data)
            w = MessageBox("提示",f'安装完毕！',self)
            w.exec()
        else:
            self.ui.PlainTextEdit.appendPlainText(data)
            
    def install_application_count_processor(self,data):
        self.ui.SubtitleLabel_8.setText(f"正在安装第{data}个应用")
    
    
    def install_application(self):
        try:
            data = json.loads(self.ui.LineEdit.text())
            self.ui.IndeterminateProgressBar.show()
            self.ui.SubtitleLabel_8.show()
            self.t = CommandExecuter.InstallApp(data)
            self.t.sig.connect(self.install_application_info_processor)
            self.t.int_sig.connect(self.install_application_count_processor)
            self.t.start()
        except Exception:
            pass
        
                
            
    

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
        reg_exp = QRegExp(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        validator = QRegExpValidator(reg_exp, self.ui.LineEdit)
        self.ui.LineEdit.setValidator(validator)
        number_reg_exp = QRegExp(r'^\d*$')
        number_validator = QRegExpValidator(number_reg_exp,self.ui.LineEdit_2)
        self.ui.LineEdit_2.setValidator(number_validator)
        self.ui.PrimaryPushButton.clicked.connect(self.connectDevices)
        
    
    def getModelThread_response(self,data:str):
        try:
            lines = data.split('\n')  # 将字符串按换行符分割成列表
            non_empty_lines = [line for line in lines if line.strip()]  # 使用列表推导式仅保留非空行
            result = '\n'.join(non_empty_lines)  # 用换行符重新连接非空行
            self.ui.StrongBodyLabel_4.setText(result)
        except:
            pass
            
    def getBatteryThread_response(self,data:str):
        try:
            self.ui.ProgressBar.setValue(int(data.replace("level:","")))
        except:
            self.getBatteryThread.start()
    def getManufacturerThread_response(self,data:str):
        try:
            lines = data.split('\n')  # 将字符串按换行符分割成列表
            non_empty_lines = [line for line in lines if line.strip()]  # 使用列表推导式仅保留非空行
            result = '\n'.join(non_empty_lines)  # 用换行符重新连接非空行
            self.ui.StrongBodyLabel_6.setText(result)
        except:
            pass
    def onComboBoxTextChanged(self):
        global now_device
        now_device = self.ui.ComboBox.currentText()
        self.getModelThread = CommandExecuter.CommandExecuter(f".\\adb_executable\\adb -s {self.ui.ComboBox.currentText()} shell getprop ro.product.model")
        self.getModelThread.sig.connect(self.getModelThread_response)
        self.getModelThread.wait()
        self.getModelThread.start()
        self.getBatteryThread = CommandExecuter.CommandExecuter(f".\\adb_executable\\adb -s {self.ui.ComboBox.currentText()} shell dumpsys battery | grep level")
        self.getBatteryThread.sig.connect(self.getBatteryThread_response)
        self.getBatteryThread.wait()
        self.getBatteryThread.start()
        self.getManufacturerThread = CommandExecuter.CommandExecuter(f".\\adb_executable\\adb -s {self.ui.ComboBox.currentText()} shell getprop ro.product.manufacturer")
        self.getManufacturerThread.sig.connect(self.getManufacturerThread_response)
        self.getManufacturerThread.wait()
        self.getManufacturerThread.start()
        
    def connectDevices(self):
        def getResult(result):
            if("bad port number" in result):
                w = MessageBox("错误","端口号填写有误",self)
                w.exec()
            elif("无法连接" in result):
                w = MessageBox("错误","连接失败,请检查端口和IP是否正常",self)
                w.exec()
            elif("connected" in result):
                w = MessageBox("提示","连接成功",self)
                w.exec()
            else:
                w = MessageBox("错误",f"未知错误，错误如下:\n{result}",self)
                w.exec()
        if(self.ui.LineEdit.text() != ""):
            if(self.ui.LineEdit_2.text() == ""):
                port = "5555"
                self.t = CommandExecuter.CommandExecuter(f'{os.getcwd()}/adb_executable/adb.exe connect {self.ui.LineEdit.text()}:{port}')
                self.t.sig.connect(getResult)
                self.t.start()
            else:
                self.t = CommandExecuter.CommandExecuter(f'{os.getcwd()}/adb_executable/adb.exe connect {self.ui.LineEdit.text()}:{self.ui.LineEdit_2.text()}')
                self.t.sig.connect(getResult)
                self.t.start()
        else:
            w = MessageBox("错误","未填写IP地址",self)
            w.exec()







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
            shutil.rmtree(f"{os.getcwd()}/cache")
            RestartADBWindow.close()
        else:
            event.ignore()
    def __init__(self):
        super().__init__()
        self.titleBar.maxBtn.hide()
        # create sub interface
        self.windowEffect.setMicaEffect(self.winId())
        self.homeInterface = HomeWidget(self)
        setThemeColor('#28afe9')
        self.appInterface = ApplicationWidget(self)
        self.videoInterface = Widget('Video Interface', self)
        self.settingsInterface = SettingsActivity.SettingInterface(self)
        self.aboutInterface = AboutWidget(self)
        self.waiterThread = ADBWaiter()
        self.waiterThread.sig.connect(self.waiterProcessor)
        self.waiterThread.error_sig.connect(self.waiterProcessor)
        self.waiterThread.start()
        self.aboutInterface.ui.ToolButton.clicked.connect(self.return_home)
        if(os.path.exists(f"{os.getcwd()}/config/config.json")):
            with open(f"{os.getcwd()}/config/config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
            if(config["QFluentWidgets"]["ThemeMode"] == "Dark"):
                if(config["isMica"]):
                    setTheme(Theme.DARK)
                    self.homeInterface.ui.SimpleCardWidget.setStyleSheet(widget_dark_style)
                    self.homeInterface.ui.SimpleCardWidget_2.setStyleSheet(widget_dark_style)
                    self.appInterface.ui.ElevatedCardWidget.setStyleSheet(widget_dark_style)
                    self.appInterface.ui.SimpleCardWidget.setStyleSheet(widget_dark_style)
                    self.settingsInterface.settingLabel.setStyleSheet("font: 33px 'Microsoft YaHei Light';background-color: transparent;color: white;")
            else:
                setTheme(Theme.LIGHT)
            if(config["QFluentWidgets"]["isMica"]):
                if(config["QFluentWidgets"]["ThemeMode"] == "Dark"):
                    self.windowEffect.setMicaEffect(self.winId(),isDarkMode=True)
                else:
                    self.windowEffect.setMicaEffect(self.winId(),isDarkMode=False)
            if(config["QFluentWidgets"]["isAcrylic"]):
                self.windowEffect.setAcrylicEffect(self.winId())
            if(config["QFluentWidgets"]["isAero"]):
                self.windowEffect.setAeroEffect(self.winId())
        self.initNavigation()
        self.initWindow()
    def return_home(self):
        self.switchTo(self.homeInterface)
    def initNavigation(self):
        self.addSubInterface(self.homeInterface, FIF.HOME, '主页', FIF.HOME_FILL)
        self.addSubInterface(self.appInterface, FIF.APPLICATION, '应用安装')
        self.addSubInterface(self.videoInterface, FIF.VIDEO, '屏幕工具箱')
        self.appInterface.ui.PrimaryPushButton.setDisabled(True)

        self.addSubInterface(self.settingsInterface, FIF.SETTING, '设置', FIF.SETTING, NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.aboutInterface,FIF.INFO,"关于",FIF.INFO,NavigationItemPosition.BOTTOM)
        self.navigationInterface.addItem(
            routeKey='ADB_Terminal',
            icon=FIF.COMMAND_PROMPT,
            text='ADB终端',
            onClick=self.adb_terminal,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )
        self.navigationInterface.setCurrentItem(self.homeInterface.objectName())
    def adb_terminal(self):
        subprocess.Popen(['cmd', '/k', f'cd {os.getcwd()}/adb_executable'], creationflags=subprocess.CREATE_NEW_CONSOLE)
    def initWindow(self):
        self.resize(1000, 700)
        self.setFixedSize(1000,700)
        self.setWindowIcon(QIcon(':/images/icon.png'))
        self.setWindowTitle('WaterBox')
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)

            
    def waiterProcessor(self,data: dict):
        if not isinstance(data,str):
            if(data['app'] != "crash"):
                if(data['present'] == True and data['status'] != "offline"):
                    device_name_list.append(data['serial'])
                    self.homeInterface.ui.ComboBox.setDisabled(False)
                    self.homeInterface.ui.ComboBox.items.clear()
                    self.homeInterface.ui.ComboBox.addItems(device_name_list)
                    self.homeInterface.ui.ComboBox.setCurrentIndex(len(device_name_list)-1)
                    self.appInterface.ui.PrimaryPushButton.setDisabled(False)
                elif(data['status'] == "offline"):
                    w =  MessageBox("提醒","设备已离线，请尝试重新连接设备")
                    w.exec()
                elif(data['present'] != True):
                    device_name_list.remove(data['serial'])
                    self.homeInterface.ui.ComboBox.items.clear()
                    self.homeInterface.ui.ComboBox.addItems(device_name_list)
                    self.homeInterface.ui.ProgressBar.setValue(0)
                    self.homeInterface.ui.ComboBox.setCurrentIndex(len(device_name_list)-1)
                    if(len(device_name_list) == 0):
                        self.homeInterface.ui.ComboBox.setDisabled(True)
                        self.homeInterface.ui.ComboBox.setText("(未连接)")
                        self.appInterface.ui.PrimaryPushButton.setDisabled(True)
                        self.homeInterface.ui.StrongBodyLabel_4.setText("(未连接)")
                        self.homeInterface.ui.StrongBodyLabel_6.setText("(未连接)")
                        self.homeInterface.ui.ProgressBar.setValue(0)
                    else:
                        self.homeInterface.ui.ComboBox.setDisabled(False)
                        self.appInterface.ui.PrimaryPushButton.setDisabled(False)
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