import os
import shutil
import maya.cmds as cmds

PLUGIN_NAME = "transferNode.py"  
SCRIPTS_DIR_NAME = "scripts" 
USER_SETUP_PATH = os.path.join(cmds.internalVar(userAppDir=True), "userSetup.py") 

def install_plugin():
    # maya script directory
    scripts_dir = cmds.internalVar(userScriptDir=True)
    general_dir = scripts_dir.split("scripts")[0]
    # Check if there is a plugin directory
    plugin_dir = os.path.join(general_dir, "plug-ins")
    if not os.path.exists(plugin_dir):
        os.makedirs(plugin_dir)
        print(f"Created directory: {plugin_dir}")
    else:
        print(f"Directory already exists: {plugin_dir}")

    print(f"Plugin directory: {plugin_dir}")

    user_app_dir = cmds.internalVar(userAppDir=True)
    plugin_source = os.path.join(os.path.dirname(__file__), PLUGIN_NAME)

    # Copy plugin to scripts directory
    plugin_dest = os.path.join(plugin_dir, PLUGIN_NAME)
    if not os.path.exists(plugin_dest):
        shutil.copy(plugin_source, plugin_dest)
        print(f"{PLUGIN_NAME} installed successfully.")
    else:
        print(f"{PLUGIN_NAME} already exists in the scripts directory.")

    # Check if userSetup.py exists and add plugin import
    if os.path.exists(USER_SETUP_PATH):
        with open(USER_SETUP_PATH, "a") as file:
            file.write(f'\nimport {PLUGIN_NAME[:-3]}\n') 
            print(f"Added {PLUGIN_NAME} to userSetup.py for auto-loading.")
    else:
        print(f"please turn on auto-load for {PLUGIN_NAME}")


def onMayaDroppedPythonFile(*args):
    """
    This function is called when the script is dropped into Maya.
    It installs the plugin and adds it to userSetup.py.
    """
    try:
        install_plugin()
        print("Plugin installed successfully.")
    except Exception as e:
        print(f"Error installing plugin: {e}")
    
