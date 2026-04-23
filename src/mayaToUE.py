from PySide6.QtWidgets import QVBoxLayout,QLabel,QHBoxLayout,QLineEdit,QPushButton
from core.MayaWidget import MayaWidget
import maya.cmds as mc

class MayaToUE:
    def __init__(self):
        self.meshes = []
        self.rootJnt = ""
        self.clips = []

    def setSelectedAsMesh(self):
        selection = mc.ls(sl=True)
        if not selection:
            raise Exception("please select the mesh(es) of the rig")
        
        for obj in selection:
            shapes = mc.listRelatives(obj, s=True)
            if not shapes or mc.objectType(shapes[0]) != "mesh":
                raise Exception (f"{obj} is not mesh, please selct the mesh(es) of the rig")
            
        self.meshes = selection


class MayatoUEWidget(MayaWidget):
    def __init__(self):
        super().__init__()
        self.mayaToUE = MayaToUE()
        self.setWindowTitle("Maya to Unreal Engine")

        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterlayout)

        meshSelectLayout = QHBoxLayout()
        self.masterLayout.addLayout(meshSelectLayout)
        meshSelectLayout.addWidget(QLabel("Mesh:"))
        self.meshSelectLineEdit = QLineEdit()
        self.meshSelectLineEdit.setEnabled(False)
        meshSelectLayout.addWidget(self.meshSelectLineEdit)
        meshSelectBtn = QPushButton("<<<")
        meshSelectLayout.addWidget(meshSelectBtn)
        meshSelectBtn.clicked.connect(self.meshSelectBtnClicked)

        def MeshSelectBtnClicked(self):
            self.mayaToUE.setSelectedAsMesh()
            self.meshSelectLineEdit.setText(",".join(self.mayaToUE.meshes))



    def GetWidgetHash(self):
        return "b484e2e0c10199b55dc3b0e3273fdbb38bca8ddfd80dfc15d8fca0d6df3a7e40189d2850b34152aac0bc2ec93b66cdaf"
    
def Run():
    MayatoUEWidget = MayatoUEWidget()
    MayatoUEWidget.show()

    Run()