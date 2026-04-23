##Ctrl P is to search 
##Alt+leftarrow key goes back to the prevous line you were at
##Ctrl+P and type @ ___ to find a symbol
from core.MayaWidget import MayaWidget                                                                  ##imports custom base class that ensures UI works correctly within Maya
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QColorDialog    ## imports UI from Qt
import maya.cmds as mc                                                                                  ## imports Maya's standard Python commands to control the 3D scene
from maya.OpenMaya import MVector                                                                       ## imports Maya's Math library, this is the same as the Vector3 in Unity, transform.position

import importlib                                                                                        ## reloads Pythons built-in library
import core.MayaUtilities                                                                               ## imports MayaUtilities custon script
importlib.reload(core.MayaUtilities)                                                                    ## imports all the def from Maya Utilities
from core.MayaUtilities import (CreateCircleControllerForJnt,
                                CreateBoxControllerForJnt,
                                CreatePlusController,
                                ConfigureCtrlForJnt,
                                GetObjectPositionAsMVec
                                )

class LimbRigger:                                                                                       ## the class to handle the rigging job
    def __init__(self):                                                                                 ## the constructor of the limb 
        self.nameBase = ""                                                                              ## creates an empty string that will later hold Limb name
        self.controllerSize = 10                                                                        ## sets the radius of FK controllers
        self.blendControllerSize = 4                                                                    ## sets the IKFK switch controller size
        self.controlColorRGB = [0,0,0]                                                                  ## list representing RBG colors

    def SetNameBase(self, newNameBase):                                                                 ## defines the functions
        self.nameBase = newNameBase                                                                     ## temp stores and assigns to class variable
        print(f"name base is set to: {self.nameBase}")                                                  ## feedback/ prints

    def SetControllerSize(self, newControllerSize):                                                     ## defines controller size and creates new variable
        self.controllerSize = newControllerSize                                                         ## allows a value other than default

    def SetBlendControllerSize(self, newBlendControllerSize):                                           ## defines blend controller size and creates new variable
        self.blendControllerSize = newBlendControllerSize                                               ## allows default to be overwritten

    def RigLimb(self):                                                                                  ## defines main method to build rig and has excess to all earlier variables
        print("Start rigging!!")                                                                        ## print to show its working
        rootJnt, midJnt, endJnt = mc.ls(sl=True)                                                        ## selects list selection command (have to select 3 joints)
        print(f"found root {rootJnt}, mid: {midJnt} and end: {endJnt}")                                 ## debug print

        rootCtrl, rootCtrlGrp = CreateCircleControllerForJnt(rootJnt, "fk_" + self.nameBase, self.controllerSize)         ## creates a nurbs circle for shoulder and names it
        midCtrl, midCtrlGrp = CreateCircleControllerForJnt(midJnt, "fk_" + self.nameBase, self.controllerSize)            ## creates a nurbs circle for elbow joint and names it
        endCtrl, endCtrlGrp = CreateCircleControllerForJnt(endJnt, "fk_" + self.nameBase, self.controllerSize)            ## creates a nurbs circle for wrist joint and manes it

        mc.parent(endCtrlGrp, midCtrl)                                                                                    ## parents wrist to elbow
        mc.parent(midCtrlGrp, rootCtrl)                                                                                   ## parents elbow to shoulder

        endIkCtrl, endIkCtrlGrp = CreateBoxControllerForJnt(endJnt, "ik_" + self.nameBase, self.controllerSize)           ## Creates box controller for IK and names it

        ikFkBlendCtrlPrefix = self.nameBase + "_ikfkBlend"                                                                ## creates a name for controller
        ikFkBlendController =  CreatePlusController(ikFkBlendCtrlPrefix, self.blendControllerSize)                        ## creates a plus shape and set size 
        ikFkBlendController, ikFkBlendControllerGrp = ConfigureCtrlForJnt(rootJnt, ikFkBlendController, False)            ## snaps plus controller to root joint and doesnt contrain joint to controller

        ikfkBlendAttrName = "ikfkBlend"                                                                                   ## sets a long name to ikfk blend
        mc.addAttr(ikFkBlendController, ln=ikfkBlendAttrName, min=0, max=1, k=True)                                       ## creates a keyable slider to min 0 and Max 1

        ikHandleName = "ikHandle_" + self.nameBase                                                                        ## creates reverse Kinematics
        mc.ikHandle(n=ikHandleName, sj = rootJnt, ee=endJnt, sol="ikRPsolver")                                            ## allows you to locate and use the pole vector of said limb

        rootJntLoc = GetObjectPositionAsMVec(rootJnt)                                                                     ## finds the exact x,y,z coordinates of root limb
        endJntLoc = GetObjectPositionAsMVec(endJnt)                                                                       ## finds the exact x,y,z coords of End of limb

        poleVectorVals = mc.getAttr(f"{ikHandleName}.poleVector")[0]                                                      ## grabs the pole vectors value
        poleVecDir = MVector(poleVectorVals[0], poleVectorVals[1], poleVectorVals[2])                                     ## takes Pole vectore and sends to mVector constructor (helps offset elbow control)
        poleVecDir.normalize()                                                                                            ## make it a unit vector, a vector that has a length of 1

        rootToEndVec = endJntLoc - rootJntLoc                                                                             ## subtracts shoulder and wrist position to get the distance between them
        rootToEndDist = rootToEndVec.length()                                                                             ## finds what distance the elbow/knee controller should sit

        poleVectorCtrlLoc = rootJntLoc + rootToEndVec/2.0 + poleVecDir * rootToEndDist                                    ## adds the horizontal offset to the vertical offset to create the elbow triangle

        poleVectorCtrlName = "ac_ik_" + self.nameBase + "poleVector"                                                      ## creates the elbow pole vector name
        mc.spaceLocator(n=poleVectorCtrlName)                                                                             ## creates a locator as the elbow controller

        poleVectorCtrlGrpName = poleVectorCtrlName + "_grp"                                                               ## names the group for the elbow
        mc.group(poleVectorCtrlName, n = poleVectorCtrlGrpName)                                                           ## creates the group for elbow contoller

        mc.setAttr(f"{poleVectorCtrlGrpName}.translate", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, type="double3")                ## moves group to previously calculated coordinates
        mc.poleVectorConstraint(poleVectorCtrlName, ikHandleName)                                                                                      ## constrains pole vector group to mid joint

        mc.parent(ikHandleName, endIkCtrl)                                                                                ## makes IK handle child of the wrist box controller
        mc.setAttr(f"{ikHandleName}.v", 0)                                                                                ## toggles visability off

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{ikHandleName}.ikBlend")                           ## when slider 0, IK control is off, slider 1, IK sontrol is on
        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{endIkCtrlGrp}.v")                                 ## connects ik visablity slider to the IK box controller
        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{poleVectorCtrlGrpName}.v")                        ## connects the pole vector to the visabilty

        reverseNodeName = f"{self.nameBase}_reverse"                                                                      ## nameing variable
        mc.createNode("reverse", n=reverseNodeName)                                                                       ## creates reverse node (ik controllers visible and moveable when slider on, invisible and unmoveable when slider off)

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{reverseNodeName}.inputX")                         ## connects 0 to 1 slider to reverse node
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{rootCtrlGrp}.v")                                                  ## takes output and plugs it into FK root group

        orientConstaint = None                                                                                            ## assumes we havent found the contraint yet?
        wristConnections = mc.listConnections(endJnt)                                                                     ## asks maya to show every node currently plugged into wrist joint
        for connection in wristConnections:                                                                               ## starts a loop with every connection and call it connection then run:
            if mc.objectType(connection) == "orientConstraint":                                                           ## if the statement above is true:
                orientConstaint = connection                                                                              ## we store it in the variable orientconstraint
                break                                                                                                     ## once constraint found stops looking

        mc.connectAttr(f"{ikFkBlendController}.{ikfkBlendAttrName}", f"{orientConstaint}.{endIkCtrl}W1")                  ## connects the 0 to 1 slider to IK weight (has 100% influence over rotation)
        mc.connectAttr(f"{reverseNodeName}.outputX", f"{orientConstaint}.{endCtrl}W0")                                    ## when connection is flipped then FK has 100% of the weight

        topGrpName = f"{self.nameBase}_rig_grp"                                                                           ## creates a naming string for main folder
        mc.group(n=topGrpName, empty=True)                                                                                ## creates a null folder with no geo

        mc.parent(rootCtrlGrp, topGrpName)                                                                                ## parents FK (shoulder/hip) group to main rig group
        mc.parent(ikFkBlendControllerGrp, topGrpName)                                                                     ## parents IK/FK switch (plus) to main rig group
        mc.parent(endIkCtrlGrp, topGrpName)                                                                               ## parents ik wrist/ankle to main rig group
        mc.parent(poleVectorCtrlGrpName, topGrpName)                                                                      ## parents pole vector (elbow) into main rig group

        # add color overide for the topGrpName to be self.controllColorRGB
        mc.setAttr(topGrpName + ".overrideEnabled",1)                                                                               ## tells maya to ignore default rules and give you master controls
        mc.setAttr(topGrpName + ".overrideRGBColors",1)                                                                             ## switches coloring mode from index to full RGB spectrum
        mc.setAttr(topGrpName + ".overrideColorRGB", self.controlColorRGB[0], self.controlColorRGB[1], self.controlColorRGB[2])     ## takes color applied by the user and plugs it into the slots


