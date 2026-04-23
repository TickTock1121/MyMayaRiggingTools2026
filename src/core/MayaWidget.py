import maya.cmds as mc
from PySide6.QtWidgets import QWidget, QMainWindow
from PySide6.QtCore import Qt
import maya.OpenMayaUI as omui
from shiboken6 import wrapInstance

def GetMayaMainWindow()->QMainWindow:
    GetMayaMainWindow = omui.MQtUtil.mainWindow()
    return wrapInstance(int(GetMayaMainWindow), QMainWindow)

def RemoveWidgetWithName(objectName):
    for widget in GetMayaMainWindow().findChildren(QWidget, objectName):
        widget.deleteLater()

class MayaWidget(QWidget):
    def __init__(self):
        super().__init__(parent=GetMayaMainWindow())
        self.setWindowFlag(Qt.WindowType.Window)
        self.setWindowTitle("Maya Widget")
        RemoveWidgetWithName(self.GetWidgetHash())
        self.setObjectName(self.GetWidgetHash())

    def GetWidgetHash(self):
        return "c126f41fe55a05cb4c0a4089fb423ba7ab69f70ac8458c40e7107acf2c3dd17c"
