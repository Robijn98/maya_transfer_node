import pytest

import sys, os
import maya.standalone

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import transferNode


node_name = 'transferNode'
maya_initialized = False

def setup_module(module):
    global maya_initialized
    maya.standalone.initialize(name='python')
    maya_initialized = True
    import maya.cmds as cmds

    print("loading plugin for test")
    cmds.loadPlugin("transferNode.py")
    cmds.createNode("transfer_py", name=node_name)
    
def teardown_module(module):
    global maya_initialized
    if maya_initialized:
        maya.standalone.uninitialize()
        maya_initialized = False
        print("uninitializing maya standalone")

def test_create_node():
    import maya.cmds as cmds
    assert cmds.objExists(node_name), f"Node {node_name} does not exist after creation."
    print(f"Node {node_name} exists after creation.")

def test_node_attributes():
    import maya.cmds as cmds
    attributes = cmds.listAttr(node_name)
    assert attributes is not None, f"Node {node_name} has no attributes."
    print(f"Node {node_name} has attributes: {attributes}")

def test_node_connections():
    import maya.cmds as cmds

    # Create test node and scene
    transfer = cmds.createNode("transfer_py", name="connect_node")
    cube = cmds.polyCube(name="testCube")[0]
    dm = cmds.deltaMush(cube)[0]
    checker = cmds.shadingNode("checker", asTexture=True)
    blinn = cmds.shadingNode("blinn", asShader=True)

    # Connect attributes
    cubeShape = cmds.listRelatives(cube, shapes=True)[0]
    cmds.connectAttr(f"{cubeShape}.outMesh", f"{transfer}.inputMesh")
    cmds.connectAttr(f"{checker}.outColor", f"{transfer}.colorIn")
    cmds.connectAttr(f"{transfer}.outColor", f"{blinn}.color")

    # Check connections
    input_connections = cmds.listConnections(transfer, source=True, destination=False)
    output_connections = cmds.listConnections(transfer, source=False, destination=True)

    assert input_connections is not None, f"Node {transfer} has no input connections."

    print(f"Node {transfer} has input connections: {input_connections}")

def test_weight_attribute():
    import maya.cmds as cmds

    # Create test node and scene
    transfer = cmds.createNode("transfer_py", name="weight_node")
    cube = cmds.polyCube(name="testCube")[0]
    dm = cmds.deltaMush(cube)[0]
    checker = cmds.shadingNode("checker", asTexture=True)
    blinn = cmds.shadingNode("blinn", asShader=True)

    # Connect attributes
    cubeShape = cmds.listRelatives(cube, shapes=True)[0]
    cmds.connectAttr(f"{cubeShape}.outMesh", f"{transfer}.inputMesh")
    cmds.connectAttr(f"{checker}.outColor", f"{transfer}.colorIn")
    cmds.connectAttr(f"{transfer}.outColor", f"{blinn}.color")

    #check that output weights is 0.5
    assert cmds.getAttr(f"{transfer}.weights[0]") == 0.5, f"Node {transfer} output weights is not 0.5."

    