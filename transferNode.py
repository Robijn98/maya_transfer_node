from __future__ import division
import sys
import math
import maya.api.OpenMaya as om
import maya.api.OpenMayaRender as omr
import maya.OpenMayaRender as omr_legacy
import maya.OpenMaya as om_legacy
import maya.cmds as cmds


def maya_useNewAPI():
    pass


def get_uvs(mesh):
    num_verts = cmds.polyEvaluate(mesh, vertex=True)
    uCoords = om_legacy.MFloatArray()
    vCoords = om_legacy.MFloatArray()

    for i in range(num_verts):
        vert = f"{mesh}.vtx[{i}]"
        uv = cmds.polyListComponentConversion(vert, fromVertex=True, toUV=True)
        uv = cmds.filterExpand(uv, selectionMask=35)

        if uv:
            uv_val = cmds.polyEditUV(uv[0], query=True)
            uCoords.append(uv_val[0])
            vCoords.append(uv_val[1])
        else:
            uCoords.append(0.0)
            vCoords.append(0.0)

    return uCoords, vCoords


def sampleColor2D(shadingNode, mesh):
    
    vertices = cmds.ls(f"{mesh}.vtx[*]", flatten=True)
    points = [cmds.pointPosition(vtx, world=True) for vtx in vertices]    
        
    textureNodeAttr = shadingNode
    numSamples = len(points)
    pointArray = om_legacy.MFloatPointArray()
    refPoints = om_legacy.MFloatPointArray()
    
    pointArray.setLength(numSamples)
    refPoints.setLength(numSamples)
    
    for i, point in enumerate(points):
        location = om_legacy.MFloatPoint(point[0], point[1], point[2])
        pointArray.set(location, i)
        refPoints.set(location, i)
    
    uCoords, vCoords = get_uvs(mesh)
    useShadowMap = False
    reuseMaps = False
    cameraMatrix = om_legacy.MFloatMatrix()
    
    resultColors = om_legacy.MFloatVectorArray()
    resultTransparencies = om_legacy.MFloatVectorArray()

    omr_legacy.MRenderUtil.sampleShadingNetwork(
        textureNodeAttr, 
        numSamples, 
        useShadowMap, 
        reuseMaps,
        cameraMatrix, 
        pointArray,
        uCoords, 
        vCoords, 
        None, 
        refPoints,
        None, 
        None, 
        None, 
        resultColors, 
        resultTransparencies
    )
    
    sampledColorArray = []
    for i in range(resultColors.length()):
        vec = resultColors[i]
        sampledColorArray.append([vec.x, vec.y, vec.z])
        
    return sampledColorArray


# Node declaration

