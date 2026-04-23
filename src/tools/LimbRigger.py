##Ctrl P is to search 
##Alt+leftarrow key goes back to the prevous line you were at
##Ctrl+P and type @ ___ to find a symbol
from core.MayaWidget import MayaWidget
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QColorDialog
import maya.cmds as mc
from maya.OpenMaya import MVector # this is the same as the Vector3 in Unity, transform.position

import importlib
import core.MayaUtilities
importlib.reload(core.MayaUtilities)
from core.MayaUtilities import (CreateCircleControllerForJnt, 
                                CreateBoxControllerForJnt,
                                CreatePlusController,
                                ConfigureCtrlForJnt,
                                GetObjectPositionAsMVec
                                )
# the class to handle the rigging job
class LimbRigger:
    # the constructor of the limb 
    def __init__(self):
        self.nameBase = ""
        self.controllerSize = 10
        self.blendControllerSize = 4
        self.controlColorRGB = [0,0,0]

    def SetNameBase(self, newNameBase):
        self.nameBase = newNameBase
        print(f"name base is set to: {self.nameBase}")

    def SetControllerSize(self, newControllerSize):
        self.controllerSize = newControllerSize

    def SetBlendControllerSize(self, newBlendControllerSize):
        self.blendControllerSize = newBlendControllerSize

    def RigLimb(self):
        print("Start rigging!!")
        rootJnt, midJnt, endJnt = mc.ls(sl=True)
        print(f"found root {rootJnt}, mid: {midJnt} and end: {endJnt}")

        rootCtrl, rootCtrlGrp = CreateCircleControllerForJnt(rootJnt, "fk_" + self.nameBase, self.controllerSize)
        midCtrl, midCtrlGrp = CreateCircleControllerForJnt(midJnt, "fk_" + self.nameBase, self.controllerSize)
        endCtrl, endCtrlGrp = CreateCircleControllerForJnt(endJnt, "fk_" + self.nameBase, self.controllerSize)

        mc.parent(endCtrlGrp, midCtrl)
        mc.parent(midCtrlGrp, rootCtrl)

        endIkCtrl, endIkCtrlGrp = CreateBoxControllerForJnt(endJnt, "ik_" + self.nameBase, self.controllerSize)

        ikFkBlendCtrlPrefix = self.nameBase + "_ikfkBlend"
        ikFkBlendController =  CreatePlusController(ikFkBlendCtrlPrefix, self.blendControllerSize)
        ikFkBlendController, ikFkBlendControllerGrp = ConfigureCtrlForJnt(rootJnt, ikFkBlendController, False)

        ikfkBlendAttrName = "ikfkBlend"
        mc.addAttr(ikFkBlendController, ln=ikfkBlendAttrName, min=0, max=1, k=True)

        ikHandleName = "ikHandle_" + self.nameBase 
        mc.ikHandle(n=ikHandleName, sj = rootJnt, ee=endJnt, sol="ikRPsolver")

        rootJntLoc = GetObjectPositionAsMVec(rootJnt)
        endJntLoc = GetObjectPositionAsMVec(endJnt)

        poleVectorVals = mc.getAttr(f"{ikHandleName}.poleVector")[0]
        poleVecDir = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2])
        poleVecDir.normalize() # make it a unit vector, a vector that has a length of 1

        rootToEndVec = endJntLoc - rootJntLoc
        rootToEndDist = rootToEndVec.length()

        poleVectorCtrlLoc = rootJntLoc + rootToEndVec/2.0 + poleVecDir * rootToEndDist

        poleVectorCtrlName = "ac_ik_" + self.nameBase + "poleVector"
        mc.spaceLocator(n=poleVectorCtrlName)

        poleVectorCtrlGrpName = poleVectorCtrlName + "_grp"
        mc.group(poleVectorCtrlName, n = poleVectorCtrlGrpName)

        mc.setAttr(f"{poleVectorCtrlGrpName}.translate", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, type="double3")
        mc.poleVectorConstraint(poleVectorCtrlName, ikHandleName)

        mc.parent(ikHandleName, endIkCtrl)
        mc.setAttr(f"{ikHandleName}.v", 0)

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{ikHandleName}.ikBlend")
        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{endIkCtrlGrp}.v")
        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{poleVectorCtrlGrpName}.v")

        reverseNodeName = f"{self.nameBase}_reverse"
        mc.createNode("reverse", n=reverseNodeName)

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{reverseNodeName}.inputX")
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{rootCtrlGrp}.v")

        orientConstaint = None
        wristConnections = mc.listConnections(endJnt)
        for connection in wristConnections:
            if mc.objectType(connection) == "orientConstraint":
                orientConstaint = connection
                break

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{orientConstaint}.{endIkCtrl}W1")
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{orientConstaint}.{endCtrl}W0")

        topGrpName = f"{self.nameBase}_rig_grp"
        mc.group(n=topGrpName, empty=True)

        mc.parent(rootCtrlGrp, topGrpName)
        mc.parent(ikFkBlendControllerGrp, topGrpName)
        mc.parent(endIkCtrlGrp, topGrpName)
        mc.parent(poleVectorCtrlGrpName, topGrpName)

        # add color overide for the topGrpName to be self.controllColorRGB
        mc.setAttr(topGrpName + ".overrideEnabled",1)
        mc.setAttr(topGrpName + ".overrideRGBColors",1)
        mc.setAttr(topGrpName + ".overrideColorRGB", self.controlColorRGB[0], self.controlColorRGB[1], self.controlColorRGB[2])


class LimbRiggerWidget(MayaWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Limb Rigger")
        self.rigger = LimbRigger()
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.masterLayout.addWidget(QLabel("Select the 3 joints of the limb, from base to end, and then:"))

        self.infoLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.infoLayout)
        self.infoLayout.addWidget(QLabel("Name Base:"))

        self.nameBaseLineEdit = QLineEdit()
        self.infoLayout.addWidget(self.nameBaseLineEdit)

        self.setNameBaseBtn = QPushButton("Set Name Base")
        self.setNameBaseBtn.clicked.connect(self.SetNameBaseBtnClicked)
        self.infoLayout.addWidget(self.setNameBaseBtn)


        # add a color pick widget to the self.masterLayout

        self.colorPicker = QPushButton("Color Picker")
        self.colorPicker.clicked.connect(self.ColorPickerBtnClicked)
        self.masterLayout.addWidget(self.colorPicker)
            
        # listen for color change and connect to a function.
        # the function needs to update the color of of limbRigger: self.rigger.controlColorRGB

        self.rigLimbBtn = QPushButton("Rig Limb")
        self.rigLimbBtn.clicked.connect(self.RigLimbBtnClicked)
        self.masterLayout.addWidget(self.rigLimbBtn)

    def SetNameBaseBtnClicked(self):
        self.rigger.SetNameBase(self.nameBaseLineEdit.text())

    def RigLimbBtnClicked(self):
        self.rigger.RigLimb()

    
    def ColorPickerBtnClicked(self):
        pickedColor = QColorDialog().getColor()
        self.rigger.controlColorRGB[0] = pickedColor.redF()
        self.rigger.controlColorRGB[1] = pickedColor.greenF()
        self.rigger.controlColorRGB[2] = pickedColor.blueF()
        print(self.rigger.controlColorRGB)

    def SetControlColor(self, newControlColorRGB):
        self.controlColorRGB = newControlColorRGB



    def GetWidgetHash(self):
        return "b5921fb4562094613c70a2aa7fb45ae8dabfa8bdad6aad52aa8eef0ffd5b0f06"


def Run():
    limbRiggerWidget = LimbRiggerWidget()
    limbRiggerWidget.show()

Run()