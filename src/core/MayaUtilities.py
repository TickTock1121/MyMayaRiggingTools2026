import maya.cmds as mc
import maya.mel as ml
from maya.OpenMaya import MVector

def ConfigureCtrlForJnt(jnt, ctrlName, doContraint=True):
    ctrlGrpName = ctrlName + "_grp"
    mc.group(ctrlName, n=ctrlGrpName)

    mc.matchTransform(ctrlGrpName, jnt)
    if doContraint:
        mc.orientConstraint(ctrlName, jnt)  

    return ctrlName, ctrlGrpName

# make the plus shaped controller, this will be used for the ikfk blend
def CreatePlusController(namePrefix, size):
    # use the ml.eval() to make the plus shaped curve
    ctrlName = f"ac_{namePrefix}"
    ml.eval(f"curve -n {ctrlName} -d 1 -p 1 1 0 -p 1 3 0 -p -1 3 0 -p -1 1 0 -p -3 1 0 -p -3 -1 0 -p -1 -1 0 -p -1 -3 0 -p 1 -3 0 -p 1 -1 0 -p 3 -1 0 -p 3 1 0 -p 1 1 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")

    # scale the controller to the size
    mc.setAttr(f"{ctrlName}.scale", size/6.0, size/6.0, size/6.0, type="double3")

    # freeze transformation
    mc.makeIdentity(ctrlName, apply=True)

    # lock and hide the translate, scale, and rotation, and visibility of the controller
    mc.setAttr(f'{ctrlName}.translateX', lock=True, cb=False, k=False)
    mc.setAttr(f'{ctrlName}.translateY', lock=True, cb=False, k=False)
    mc.setAttr(f'{ctrlName}.translateZ', lock=True, cb=False, k=False)
    mc.setAttr(f'{ctrlName}.scaleX', lock=True, cb=False, k=False)
    mc.setAttr(f'{ctrlName}.scaleY', lock=True, cb=False, k=False)
    mc.setAttr(f'{ctrlName}.scaleZ', lock=True, cb=False, k=False)
    mc.setAttr(f'{ctrlName}.rotateX', lock=True, cb=False, k=False)
    mc.setAttr(f'{ctrlName}.rotateY', lock=True, cb=False, k=False)
    mc.setAttr(f'{ctrlName}.rotateZ', lock=True, cb=False, k=False)
    mc.setAttr(f'{ctrlName}.visibility', lock=True, cb=False, k=False)

    SetCurveLineWidth(ctrlName, 2)
    return ctrlName



def CreateCircleControllerForJnt(jnt, namePrefix, radius=10):
    ctrlName = f"ac_{namePrefix}_{jnt}"  
    mc.circle(n=ctrlName, r = radius, nr=(1,0,0))
    SetCurveLineWidth(ctrlName, 2)
    return ConfigureCtrlForJnt(jnt, ctrlName)


def CreateBoxControllerForJnt(jnt, namePrefix, size=10):
    ctrlName = f"ac_{namePrefix}_{jnt}"
    ml.eval(f"curve -n {ctrlName} -d 1 -p -0.5 0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p 0.5 -0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p -0.5 -0.5 0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15;")
    mc.setAttr(f"{ctrlName}.scale", size, size, size, type="double3")

    # this is the same as freeze transformation command in maya
    mc.makeIdentity(ctrlName, apply=True)

    SetCurveLineWidth(ctrlName, 2)
    return ConfigureCtrlForJnt(jnt, ctrlName)


def GetObjectPositionAsMVec(objectName)->MVector:
    # t means translate values, ws means world space, q mean query
    wsLoc = mc.xform(objectName, t=True, ws=True, q=True)
    return MVector(wsLoc[0], wsLoc[1], wsLoc[2])

def SetCurveLineWidth(curve, newWidth):
    shapes = mc.listRelatives(curve, s=True)
    for shape in shapes:
        mc.setAttr(f"{shape}.lineWidth", newWidth)

    