"""Capture the dedicated viewport with a sidecar of known inputs and provenance."""

import json
from datetime import datetime, timezone
from pathlib import Path

from maya import cmds


def still(demo, panel, directory, frame=None):
    if cmds.about(batch=True):
        raise RuntimeError("Viewport capture requires interactive Maya.")
    folder = Path(directory).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)
    name = "week05_{}_{}".format(demo.mode, datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    target = folder / (name + ".png")
    raw_target = folder / (name + "_raw.png")
    if target.exists():
        raise FileExistsError(target)
    # Remove selection manipulators from teaching captures, then restore the user's selection.
    selection=cmds.ls(selection=True,long=True) or []
    from . import viewport_labels
    from maya import OpenMayaUI
    from PySide6 import QtGui
    import numpy as np
    viewport_labels.ensure(demo, next((cmds.getAttr(n+'.fontSize') for n in cmds.ls(demo.namespace+':*',type=viewport_labels.TYPE_NAME) or []), viewport_labels.DEFAULT_SIZE))
    camera=demo.camera
    camera_matrix=cmds.xform(camera,q=True,worldSpace=True,matrix=True)
    ortho=cmds.camera(camera,q=True,orthographic=True)
    ortho_width=cmds.camera(camera,q=True,orthographicWidth=True)
    interest=cmds.camera(camera,q=True,centerOfInterest=True)
    gradient=cmds.displayPref(q=True,displayGradient=True)
    background=cmds.displayRGBColor('background',q=True)
    settings={}
    undo_enabled=cmds.undoInfo(q=True,state=True)
    try:
        cmds.undoInfo(stateWithoutFlush=False)
        demo.update_point_labels()
        if frame:frame()
        # Spend more of the render on geometry before trimming the outer margin.
        if cmds.camera(camera,q=True,orthographic=True):
            cmds.camera(camera,e=True,orthographicWidth=cmds.camera(camera,q=True,orthographicWidth=True)*.9)
        view=OpenMayaUI.M3dView()
        OpenMayaUI.M3dView.getM3dViewFromModelPanel(panel,view)
        scale=2160/max(1,view.portHeight())
        for n in cmds.ls(demo.namespace+':*',type=viewport_labels.TYPE_NAME) or []:
            settings[n+'.fontSize']=cmds.getAttr(n+'.fontSize')
            cmds.setAttr(n+'.fontSize',min(240,round(settings[n+'.fontSize']*scale)))
        for n in cmds.ls(demo.namespace+':*',type='nurbsCurve') or []:
            if cmds.attributeQuery('lineWidth',node=n,exists=True):
                settings[n+'.lineWidth']=cmds.getAttr(n+'.lineWidth')
                cmds.setAttr(n+'.lineWidth',max(2,2*scale))
        for attr,value in [('multiSampleEnable',True),('multiSampleCount',8)]:
            plug='hardwareRenderingGlobals.'+attr
            settings[plug]=cmds.getAttr(plug)
            cmds.setAttr(plug,value)
        cmds.displayPref(displayGradient=False)
        cmds.displayRGBColor('background',0,0,0)
        cmds.select(clear=True)
        cmds.refresh(force=True)
        cmds.playblast(
            editorPanelName=panel,
            format="image",
            compression="png",
            frame=cmds.currentTime(query=True),
            completeFilename=str(raw_target),
            viewer=False,
            showOrnaments=False,
            widthHeight=(3840, 2160),
            percent=100,
            offScreen=True,
        )
    finally:
        for plug,value in settings.items():cmds.setAttr(plug,value)
        cmds.xform(camera,worldSpace=True,matrix=camera_matrix)
        cmds.camera(camera,e=True,orthographic=ortho,orthographicWidth=ortho_width,centerOfInterest=interest)
        cmds.displayPref(displayGradient=gradient)
        cmds.displayRGBColor('background',*background)
        cmds.select([node for node in selection if cmds.objExists(node)],replace=True)
        cmds.undoInfo(stateWithoutFlush=undo_enabled)
        cmds.refresh(force=True)
    if not raw_target.is_file():
        raise RuntimeError("Maya did not write the requested capture.")
    source=QtGui.QImage(str(raw_target)).convertToFormat(QtGui.QImage.Format_RGBA8888)
    if source.isNull():raise RuntimeError('Cannot read the viewport capture.')
    pixels=np.frombuffer(source.constBits(),dtype=np.uint8).reshape(source.height(),source.bytesPerLine())[:,:source.width()*4].reshape(source.height(),source.width(),4)
    ys,xs=np.where(np.any(pixels[:,:,:3]>20,axis=2))
    if not len(xs):raise RuntimeError('The capture is empty; raw image kept for inspection.')
    margin=max(48,round(max(xs.max()-xs.min(),ys.max()-ys.min())*.045))
    x0=max(0,int(xs.min())-margin);y0=max(0,int(ys.min())-margin)
    x1=min(source.width(),int(xs.max())+margin+1);y1=min(source.height(),int(ys.max())+margin+1)
    if not source.copy(x0,y0,x1-x0,y1-y0).save(str(target)):
        raise RuntimeError('Cannot save the cropped slide capture.')
    data = dict(
        created=datetime.now(timezone.utc).isoformat(),
        maya=cmds.about(version=True),
        source="Instructor-generated Week 5 Maya scene",
        namespace=demo.namespace,
        mode=demo.mode,
        overlay=demo.topic,
        arm_mode=("IK" if cmds.getAttr(demo.ik + ".ikBlend") > 0.5 else "FK") if demo.mode == "arm" else None,
        readout=demo.readout(),
        image=target.name,
        credit="Prof. Monteagudo — Week 5 Applied Math Maya demo",
        code=str(Path(__file__).resolve().parent),
        edited=True,
        processing='High-resolution viewport render with scaled labels, antialiased thicker curves, black background, and empty-margin crop; no upscaling.',
        raw_image=raw_target.name,
        raw_size=[source.width(),source.height()],
        crop_bounds=[x0,y0,x1,y1],
        image_size=[x1-x0,y1-y0],
    )
    if demo.mode=="rotations":
        data["hand_local_matrix"]=cmds.getAttr(demo.hand+".matrix")
        data["hand_world_matrix"]=cmds.getAttr(demo.hand+".worldMatrix[0]")
    prop=demo.name("attachment_prop")
    if demo.mode=="arm" and cmds.objExists(prop) and cmds.getAttr(prop+".visibility"):
        data["attachment"]={"mode":cmds.getAttr(prop+".attachmentMode"),"world_matrix":cmds.getAttr(prop+".worldMatrix[0]")}
    target.with_suffix(".json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    return target
