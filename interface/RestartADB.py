import sys

from PyQt5.QtCore import Qt, QTranslator, QLocale, QRect, QCoreApplication, QMetaObject
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication
from qframelesswindow import FramelessWindow, StandardTitleBar, AcrylicWindow
from qfluentwidgets import setThemeColor, FluentTranslator, setTheme, Theme, SplitTitleBar

import os,sys
current_dir = os.path.dirname(os.path.abspath(__file__))
# 计算并添加上一级目录到sys.path
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)  # 将其添加到搜索路径的开始，保证优先级最高
from resources import main_rc
del sys.path[0]


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 113)
        self.TitleLabel = TitleLabel(Form)
        self.TitleLabel.setGeometry(QRect(60, 10, 301, 71))
        self.TitleLabel.setObjectName("TitleLabel")
        self.IndeterminateProgressBar = IndeterminateProgressBar(Form)
        self.IndeterminateProgressBar.setGeometry(QRect(20, 80, 361, 4))
        self.IndeterminateProgressBar.setObjectName("IndeterminateProgressBar")

        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.TitleLabel.setText(_translate("Form", "正在重启ADB服务器"))
from qfluentwidgets import IndeterminateProgressBar, TitleLabel


class RestartADBWindow(AcrylicWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # setTheme(Theme.DARK)
        setThemeColor('#28afe9')
        self.titleBar.maxBtn.hide()
        self.titleBar.minBtn.hide()
        self.titleBar.closeBtn.hide()
        
        
        self.setWindowTitle('WaterBox-RestartADB')
        self.setWindowIcon(QIcon(":/images/icon.png"))
        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=False)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowSystemMenuHint)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)



if __name__ == '__main__':
    # enable dpi scale
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

    app = QApplication(sys.argv)

    # Internationalization
    translator = FluentTranslator(QLocale())
    app.installTranslator(translator)

    w = RestartADBWindow()
    w.show()
    app.exec_()