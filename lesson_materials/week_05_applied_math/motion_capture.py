"""Record reproducible teaching motions with a fixed camera and restore state."""
import json,math
from pathlib import Path
from datetime import datetime,timezone
from maya import cmds,OpenMayaUI
from . import viewport_labels


def choices(demo):
    if demo.mode=='vectors':
        result=['Translate the points together']
        if demo.topic in ('Dot / alignment','Dot / projection','Cross / plane','Vectors'):
            result.append('Turn the second vector')
        return result
    if getattr(demo,'space_case',None):
        return ['Move the reference frame']
    if demo.mode=='rotations':
        return ['Rotate the parent','Scale the object','Position interpolation','Euler interpolation','Quaternion interpolation']
    return []


def record(window, recipe, directory, frames=72, fps=12, size=(1280,720), progress=None):
    """Export a looping GIF, original PNG frames and exact per-frame values.

    Motions use the active lesson. Connected or keyed inputs are rejected rather
    than overwritten. The fixed camera includes a framing margin for the sweep.
    """
    if cmds.about(batch=True):raise RuntimeError('Motion capture requires interactive Maya.')
    demo=window.demo
    if recipe not in choices(demo):raise ValueError('Choose a motion supported by this lesson.')
    if frames<4 or fps<=0:raise ValueError('Use at least four frames and positive fps.')
    active_timer=window.timer.isActive()
    nodes=[demo.root,*demo.points,demo.hand,demo.rotation_parent]
    if getattr(demo,'space_case',None):nodes += [demo.space_frame,demo.space_point]
    nodes=list(dict.fromkeys(n for n in nodes if cmds.objExists(n)))
    state={n:{a:cmds.getAttr(n+'.'+a)[0] for a in ('translate','rotate','scale')} for n in nodes}
    affected=([demo.root] if recipe=='Translate the points together' else
              [demo.points[2]] if recipe=='Turn the second vector' else
              [demo.space_frame] if recipe=='Move the reference frame' else
              [demo.rotation_parent] if recipe=='Rotate the parent' else [demo.hand])
    channel=('translate' if recipe in ('Translate the points together','Turn the second vector','Move the reference frame','Position interpolation')
             else 'scale' if recipe=='Scale the object' else 'rotate')
    plugs=[node+'.'+channel+axis for node in affected for axis in 'XYZ']
    if recipe in ('Euler interpolation','Quaternion interpolation'):plugs.append(demo.hand+'.translateX')
    for plug in plugs:
            if cmds.getAttr(plug,lock=True) or cmds.listConnections(plug,source=True,destination=False):
                raise RuntimeError('Restore an unkeyed lesson before capture: '+plug)
    folder=Path(directory).expanduser().resolve()/('week05_motion_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    folder.mkdir(parents=True,exist_ok=False)
    camera=demo.camera;camera_matrix=cmds.xform(camera,q=True,ws=True,matrix=True)
    camera_attrs={a:cmds.getAttr(camera+'.'+a) for a in ('orthographic','orthographicWidth','centerOfInterest')}
    selection=cmds.ls(sl=True,long=True) or [];undo=cmds.undoInfo(q=True,state=True)
    gradient=cmds.displayPref(q=True,displayGradient=True);background=cmds.displayRGBColor('background',q=True)
    settings={};paths=[];samples=[]
    def move(t):
        if recipe=='Translate the points together':
            p=state[demo.root]['translate'];cmds.setAttr(demo.root+'.translate',p[0]+2*t,p[1]+t,p[2])
        elif recipe=='Turn the second vector':
            e=state[demo.points[1]]['translate'];w=state[demo.points[2]]['translate'];dx,dy=w[0]-e[0],w[1]-e[1]
            theta=math.pi*1.25*t;c,s=math.cos(theta),math.sin(theta)
            cmds.setAttr(demo.points[2]+'.translate',e[0]+dx*c-dy*s,e[1]+dx*s+dy*c,w[2])
        elif recipe=='Move the reference frame':
            p=state[demo.space_frame]['translate'];cmds.setAttr(demo.space_frame+'.translate',p[0]+2*t,p[1],p[2])
        elif recipe=='Rotate the parent':
            r=state[demo.rotation_parent]['rotate'];cmds.setAttr(demo.rotation_parent+'.rotate',r[0],r[1],r[2]+90*t)
        elif recipe=='Scale the object':
            cmds.setAttr(demo.hand+'.scale',*(v*(1+t) for v in state[demo.hand]['scale']))
        elif recipe=='Position interpolation':cmds.setAttr(demo.hand+'.translateX',4*t)
        else:demo.interpolate(t,'euler' if recipe=='Euler interpolation' else 'slerp')
        demo.update_point_labels()
        if demo.mode=='vectors':
            for label,node in zip('SEW',demo.points):
                value=cmds.xform(node,q=True,ws=True,t=True)
                # Moving numeric strings distract from the invariant and can
                # collide with markers. Exact coordinates remain in capture.json.
                text=label
                cmds.setAttr(demo.name(label+'_labelShape')+'.text',text,type='string')
    try:
        window.stop_preview();window.timer.stop()
        cmds.undoInfo(stateWithoutFlush=False)
        move(.5);window.frame()
        # A fixed frame prevents the auto-fit from making scale appear unchanged.
        if cmds.getAttr(camera+'.orthographic'):
            cmds.setAttr(camera+'.orthographicWidth',cmds.getAttr(camera+'.orthographicWidth')*(1.9 if demo.mode=='vectors' else 1.35))
        else:
            from maya.api import OpenMaya as om
            m=om.MMatrix(cmds.xform(camera,q=True,ws=True,matrix=True));back=om.MVector(0,0,cmds.getAttr(camera+'.centerOfInterest')*.5)*m
            p=cmds.xform(camera,q=True,ws=True,t=True);cmds.xform(camera,ws=True,t=[p[i]+back[i] for i in range(3)])
        viewport_labels.ensure(demo,window.label_size.value())
        view=OpenMayaUI.M3dView();OpenMayaUI.M3dView.getM3dViewFromModelPanel(window.panel,view)
        factor=size[1]/max(1,view.portHeight())
        for n in cmds.ls(demo.namespace+':*',type=viewport_labels.TYPE_NAME) or []:
            plug=n+'.fontSize';settings[plug]=cmds.getAttr(plug);cmds.setAttr(plug,min(180,max(20,round(settings[plug]*factor))))
            # The camera Y label projects onto the world axes in this observer
            # view. Its green axis remains visible; suppress only the label.
            if 'space_YfShape' in n and str(getattr(demo,'space_case','')).startswith('camera'):
                plug=n+'.visibility';settings[plug]=cmds.getAttr(plug);cmds.setAttr(plug,False)
        for n in cmds.ls(demo.namespace+':*',type='nurbsCurve') or []:
            if cmds.attributeQuery('lineWidth',node=n,exists=True):
                plug=n+'.lineWidth';settings[plug]=cmds.getAttr(plug);cmds.setAttr(plug,max(2,2*factor))
        for attr,value in [('multiSampleEnable',True),('multiSampleCount',8)]:
            plug='hardwareRenderingGlobals.'+attr;settings[plug]=cmds.getAttr(plug);cmds.setAttr(plug,value)
        cmds.displayPref(displayGradient=False);cmds.displayRGBColor('background',0,0,0);cmds.select(clear=True)
        for i in range(frames):
            if progress and progress(i,frames) is False:raise RuntimeError('Capture cancelled; completed PNG frames are retained.')
            # Hold each endpoint, then travel out and back with smooth joins.
            phase=i/frames
            t=(0 if phase<.1 else .5-.5*math.cos(math.pi*(phase-.1)/.35) if phase<.45 else
               1 if phase<.55 else .5+.5*math.cos(math.pi*(phase-.55)/.35) if phase<.9 else 0)
            move(t);cmds.refresh(force=True)
            dest=folder/('frame_%04d.png'%i)
            cmds.playblast(editorPanelName=window.panel,format='image',compression='png',frame=cmds.currentTime(q=True),completeFilename=str(dest),viewer=False,showOrnaments=False,widthHeight=size,percent=100,offScreen=True)
            if not dest.is_file():raise RuntimeError('Maya did not write '+str(dest))
            paths.append(dest)
            samples.append({'frame':i,'progress':t,'points':[cmds.xform(p,q=True,ws=True,t=True) for p in demo.points],
                            'hand_world_matrix':cmds.getAttr(demo.hand+'.worldMatrix[0]'),
                            'reference_matrix':cmds.getAttr(demo.space_frame+'.worldMatrix[0]') if getattr(demo,'space_case',None) else None})
    finally:
        for n,attrs in state.items():
            for a,value in attrs.items():
                for axis,v in zip('XYZ',value):
                    plug=n+'.'+a+axis
                    if not cmds.getAttr(plug,lock=True) and not cmds.listConnections(plug,s=True,d=False):cmds.setAttr(plug,v)
        for plug,value in settings.items():cmds.setAttr(plug,value)
        cmds.xform(camera,ws=True,matrix=camera_matrix)
        for a,value in camera_attrs.items():cmds.setAttr(camera+'.'+a,value)
        cmds.displayPref(displayGradient=gradient);cmds.displayRGBColor('background',*background)
        cmds.select([n for n in selection if cmds.objExists(n)],replace=True)
        cmds.undoInfo(stateWithoutFlush=undo);window.refresh();cmds.refresh(force=True)
        if active_timer:window.timer.start()
    from .gif_export import from_pngs
    gif=folder/'animation.gif';from_pngs(paths,gif,fps)
    metadata={'created':datetime.now(timezone.utc).isoformat(),'source':'Actual Maya viewport capture','maya':cmds.about(version=True),
              'recipe':recipe,'lecture_step':window.lecture_step.currentText(),'variation':window.variation.currentText(),'fps':fps,'gif_frame_delay_ms':round(100/fps)*10,
              'source_size':size,'frames':samples,'credit':'Prof. Monteagudo course visualizer','processing':'Fixed camera, PNG frames, one content-union crop with 50 px margin for every GIF frame, Qt palette quantization, looping GIF. Timing eases and holds endpoints.'}
    (folder/'capture.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    (folder/'preview.html').write_text('<!doctype html><meta charset="utf-8"><title>'+recipe+'</title><body style="background:#111;color:white;font:20px sans-serif"><h1>'+recipe+'</h1><img style="max-width:100%" src="animation.gif"><p>Actual Maya viewport capture. Original PNG frames and values are stored alongside this file.</p>',encoding='utf-8')
    return gif