class transferNode(om.MPxNode):
    id = om.MTypeId(0x81170)

    # Input attributes
    aColor1 = None
    inputMesh = None

    # Output attributes
    aOutColor = None
    weights = None

    def __init__(self):
        om.MPxNode.__init__(self)

    @staticmethod
    def creator():
        return transferNode()

    @staticmethod
    def initialize():
        nAttr = om.MFnNumericAttribute()
        tAttr = om.MFnTypedAttribute()

        # Input attributes
        transferNode.aColor1 = nAttr.createColor("colorIn", "ci")
        nAttr.keyable = True
        nAttr.storable = True
        nAttr.readable = True
        nAttr.writable = True

        # mesh input
        transferNode.inputMesh = tAttr.create("inputMesh", "im", om.MFnData.kMesh)
        tAttr.storable = False
        tAttr.writable = True
        tAttr.readable = True
        tAttr.keyable = False
        tAttr.hidden = False
        tAttr.connectable = True

        # color channel chooser
        enumAttr = om.MFnEnumAttribute()
        transferNode.channelChooser = enumAttr.create("channelChooser", "cc")
        enumAttr.addField("Red", 0)
        enumAttr.addField("Green", 1)
        enumAttr.addField("Blue", 2)
        enumAttr.addField("Average", 3)
        enumAttr.addField("Luminance", 4)
        enumAttr.default = 0

        # Output attributes
        transferNode.aOutColor = nAttr.createColor("outColor", "oc")
        nAttr.keyable = False
        nAttr.storable = False
        nAttr.readable = True
        nAttr.writable = False

        # add weightMap attribute
        weightAttr = om.MFnNumericAttribute()
        transferNode.weights = weightAttr.create("weights", "wm", om.MFnNumericData.kFloat, 1.0)
        weightAttr.setMin(0.0)
        weightAttr.setMax(1.0)
        weightAttr.array = True
        weightAttr.usesArrayDataBuilder = True
        weightAttr.keyable = False
        weightAttr.storable = False
        weightAttr.readable = True
        weightAttr.writable = False

        # Add attributes to the node database.
        om.MPxNode.addAttribute(transferNode.aColor1)
        om.MPxNode.addAttribute(transferNode.inputMesh)

        om.MPxNode.addAttribute(transferNode.aOutColor)
        om.MPxNode.addAttribute(transferNode.weights)

        om.MPxNode.addAttribute(transferNode.channelChooser)

        # All input affect the output color
        om.MPxNode.attributeAffects(transferNode.aColor1, transferNode.aOutColor)
        om.MPxNode.attributeAffects(transferNode.inputMesh, transferNode.weights)
        om.MPxNode.attributeAffects(transferNode.aColor1, transferNode.weights)
        om.MPxNode.attributeAffects(transferNode.channelChooser, transferNode.weights)

    def compute(self, plug, block):
        if plug == transferNode.aOutColor:
            # colours
            surfaceColor1 = block.inputValue(transferNode.aColor1).asFloatVector()
            resultColor = surfaceColor1

            outColorHandle = block.outputValue(transferNode.aOutColor)
            outColorHandle.setMFloatVector(resultColor)
            outColorHandle.setClean()

        elif plug == transferNode.weights:
            # weightmap
            mesh_data = block.inputValue(transferNode.inputMesh)
            mesh = mesh_data.asMesh()

            meshPlug = om.MPlug(self.thisMObject(), transferNode.inputMesh)
            if meshPlug.isConnected:
                sourcePlug = meshPlug.source()
                meshNode = sourcePlug.node()
                meshName = om.MFnDependencyNode(meshNode).name()
                transformName = cmds.listRelatives(meshName, parent=True)[0]

            else:
                om.MGlobal.displayError("inputMesh is not connected to a mesh node")

            meshFn = om.MFnMesh(mesh)
            array_data_handle = block.outputArrayValue(transferNode.weights)
            points = meshFn.getPoints(om.MSpace.kObject)
            numPoints = len(points)

            shadingPlug = om.MPlug(self.thisMObject(), transferNode.aColor1)
            if shadingPlug.isConnected:
                connectedPlug = shadingPlug.source()
                shadingNode = connectedPlug.node()
                shadingName = om.MFnDependencyNode(shadingNode).name()
            else:
                om.MGlobal.displayError("aColor1 is not connected to a shading node")
                return

            sampledColors = sampleColor2D(f"{shadingName}.outColor", transformName)


            array_builder = om.MArrayDataBuilder(block, transferNode.weights, numPoints)

            output_array_handle = array_data_handle.builder()
            om.MGlobal.displayInfo("Data size: " + str(numPoints))

            mode = block.inputValue(transferNode.channelChooser).asShort()

            for i in range(0, numPoints):
                child = array_builder.addLast()
                if mode == 0:
                    child.setFloat(sampledColors[i][0])
                elif mode == 1:
                    child.setFloat(sampledColors[i][1])
                elif mode == 2:
                    child.setFloat(sampledColors[i][2])
                elif mode == 3:
                    child.setFloat((sampledColors[i][0] + sampledColors[i][1] + sampledColors[i][2]) / 3.0)
                elif mode == 4:
                    child.setFloat(
                        (0.299 * sampledColors[i][0] + 0.587 * sampledColors[i][1] + 0.114 * sampledColors[i][2]))

            array_data_handle.set(array_builder)
            array_data_handle.setAllClean()
            block.setClean(plug)

        else:
            raise RuntimeError("Invalid plug")

        return self

    def postConstructor(self):
        pass


