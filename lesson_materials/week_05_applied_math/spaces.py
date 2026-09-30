"""Prepared coordinate frames: Maya row-vector transforms, read live from the scene."""
from maya import cmds
from maya.api import OpenMaya as om
from .calculations import vector


def clear(demo):
    demo.space_case = None
    group = demo.name('space_demo')
    if cmds.objExists(group):
        cmds.delete(group)
    for n in getattr(demo,'space_materials',[]):
        if cmds.objExists(n):cmds.delete(n)
    demo.space_materials=[]


def prepare(demo, case):
    before=set(cmds.ls(demo.namespace+':*',type='surfaceShader') or []) | set(cmds.ls(demo.namespace+':*',type='shadingEngine') or [])
    demo.space_case = case
    for name in ('start_pose','end_pose','rotation_labels'):
        cmds.setAttr(demo.name(name)+'.visibility',False)
    group = cmds.group(empty=True, name=demo.name('space_demo'), parent=demo.root)
    cmds.setAttr(demo.rotation_parent+'.visibility', False)
    frame = cmds.group(empty=True, name=demo.name('reference_frame'), parent=group)
    demo.space_frame = frame
    colors = ((1,.4,.4),(.35,1,.6),(.4,.65,1))
    def label(name, text, xyz, parent, color):
        node=cmds.createNode('transform',name=demo.name('space_'+name),parent=parent)
        cmds.setAttr(node+'.translate',*xyz)
        shape=cmds.createNode('annotationShape',name=demo.name('space_'+name+'Shape'),parent=node)
        cmds.setAttr(shape+'.text',text,type='string');cmds.setAttr(shape+'.displayArrow',False)
        cmds.setAttr(shape+'.overrideEnabled',True);cmds.setAttr(shape+'.overrideRGBColors',True)
        cmds.setAttr(shape+'.overrideColorRGB',*color)
    def axis(name, parent, end, color):
        line=cmds.curve(name=demo.name('space_'+name+'_axis'),degree=1,point=[(0,0,0),end])
        line=cmds.parent(line,parent,relative=True)[0];demo.color(line,color)
        cmds.setAttr(cmds.listRelatives(line,shapes=True)[0]+'.lineWidth',3)
        label(name,name,tuple(v*1.3 for v in end),parent,color)
    for i,name in enumerate(('Xw','Yw','Zw')):
        if i==2 and case not in ('camera','camera_moved','tangent'):continue
        end=[0,0,0];end[i]=2
        axis(name.replace(' ','_'),group,end,colors[i])
    label('origin','Ow',(0,-.65,0),group,(.85,.85,.85))
    if case in ('local','pointdir','parent'):
        cmds.setAttr(frame+'.translate',3,0,0)
    if case=='parent':cmds.setAttr(frame+'.rotateZ',90)
    if case.startswith('camera'):
        cmds.setAttr(frame+'.translate',2 if case=='camera_moved' else 1,0,6)
        cam=cmds.camera(name=demo.name('reference_camera'))[0]
        cmds.parent(cam,frame,relative=True)
        label('camera','C',(0,-.65,0),frame,(1,.8,.2))
        axis('-Z view',frame,(0,0,-3),(1,.8,.2))
        wire=cmds.curve(name=demo.name('camera_frustum'),degree=1,point=[(0,0,0),(-.6,-.4,-1),(.6,-.4,-1),(0,0,0),(.6,.4,-1),(-.6,.4,-1),(0,0,0),(-.6,-.4,-1),(-.6,.4,-1),(.6,.4,-1),(.6,-.4,-1)])
        cmds.parent(wire,frame,relative=True);demo.color(wire,(1,.8,.2))
    if case=='tangent':
        cmds.setAttr(frame+'.translate',3,0,0)
        cmds.setAttr(frame+'.rotateX',-90)
        patch=cmds.polyPlane(name=demo.name('tangent_patch'),width=3,height=3,subdivisionsX=1,subdivisionsY=1,axis=(0,0,1),constructionHistory=False)[0]
        cmds.parent(patch,frame,relative=True);demo.color(patch,(.13,.18,.22))
    names=('T','B','N') if case=='tangent' else ('Xf','Yf','Zf')
    if case!='world':
        for i,name in enumerate(names):
            if i==2 and case not in ('camera','camera_moved','tangent'):continue
            end=[0,0,0];end[i]=1.5
            axis(name.replace(' ','_'),frame,end,colors[i])
        if not case.startswith('camera'):label('frame_origin','Of',(0,-.65,0),frame,(1,.8,.2))
    point=cmds.spaceLocator(name=demo.name('space_point_P'))[0]
    cmds.parent(point,group,relative=True)
    demo.space_point=point
    if case.startswith('camera'):world=(4,2,0)
    elif case=='world':world=(1,2,0)
    else:world=tuple(om.MPoint(1,2,0)*om.MMatrix(cmds.getAttr(frame+'.worldMatrix[0]')))[:3]
    cmds.xform(point,worldSpace=True,translation=world)
    demo.color(point,(1,.8,.2))
    cmds.setAttr(point+'.localScale',.13,.13,.13)
    label('P','P',(.35,.45,0),point,(1,.8,.2))
    # Point remains independent: moving a frame changes its coordinates, not P.
    demo.space_materials=list((set(cmds.ls(demo.namespace+':*',type='surfaceShader') or []) | set(cmds.ls(demo.namespace+':*',type='shadingEngine') or []))-before)
    worked(demo)


