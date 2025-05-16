
cmake_minimum_required(VERSION 3.20)

project(transferNode)
set(PLUGINS_FOLDER ${CMAKE_CURRENT_SOURCE_DIR}/plugins)

# Copy the python files from the PythonPlugins folder to the plugins folder

file(GLOB PYTHON_PLUGINS ${CMAKE_CURRENT_SOURCE_DIR}/transferNode.py)
file(GLOB PYTHON_PLUGINS ${CMAKE_CURRENT_SOURCE_DIR}/colourNode.py)
file(GLOB PYTHON_PLUGINS ${CMAKE_CURRENT_SOURCE_DIR}/inputNode.py)

file(COPY ${PYTHON_PLUGINS} DESTINATION ${PLUGINS_FOLDER})
# add to the IDE none of these get built

add_custom_target(PythonPluginsForIDE SOURCES ${PYTHON_PLUGINS})
