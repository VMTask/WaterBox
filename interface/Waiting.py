import sys

from PyQt5.QtCore import Qt, QTranslator, QLocale, QRect, QCoreApplication, QMetaObject
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication
from qframelesswindow import FramelessWindow, StandardTitleBar, AcrylicWindow
from qfluentwidgets import setThemeColor, FluentTranslator, setTheme, Theme, SplitTitleBar


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 113)
        self.TitleLabel = TitleLabel(Form)
        self.TitleLabel.setGeometry(QRect(60, 10, 301, 71))
        self.TitleLabel.setObjectName("TitleLabel")

        self.retranslateUi(Form)
        QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.TitleLabel.setText("加载中...")
        self.TitleLabel.move(150, 25)
        self.TitleLabel.raise_()


from qfluentwidgets import IndeterminateProgressBar, TitleLabel


class WaitingWindow(AcrylicWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # setTheme(Theme.DARK)
        setThemeColor('#28afe9')
        self.titleBar.maxBtn.hide()
        self.titleBar.minBtn.hide()
        self.titleBar.closeBtn.hide()

        self.setWindowTitle('WaterBox-Waiting')
        self.setWindowIcon(QIcon(":/images/icon.png"))
        self.windowEffect.setMicaEffect(self.winId(), isDarkMode=False)
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setWindowFlags(Qt.WindowSystemMenuHint)
        desktop = QApplication.desktop().availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w // 2 - self.width() // 2, h // 2 - self.height() // 2)


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

    w = WaitingWindow()
    w.show()
    app.exec_()