# ## Override declaration
# ###########################
# The transferNodeOverride class is used to create a custom shading node override, fix last
class transferNodeOverride(omr.MPxShadingNodeOverride):
    @staticmethod
    def creator(obj):
        return transferNodeOverride(obj)

    def __init__(self, obj):
        omr.MPxShadingNodeOverride.__init__(self, obj)

        # Register fragment with manager
        fragmentMgr = omr.MRenderer.getFragmentManager()
        if fragmentMgr is not None:
            if not fragmentMgr.hasFragment("transferNodePluginFragment"):
                fragmentBody = "<fragment uiName=\"transferNodePluginFragment\" name=\"transferNodePluginFragment\" type=\"plumbing\" class=\"ShadeFragment\" version=\"1.0\">"
                fragmentBody += "   <description><![CDATA[color pass through procedural texture fragment]]></description>"
                fragmentBody += "   <properties>"
                fragmentBody += "       <float3 name=\"colorIn\" />"
                fragmentBody += "   </properties>"
                fragmentBody += "   <values>"
                fragmentBody += "       <float3 name=\"colorIn\" value=\"0.75,0.3,0.1\" />"
                fragmentBody += "   </values>"
                fragmentBody += "   <outputs>"
                fragmentBody += "       <float3 name=\"outColor\" />"
                fragmentBody += "   </outputs>"
                fragmentBody += "   <implementation>"
                fragmentBody += "   <implementation render=\"OGSRenderer\" language=\"Cg\" lang_version=\"2.1\">"
                fragmentBody += "       <function_name val=\"transferNodePluginFragment\" />"
                fragmentBody += "       <source><![CDATA["
                # Cg
                fragmentBody += "float3 transferNodePluginFragment(float3 colorIn) \n"
                fragmentBody += "{ \n"
                fragmentBody += "   return colorIn; \n"
                fragmentBody += "} \n"
                fragmentBody += "]]></source>"
                fragmentBody += "   </implementation>"
                fragmentBody += "   <implementation render=\"OGSRenderer\" language=\"HLSL\" lang_version=\"11.0\">"
                fragmentBody += "       <function_name val=\"transferNodePluginFragment\" />"
                fragmentBody += "       <source><![CDATA["
                # HSLS
                fragmentBody += "float3 transferNodePluginFragment(float3 colorIn) \n"
                fragmentBody += "{ \n"
                fragmentBody += "   return colorIn; \n"
                fragmentBody += "} \n"
                fragmentBody += "]]></source>"
                fragmentBody += "   </implementation>"
                fragmentBody += "   <implementation render=\"OGSRenderer\" language=\"GLSL\" lang_version=\"3.0\">"
                fragmentBody += "       <function_name val=\"transferNodePluginFragment\" />"
                fragmentBody += "       <source><![CDATA["
                # GLSL
                fragmentBody += "vec3 transferNodePluginFragment(vec3 colorIn) \n"
                fragmentBody += "{ \n"
                fragmentBody += "   return colorIn; \n"
                fragmentBody += "} \n"
                fragmentBody += "]]></source>"
                fragmentBody += "   </implementation>"
                fragmentBody += "   </implementation>"
                fragmentBody += "</fragment>"

                # Register the fragment in the fragment manager
                fragmentMgr.addShadeFragmentFromBuffer(fragmentBody.encode('utf-8'), False)

    def supportedDrawAPIs(self):
        return omr.MRenderer.kOpenGL | omr.MRenderer.kOpenGLCoreProfile | omr.MRenderer.kDirectX11

    def fragmentName(self):
        return "transferNodePluginFragment"


##
## Plugin setup
######################################################
sRegistrantId = "transferPlugin_py"


def initializePlugin(obj):
    plugin = om.MFnPlugin(obj, "Robin", "1.0", "Any")
    try:
        userClassify = "texture/2d:drawdb/shader/texture/2d/transfer_py"
        plugin.registerNode("transfer_py", transferNode.id, transferNode.creator, transferNode.initialize,
                            om.MPxNode.kDependNode, userClassify)
    except:
        sys.stderr.write("Failed to register node\n")
        raise

    try:
        global sRegistrantId
        omr.MDrawRegistry.registerShadingNodeOverrideCreator("drawdb/shader/texture/2d/transfer_py", sRegistrantId,
                                                             transferNodeOverride.creator)
    except:
        sys.stderr.write("Failed to register override\n")
        raise

    print("transferNode plugin loaded")


def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    try:
        plugin.deregisterNode(transferNode.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
        raise

    try:
        global sRegistrantId
        omr.MDrawRegistry.deregisterShadingNodeOverrideCreator("drawdb/shader/texture/2d/transfer_py", sRegistrantId)
    except:
        sys.stderr.write("Failed to deregister override\n")
        raise

    print("transferNode plugin unloaded\n")
