"""Upgrade native annotation anchors to adjustable VP2 text, including saved lessons."""
from pathlib import Path
from maya import cmds

TYPE_NAME = 'week05TeachingLabel'
DEFAULT_SIZE = 24


def ensure(demo, size=DEFAULT_SIZE):
    path = str(Path(__file__).with_name('viewport_labels_plugin.py'))
    # Inspect the loaded registry, not the filesystem path. Resolving an untrusted
    # path can invoke Maya's security checks even when we only want load status.
    # Python module reloads do not require reloading the registered Maya plug-in.
    loaded = cmds.pluginInfo(query=True, listPlugins=True) or []
    if 'viewport_labels_plugin' not in loaded:
        cmds.loadPlugin(path, quiet=True)
    for source in cmds.ls(demo.namespace+':*', type='annotationShape') or []:
        parent = cmds.listRelatives(source, parent=True, fullPath=True)[0]
        target = source + '_readable'
        if not cmds.objExists(target):
            target = cmds.createNode(TYPE_NAME, name=target, parent=parent)
            cmds.connectAttr(source+'.text',target+'.labelText')
            cmds.connectAttr(source+'.overrideColorRGB',target+'.labelColor')
        cmds.setAttr(target+'.fontSize',size)
        cmds.setAttr(source+'.visibility',False)


def set_size(demo, size):
    for label in cmds.ls(demo.namespace+':*', type=TYPE_NAME) or []:
        cmds.setAttr(label+'.fontSize',int(size))
    cmds.refresh(force=True)