def select(demo, role, rotate=False):
    if not getattr(demo,'space_case',None):
        cmds.warning('Choose a Coordinate spaces variation first.');return
    cmds.select(demo.space_point if role=='point' else demo.space_frame)
    cmds.setToolTo('RotateSuperContext' if rotate else 'moveSuperContext')


def worked(demo):
    p=cmds.xform(demo.space_point,q=True,ws=True,translation=True)
    matrix=om.MMatrix(cmds.getAttr(demo.space_frame+'.worldMatrix[0]'))
    local=tuple(om.MPoint(*p)*matrix.inverse())[:3]
    origin=cmds.xform(demo.space_frame,q=True,ws=True,translation=True)
    case=demo.space_case
    name='camera' if case.startswith('camera') else 'tangent' if case=='tangent' else 'reference'
    lines=['COORDINATE SPACE | origin + basis axes + units',
           'Units = '+cmds.currentUnit(q=True,linear=True),
           'Reference origin in world = '+vector(origin),
           'P_world = '+vector(p),
           'P_'+name+' = P_world * inverse(M_referenceToWorld) = '+vector(local),
           'P_world = P_'+name+' * M_referenceToWorld = '+vector(tuple(om.MPoint(*local)*matrix)[:3]),
           'The same point has different coordinates in different frames.']
    if case.startswith('camera'):
        lines += ['Maya cameras look along local -Z. Negative view Z is in front of this camera.',
                  'This is camera/view space, before perspective projection or screen pixels.']
    if case=='tangent':
        d=om.MVector(.6,.8,0)*matrix.inverse()
        lines += ['T, B, N form this surface frame. Flat teaching patch with unit scale.',
                  'Direction_world = (0.6, 0.8, 0)', 'Direction_tangent = '+vector(tuple(d))]
    if case=='pointdir':
        d=om.MVector(1,2,0)*matrix
        lines += ['Direction_reference = (1, 2, 0)', 'Direction_world = '+vector(tuple(d)),
                  'Points use w=1; directions use w=0. Translation affects only the point.']
    return '\n'.join(lines)


def frame(demo, style):
    cam=demo.camera
    flat=style==1 or (style==0 and demo.space_case not in ('camera','camera_moved','tangent'))
    cmds.viewPlace(cam,eye=(3,1,20) if flat else (14,10,19),lookAt=(2,1,2))
    if flat:cmds.setAttr(cam+'.rotate',0,0,0)
    cmds.camera(cam,edit=True,orthographic=style!=3,orthographicWidth=13)
    old=cmds.ls(selection=True,long=True) or []
    try:
        cmds.select(demo.name('space_demo'));cmds.viewFit(cam,fitFactor=.58)
    finally:cmds.select(old,replace=True) if old else cmds.select(clear=True)