class LimbRiggerWidget(MayaWidget):                                                                                       ## defines new class for UI and makes sure window behaves in Maya
    def __init__(self):                                                                                                   ## runs automatically when window is created
        super().__init__()                                                                                                ## tells python to run setup code from mayawidget
        self.setWindowTitle("Limb Rigger")                                                                                ## text that apears at the top bar of window
        self.rigger = LimbRigger()                                                                                        ## connects buttons to the rigging code
        self.masterLayout = QVBoxLayout()                                                                                 ## allows you stack buttons vertically or under the other
        self.setLayout(self.masterLayout)                                                                                 ## use masterLayout as main organizing system

        self.masterLayout.addWidget(QLabel("Select the 3 joints of the limb, from base to end, and then:"))               ## creates noneditable text with instructions (how to use the tool)

        self.infoLayout = QHBoxLayout()                                                                                   ## creates horizontal Layout (stacks left to right)
        self.masterLayout.addLayout(self.infoLayout)                                                                      ## nests horizontal inside vertical master layout
        self.infoLayout.addWidget(QLabel("Name Base:"))                                                                   ## adds label for naming field

        self.nameBaseLineEdit = QLineEdit()                                                                               ## creates a text input for naming limbs (arm_l,arm_r,ect.)
        self.infoLayout.addWidget(self.nameBaseLineEdit)                                                                  ## places button into horizontal layout, next to Name Base:

        self.setNameBaseBtn = QPushButton("Set Name Base")                                                                ## creates a button that is labeled set name base
        self.setNameBaseBtn.clicked.connect(self.SetNameBaseBtnClicked)                                                   ## tells the button what to run when clicked 
        self.infoLayout.addWidget(self.setNameBaseBtn)                                                                    ## adds button to the right of text box


        # add a color pick widget to the self.masterLayout

        self.colorPicker = QPushButton("Color Picker")                                                                    ## creates a clickable button labeled color picker
        self.colorPicker.clicked.connect(self.ColorPickerBtnClicked)                                                      ## when clicked it opens the color wheel
        self.masterLayout.addWidget(self.colorPicker)                                                                     ## arranges the button below the name base section
            
        # listen for color change and connect to a function.
        # the function needs to update the color of of limbRigger: self.rigger.controlColorRGB

        self.rigLimbBtn = QPushButton("Rig Limb")                                                                         ## creates a button to rig limb
        self.rigLimbBtn.clicked.connect(self.RigLimbBtnClicked)                                                           ## connects the button to allows rigging to happen when clicked
        self.masterLayout.addWidget(self.rigLimbBtn)                                                                      ## adds this button under the select color button

    def SetNameBaseBtnClicked(self):                                                                                      ## when button is clicked it text in text box 
        self.rigger.SetNameBase(self.nameBaseLineEdit.text())                                                             ## when rig builds joints it will know what to name them

    def RigLimbBtnClicked(self):                                                                                          ## when button labeled rig limb is clicked:
        self.rigger.RigLimb()                                                                                             ## executes the function/code rig limb

    
    def ColorPickerBtnClicked(self):                                                                                      ## bridges between the users mouse click and code that holds the color
        pickedColor = QColorDialog().getColor()                                                                           ## pauses the script and opens color picker window and waits for ok to be clicked
        self.rigger.controlColorRGB[0] = pickedColor.redF()                                                               ## grabs red percentage in picked color by user
        self.rigger.controlColorRGB[1] = pickedColor.greenF()                                                             ## grabs green percentage in color picked by user
        self.rigger.controlColorRGB[2] = pickedColor.blueF()                                                              ## grabs blue percentage in color picked by user
        print(self.rigger.controlColorRGB)                                                                                ## prints the final RBG list

    def SetControlColor(self, newControlColorRGB):                                                                        ## overrides old default color and uses one picked by the user
        self.controlColorRGB = newControlColorRGB



    def GetWidgetHash(self):                                                                                              ## uses a hash to check if the limb rigger is open (doesnt open multiple limb rigger window)
        return "b5921fb4562094613c70a2aa7fb45ae8dabfa8bdad6aad52aa8eef0ffd5b0f06"                                         ## the Unique Hash that will be used


def Run():                                                                                                                ## defines run function
    limbRiggerWidget = LimbRiggerWidget()                                                                                 ## the code becomes object in computer memory
    limbRiggerWidget.show()                                                                                               ## makes window apear on users string

Run()                                                                                                                     ## runs code 