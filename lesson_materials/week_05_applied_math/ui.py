"""Qt controls and math display surrounding a native Maya viewport."""
import math
import time
from maya import cmds, OpenMayaUI
from . import scene, calculations, presentation, help_content, lecture, viewport_labels, spaces

WINDOW = "week05MathWindow"
_instance = None
MODES = ["vectors", "arm", "rotations"]
TOPICS = ["Step 1: S to E", "Vectors", "Normalize", "Dot / alignment", "Dot / projection", "Cross / plane"]
ATTACHMENTS = ["World (unattached)", "Hierarchy parent", "Point constraint", "Orient constraint", "Parent constraint"]
EXAMPLES = [
    ("Step 1: one vector (S to E)", "Bent arm", "Start with two positions: S and E. The teal displacement is a = E - S."),
    ("Two connected vectors", "Bent arm", "S is the tail of a; E joins a to b; W is the head of b. The arrows are a and b; green is their sum."),
    ("Right angle: dot = 0", "Perpendicular", "The arrows meet at 90 degrees. Their dot product is zero."),
    ("Same direction: cross = 0", "Straight", "Both arrows point the same way. Cross = 0; no unique plane normal."),
    ("Return to start: W = S", "Coincident shoulder/wrist", "S and W overlap. The projection axis is undefined."),
    ("Zero vector: E = S", "Zero upper segment", "S and E overlap. The unit direction is undefined."),
]

CONTROL_TIPS = {
    "Reset lesson": "Rebuild only this lesson and restore its starting values. Separate baked takes remain in the scene.",
    "Frame view": "Fit the lesson's visible objects in the viewport. Does not change the math inputs.",
    "Restore example": "Restore the selected starting configuration and its suggested overlay.",
    "Move S": "Move the starting point S. Its label shows world coordinates.",
    "Move E": "Move point E. Its label shows world coordinates; a = E - S.",
    "Move W": "Move point W. Its label shows world coordinates; b = W - E.",
    "Move group": "Translate all points together. World positions change; displacements stay the same.",
    "Rotate group": "Rotate all points together. World components change; lengths stay the same.",
    "Move wrist target": "IK: choose the wrist position. The solver keeps the bone lengths fixed.",
    "Move elbow pole": "IK: choose the bend plane with the pink pole. This is not a surface normal.",
    "Rotate shoulder": "FK: rotate the shoulder and its elbow/wrist descendants.",
    "Rotate elbow": "FK: rotate the forearm and hand around the elbow.",
    "Rotate wrist": "FK: rotate the hand without changing the arm's reach.",
    "Move prop": "Edit translation when this link leaves it free. If driven, choose World (unattached), move, then relink.",
    "Rotate prop": "Edit rotation when this link leaves it free. If driven, choose World (unattached), rotate, then relink.",
    "Rotate hand": "Change the actual local orientation. Moving t again reapplies the interpolation formula.",
    "Rotate parent": "Change the parent frame and compare local versus world coordinates.",
    "Play preview": "Sweep t from 0 to 1 once over four seconds using the selected interpolation method.",
    "Stop": "Stop preview at the current t value.",
    "Bake comparison": "Create separate Euler and SLERP boxes keyed over 96 frames. Play them in Maya's main viewport/timeline. Lesson controls stay unkeyed.",
    "Save viewport + math": "Choose a folder for a viewport image, live values, and worked equations.",
    "? Help": "Open the complete guide with worked examples and reference links. Shortcut: F1.",
}


def show():
    global _instance
    if cmds.about(batch=True):
        raise RuntimeError("Run show() inside interactive Maya.")
    if _instance:
        _instance.close()
    _instance = Window()
    _instance.change_lecture_step()
    return _instance


class Window:
    def __init__(self):
        try:
            from PySide6 import QtCore, QtWidgets, QtGui
            from shiboken6 import wrapInstance
        except ImportError:
            from PySide2 import QtCore, QtWidgets, QtGui
            from shiboken2 import wrapInstance
        self.QtCore, self.QtWidgets, self.wrapInstance = QtCore, QtWidgets, wrapInstance
        self.demo = None
        self.session = scene.Session()
        self.worked_text = self.worked_html = ""
        self.collapsed = set()
        self._render_key = None
        self._hosts = []
        self._building = False
        self._loading_step = False
        if cmds.window(WINDOW, exists=True):
            cmds.deleteUI(WINDOW)
        cmds.window(WINDOW, title="Week 5 | Math in Maya", widthHeight=(1440,900))
        pane = cmds.paneLayout(configuration="vertical2", paneSize=(1,28,100))
        self.sidebar = self.host(cmds.formLayout())
        left = QtWidgets.QVBoxLayout(self.sidebar)
        left.setContentsMargins(8,8,8,8)
        self.controls_scroll = QtWidgets.QScrollArea()
        self.controls_scroll.setWidgetResizable(True)
        self.controls_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.controls_scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        content = QtWidgets.QWidget()
        self.controls_layout = QtWidgets.QVBoxLayout(content)
        self.controls_layout.setContentsMargins(0,0,6,0)
        self.controls_layout.setSpacing(8)
        self.controls_scroll.setWidget(content)
        left.addWidget(self.controls_scroll,1)
        self.capture_button = self.button(left,"Save viewport + math",self.capture)
        self.capture_button.setMinimumHeight(36)
        self.motion_capture_button = self.button(left,"Save animated example",self.capture_motion,
            "Record a prepared motion as a looping GIF and PNG frames. Restores the current scene inputs and camera.")
        controls = self.controls_layout
        self.lecture_step = self.combo(controls,"Lecture step",[s["label"] for s in lecture.STEPS],self.change_lecture_step)
        navigation=QtWidgets.QHBoxLayout()
        controls.addLayout(navigation)
        self.previous_step=self.button(navigation,"Previous",lambda:self.advance_step(-1))
        self.next_step=self.button(navigation,"Next",lambda:self.advance_step(1))
        self.step_notice=self.label(controls,"")
        self.variation=self.combo(controls,"Variation",[],self.load_variation)
        self.lab_button=self.button(controls,"Run student projection",self.run_lab,
                                    "Reload lab_extension.py, run your helper, and compare Student H with Reference H.")
        self.lab_status=self.label(controls,"")
        self.explore=QtWidgets.QCheckBox("Explore freely")
        self.explore.setToolTip("Show the original lesson, overlay, and example selectors. Turn off to return to the selected lecture step.")
        controls.addWidget(self.explore)
        self.explore.toggled.connect(self.change_explore)
        # Keep the original selectors available for independent experiments.
        self.lesson = self.combo(controls,"Lesson",["Vectors","Arm rig","Spaces & rotations"],self.change_lesson)
        actions=QtWidgets.QHBoxLayout()
        controls.addLayout(actions)
        self.reset_button=self.button(actions,"Restore variation",self.restore_current)
        self.button(actions,"Frame view",self.frame)
        self.camera_view=self.combo(controls,"View",["Lesson default","Ortho (flat XY)","Ortho (angled 3D)","Normal camera (perspective)"],self.change_camera_view)
        self.camera_view.setToolTip("Flat XY looks straight along Z: X is horizontal and Y is vertical. Z depth is collapsed. Lesson default uses flat XY for the early vectors and an angled view when depth matters.")
        label_row=QtWidgets.QHBoxLayout()
        controls.addLayout(label_row)
        self.label(label_row,"Label size")
        self.label_size=QtWidgets.QSpinBox()
        self.label_size.setRange(12,48)
        self.label_size.setValue(viewport_labels.DEFAULT_SIZE)
        self.label_size.setSuffix(" px")
        self.label_size.valueChanged.connect(self.change_label_size)
        label_row.addWidget(self.label_size)
        self.hint = self.label(controls,"")
        self.topic_menu = self.combo(controls,"Math overlay",TOPICS,self.change_topic)
        self.sections = {}
        self.sections["vectors"], vector_layout = self.section(controls)
        self.preset_menu = self.combo(vector_layout,"Example",[e[0] for e in EXAMPLES],self.preset)
        for index, (_, _, explanation) in enumerate(EXAMPLES):
            self.preset_menu.setItemData(index, explanation, QtCore.Qt.ToolTipRole)
        self.example_hint = self.label(vector_layout, "")
        self.restore_example=self.button(vector_layout,"Restore example",self.preset)
        self.point_buttons = []
        for i,label in enumerate(["Move S", "Move E", "Move W"]):
            self.point_buttons.append(self.button(vector_layout,label,lambda *_, index=i:self.select_point(index)))
        for button,color in zip(self.point_buttons,["#ff6666","#66ff73","#66a6ff"]):
            button.setStyleSheet("color:"+color)
        _, spaces = self.disclosure(vector_layout,"Coordinate spaces", "Spaces")
        spaces.parentWidget().setToolTip("Move all points: displacements stay the same. Rotate the group: world components change; lengths stay the same.")
        self.button(spaces,"Move group",lambda:self.select("root"))
        self.button(spaces,"Rotate group",lambda:self.select("root",True))
        self.sections["arm"], arm_layout = self.section(controls)
        self.rig_mode = self.combo(arm_layout,"Control mode",["IK","FK"],self.change_rig_mode)
        self.ik_controls, ik_layout = self.section(arm_layout)
        self.button(ik_layout,"Move wrist target",lambda:self.arm_control(True,"target"))
        self.button(ik_layout,"Move elbow pole",lambda:self.arm_control(True,"pole"))
        self.fk_controls, fk_layout = self.section(arm_layout)
        self.button(fk_layout,"Rotate shoulder",lambda:self.arm_control(False,0))
        self.button(fk_layout,"Rotate elbow",lambda:self.arm_control(False,1))
        self.button(fk_layout,"Rotate wrist",lambda:self.arm_control(False,2))
        _, attachment_layout = self.disclosure(arm_layout,"Prop attachment", "Link")
        self.attachment_check = QtWidgets.QCheckBox("Show prop")
        attachment_layout.addWidget(self.attachment_check)
        self.attachment_check.toggled.connect(self.change_attachment)
        self.attachment_mode = self.combo(attachment_layout,"Link",ATTACHMENTS,self.change_attachment)
        self.attachment_mode.setEnabled(False)
        self.attachment_check.setToolTip("Show the prop at the hand. Compare how links follow the wrist. Switching links preserves the current prop pose.")
        self.prop_move = self.button(attachment_layout,"Move prop",lambda:self.edit_prop(False))
        self.prop_rotate = self.button(attachment_layout,"Rotate prop",lambda:self.edit_prop(True))
        self.prop_note = self.label(attachment_layout, "")
        self.sections["rotations"], rotations = self.section(controls)
        self.space_buttons = [
            self.button(rotations,"Move space point P",lambda:spaces.select(self.demo,"point")),
            self.button(rotations,"Move reference frame",lambda:spaces.select(self.demo,"frame")),
            self.button(rotations,"Rotate reference frame",lambda:spaces.select(self.demo,"frame",True))]
        self.pose_buttons = [
            self.button(rotations,"Move hand",lambda:self.select("hand")),
            self.button(rotations,"Scale hand",lambda:self.scale_hand()),
            self.button(rotations,"Rotate hand",lambda:self.select("hand",True)),
            self.button(rotations,"Rotate parent",lambda:self.select("rotation_parent",True))]
        self.interpolation_controls, interpolation_layout = self.section(rotations)
        self.method = self.combo(interpolation_layout,"Interpolation",["Quaternion SLERP","Euler angle LERP"],self.interpolate)
        self.label(interpolation_layout,"Progress · t")
        self.t = QtWidgets.QDoubleSpinBox()
        self.t.setRange(0,1)
        self.t.setDecimals(3)
        self.t.setSingleStep(.05)
        interpolation_layout.addWidget(self.t)
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(0,1000)
        interpolation_layout.addWidget(self.slider)
        self.t.valueChanged.connect(self.spin_changed)
        self.slider.valueChanged.connect(lambda value:self.t.setValue(value/1000.0))
        # The comparison exercise is in Interpolation help and the slider tooltip.
        self.t.setToolTip("Progress between orientations: 0=start, 0.5=halfway, 1=end. See Help for Euler LERP versus SLERP.")
        self.slider.setToolTip(self.t.toolTip())
        playback=QtWidgets.QHBoxLayout()
        interpolation_layout.addLayout(playback)
        self.preview_button=self.button(playback,"Play preview",self.toggle_preview)
        self.button(playback,"Stop",self.stop_preview)
        self.bake_button=self.button(interpolation_layout,"Bake comparison",self.bake_animation)
        self.preview_timer=QtCore.QTimer()
        self.preview_timer.setInterval(33)
        self.preview_timer.timeout.connect(self.preview_tick)
        # Playback details live on the controls and in Interpolation help.
        self.button(left,"? Help",self.show_help)
        controls.addStretch(1)
        cmds.setParent(pane)
        right = cmds.paneLayout(configuration="horizontal2",paneSize=(1,100,55))
        self.panel = cmds.modelPanel(label="Week 5 viewport",menuBarVisible=False)
        cmds.modelEditor(self.panel,edit=True,displayAppearance="smoothShaded",grid=False,
                         displayLights="default",cameras=False,selectionHiliteDisplay=False)
        cmds.setParent(right)
        self.math_widget = self.host(cmds.formLayout())
        math_layout = QtWidgets.QVBoxLayout(self.math_widget)
        math_layout.setContentsMargins(8,4,8,4)
        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("Math display"))
        self.help_button(top, self.math_help_topic)
        top.addStretch(1)
        self.copy_result_button=self.button(top,"Copy result",lambda:self.copy_math(True),"Copy the current point values and result as plain text for a slide.")
        self.copy_math_button=self.button(top,"Copy math",self.copy_math,"Copy inputs and worked equations as plain text, with one equation per line. No HTML tables or font sizes.")
        self.explanation_toggle = QtWidgets.QToolButton()
        self.explanation_toggle.setText("Notes")
        self.explanation_toggle.setCheckable(True)
        top.addWidget(self.explanation_toggle)
        math_layout.addLayout(top)
        self.rotation_view = QtWidgets.QComboBox()
        self.rotation_view.addItems(["Local point to world point","Orientation interpolation","Position interpolation"])
        self.rotation_view.currentIndexChanged.connect(self.change_rotation_view)
        math_layout.addWidget(self.rotation_view)
        self.output = QtWidgets.QTextBrowser()
        self.output.setOpenLinks(False)
        self.output.setStyleSheet("QTextBrowser { background:#292929; border:none; padding:6px; }")
        self.output.anchorClicked.connect(self.toggle_calculation)
        math_layout.addWidget(self.output,1)
        self.explanations = QtWidgets.QTextBrowser()
        self.explanations.setMaximumHeight(145)
        self.explanations.setVisible(False)
        self.explanations.setStyleSheet("QTextBrowser { background:#333; border:none; font-size:14px; }")
        math_layout.addWidget(self.explanations)
        self.explanation_toggle.toggled.connect(self.explanations.setVisible)
        Shortcut = getattr(QtGui,"QShortcut",None) or QtWidgets.QShortcut
        self.help_shortcut=Shortcut(QtGui.QKeySequence("F1"),self.sidebar)
        self.help_shortcut.activated.connect(self.show_help)
        self.method.setToolTip("Euler LERP blends XYZ angles; quaternion SLERP blends orientations at constant angular speed. F1 opens the explanation and reference.")
        self.rig_mode.setToolTip("IK: position the wrist and bend plane. FK: rotate shoulder, elbow and wrist. Switching matches the current pose.")
        self.attachment_mode.setToolTip("Point drives position. Orient drives rotation. Parent drives both. Hierarchy also inherits scale. All links preserve the current pose when created.")
        self.preset_menu.setToolTip("Loads a starting configuration. After you move a point, the live result can differ from the preset name.")
        self.rotation_view.setToolTip("Choose a local-to-world matrix calculation or the orientation interpolation steps.")
        self.explanation_toggle.setToolTip("Show descriptions separately from equations. F1 opens the full guide.")
        cmds.showWindow(WINDOW)
        self.timer = QtCore.QTimer()
        self.timer.setInterval(150)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        cmds.scriptJob(uiDeleted=[WINDOW,self.close],runOnce=True)

    def advance_step(self, delta):
        self.lecture_step.setCurrentIndex(max(0,min(len(lecture.STEPS)-1,self.lecture_step.currentIndex()+delta)))

    def change_lecture_step(self,*_):
        if self._loading_step:return
        step=lecture.STEPS[self.lecture_step.currentIndex()]
        blocked=self.variation.blockSignals(True)
        self.variation.clear()
        self.variation.addItems([v["label"] for v in step["variations"]])
        self.variation.blockSignals(blocked)
        self.load_variation()

    def load_variation(self,*_):
        if self._loading_step or self.variation.currentIndex()<0:return
        step=lecture.STEPS[self.lecture_step.currentIndex()]
        variation=step["variations"][self.variation.currentIndex()]
        self._loading_step=True
        self.stop_preview()
        try:
            self.explore.blockSignals(True)
            self.explore.setChecked(False)
            self.explore.blockSignals(False)
            if step["mode"]=="arm":
                self.build("arm",reset=True)
            elif self.demo is None or self.demo.mode!=step["mode"] or not self.demo.healthy():
                self.build(step["mode"])
            with scene.edit_chunk("Week 5 lecture variation"):
                lecture.apply(self.demo,variation)
            viewport_labels.ensure(self.demo,self.label_size.value())
            topic=variation.get("topic","Rig only" if step["mode"]=="arm" else "Vectors")
            self.quiet_index(self.topic_menu,self.topic_menu.findText(topic))
            self.quiet_index(self.rotation_view,variation.get("view",0))
            self.quiet_index(self.method,variation.get("method",0))
            self.t.blockSignals(True);self.t.setValue(variation.get("t",0));self.t.blockSignals(False)
            self.slider.blockSignals(True);self.slider.setValue(round(self.t.value()*1000));self.slider.blockSignals(False)
            self.collapsed.clear()
            self._render_key=None
            self.point_buttons[2].setVisible(topic not in ("Step 1: S to E","Normalize"))
            self.update_navigation()
            self.frame()
            self.refresh()
        finally:
            self._loading_step=False

    def restore_current(self):
        if self.explore.isChecked():self.reset()
        else:self.load_variation()

    def change_explore(self,*_):
        if not self.explore.isChecked():self.load_variation()
        else:self.update_navigation()

    def update_navigation(self):
        free=self.explore.isChecked()
        space=bool(getattr(self.demo,"space_case",None))
        for button in self.space_buttons:button.setVisible(space)
        for button in self.pose_buttons:button.setVisible(not space)
        index=self.lecture_step.currentIndex()
        step=lecture.STEPS[index]
        lab=index==11 and not free
        self.lab_button.setVisible(lab)
        self.lab_status.setVisible(lab)
        self.lab_status.setText("Save lab_extension.py, then run. The math display remains the reference solution.")
        marker=self.demo.name("student_H")
        if cmds.objExists(marker):cmds.setAttr(marker+".visibility",False)
        self.previous_step.setEnabled(index>0)
        self.next_step.setEnabled(index<len(lecture.STEPS)-1)
        self.step_notice.setText("Explore freely · return to the lecture by unchecking above." if free else "Slides " + step["slides"] + " · " + step["notice"])
        self.lesson.field_widget.setVisible(free)
        self.topic_menu.field_widget.setVisible(free and self.demo.mode!="rotations")
        self.preset_menu.field_widget.setVisible(free)
        self.restore_example.setVisible(free)
        self.reset_button.setText("Reset lesson" if free else "Restore variation")
        self.reset_button.setToolTip("Rebuild this lesson." if free else "Restore the selected variation's starting values. Changing step or variation also loads its starting values.")
        self.rotation_view.setVisible(free and self.demo.mode=="rotations")
        view=self.rotation_view.currentIndex()
        self.interpolation_controls.setVisible(free or view in (1,2))
        self.method.field_widget.setVisible(view!=2)
        self.bake_button.setVisible(view==1)
        self.t.setToolTip("Progress: 0=start, 0.5=halfway, 1=end. " + ("Local position moves from X=0 to X=4." if view==2 else "Compare Euler LERP and quaternion SLERP."))
        self.slider.setToolTip(self.t.toolTip())

    def change_rotation_view(self,*_):
        if self.demo and self.demo.mode=="rotations":
            view=self.rotation_view.currentIndex()
            for name in ("start_pose","end_pose","rotation_labels"):
                cmds.setAttr(self.demo.name(name)+".visibility",view==1)
            self.update_navigation()
            self.refresh()

    def scale_hand(self):
        if self.require():
            cmds.select(self.demo.hand);cmds.setToolTo("Scale")

    def host(self, maya_layout):
        host = self.wrapInstance(int(OpenMayaUI.MQtUtil.findLayout(maya_layout)),self.QtWidgets.QWidget)
        widget = self.QtWidgets.QWidget(host)
        QtCore = self.QtCore
        class FillHost(QtCore.QObject):
            def eventFilter(self, watched, event):
                if event.type() in (QtCore.QEvent.Resize,QtCore.QEvent.Show):
                    widget.setGeometry(watched.rect())
                return False
        resizer = FillHost(host)
        host.installEventFilter(resizer)
        self._hosts.append((host,widget,resizer))
        widget.setGeometry(host.rect())
        widget.show()
        return widget

    def label(self, layout, text):
        label = self.QtWidgets.QLabel(text)
        label.setWordWrap(True)
        label.setMinimumWidth(0)
        layout.addWidget(label)
        return label

    def button(self, layout, text, callback, tooltip=None):
        button = self.QtWidgets.QPushButton(text)
        button.setToolTip(tooltip or CONTROL_TIPS.get(text, text))
        button.setMinimumHeight(29)
        button.clicked.connect(lambda *_:callback())
        layout.addWidget(button)
        return button

    def help_button(self, layout, topic):
        button = self.QtWidgets.QToolButton()
        button.setText("?")
        button.setToolTip("Definitions, worked examples, and references")
        button.setAccessibleName("Open topic help")
        button.clicked.connect(lambda *_: self.show_help(topic()))
        layout.addWidget(button)
        return button

    def math_help_topic(self):
        if self.demo and self.demo.mode == "rotations":
            return "Spaces" if self.rotation_view.currentIndex() == 0 else "Interpolation"
        if self.demo and self.demo.mode == "arm" and self.attachment_check.isChecked():
            return "Link"
        return self.topic_menu.currentText()

    def field_help_topic(self, label):
        if label == "View":return "View"
        if label in ("Lecture step", "Variation"):
            return self.math_help_topic()
        if label == "Math overlay":
            return self.math_help_topic()
        if label == "Lesson" and self.demo:
            return {"vectors": "Vectors", "arm": "Control mode", "rotations": "Spaces"}[self.demo.mode]
        return label

    def combo(self, layout, label, items, callback):
        field = self.QtWidgets.QWidget()
        row = self.QtWidgets.QVBoxLayout(field)
        row.setContentsMargins(0,0,0,0)
        row.setSpacing(3)
        heading=self.QtWidgets.QHBoxLayout()
        row.addLayout(heading)
        self.label(heading,label)
        help_button=self.QtWidgets.QToolButton()
        help_button.setText("?")
        help_button.setToolTip("Help for " + label)
        help_button.clicked.connect(lambda *_:self.show_help(self.field_help_topic(label)))
        heading.addWidget(help_button)
        combo = self.QtWidgets.QComboBox()
        combo.setToolTip(label + ": choose an option. See Help / documentation for definitions.")
        combo.addItems(items)
        combo.setMinimumWidth(0)
        combo.setSizePolicy(self.QtWidgets.QSizePolicy.Ignored,self.QtWidgets.QSizePolicy.Fixed)
        combo.setMinimumHeight(27)
        row.addWidget(combo)
        layout.addWidget(field)
        combo.currentIndexChanged.connect(callback)
        combo.field_widget = field
        return combo

    def section(self, layout):
        widget = self.QtWidgets.QWidget()
        inner = self.QtWidgets.QVBoxLayout(widget)
        inner.setContentsMargins(0,0,0,0)
        inner.setSpacing(7)
        layout.addWidget(widget)
        return widget,inner

    def disclosure(self, layout, title, help_topic=None):
        toggle = self.QtWidgets.QToolButton()
        toggle.setText(title)
        toggle.setCheckable(True)
        toggle.setToolButtonStyle(self.QtCore.Qt.ToolButtonTextBesideIcon)
        toggle.setArrowType(self.QtCore.Qt.RightArrow)
        heading = self.QtWidgets.QHBoxLayout()
        heading.addWidget(toggle)
        if help_topic:
            self.help_button(heading, lambda: help_topic)
        layout.addLayout(heading)
        content, inner = self.section(layout)
        content.hide()
        toggle.toggled.connect(content.setVisible)
        toggle.toggled.connect(lambda on:toggle.setArrowType(self.QtCore.Qt.DownArrow if on else self.QtCore.Qt.RightArrow))
        return toggle,inner

    def quiet_index(self, combo, index):
        blocked = combo.blockSignals(True)
        combo.setCurrentIndex(index)
        combo.blockSignals(blocked)

    def close(self,*_):
        self.stop_preview()
        if hasattr(self,"timer"):
            self.timer.stop()
        if cmds.window(WINDOW,exists=True):
            cmds.deleteUI(WINDOW)

    def change_lesson(self,*_):
        if not self._building:
            self.build(MODES[self.lesson.currentIndex()])

    def reset(self,*_):
        self.build(self.demo.mode if self.demo else "vectors",reset=True)

    def build(self, mode, reset=False):
        self.stop_preview()
        self._building=True
        try:
            self.demo=self.session.switch(mode,reset=reset)
            self.quiet_index(self.lesson,MODES.index(mode))
            for key,widget in self.sections.items():
                widget.setVisible(key==mode)
            self.rotation_view.setVisible(mode=="rotations")
            blocked=self.topic_menu.blockSignals(True)
            self.topic_menu.clear()
            self.topic_menu.addItems((["Rig only"]+TOPICS) if mode=="arm" else TOPICS)
            self.topic_menu.blockSignals(blocked)
            self.topic_menu.field_widget.setVisible(mode!="rotations")
            self.attachment_check.blockSignals(True)
            self.attachment_check.setChecked(False)
            self.attachment_check.blockSignals(False)
            self.attachment_mode.setEnabled(False)
            if mode=="arm" and cmds.objExists(self.demo.name("attachment_prop")):
                self.demo.attachment(visible=False)
            self.collapsed.clear()
            self._render_key=None
            if reset and mode=="vectors":
                self.quiet_index(self.preset_menu,0)
                self.example_hint.setToolTip(EXAMPLES[0][2])
            if reset and mode=="rotations":
                self.t.blockSignals(True); self.t.setValue(0); self.t.blockSignals(False)
                self.slider.blockSignals(True); self.slider.setValue(0); self.slider.blockSignals(False)
            if self.demo.healthy():
                self.change_topic()
                viewport_labels.ensure(self.demo,self.label_size.value())
                cmds.modelPanel(self.panel,edit=True,camera=self.demo.camera)
                selection=cmds.ls(selection=True,long=True) or []
                cmds.select(self.demo.root)
                cmds.isolateSelect(self.panel,state=True)
                cmds.isolateSelect(self.panel,loadSelected=True)
                cmds.select(selection,replace=True)
                self.frame()
        finally:
            self._building=False
        self.update_navigation()
        self.refresh()

    def require(self):
        if self.demo is None or not self.demo.healthy():
            cmds.warning("Reset this lesson to repair the incomplete fixture.")
            return False
        return True

    def change_topic(self,*_):
        if self.demo and self.demo.healthy():
            self.demo.display(self.topic_menu.currentText())
            self.point_buttons[2].setVisible(self.demo.topic not in ("Step 1: S to E", "Normalize"))
            if self.demo.mode=="vectors":
                self.example_hint.setToolTip("Length and unit direction of a = E - S." if self.demo.topic=="Normalize" else EXAMPLES[self.preset_menu.currentIndex()][2])
            self.collapsed.clear()
            self._render_key=None
            self.refresh()

    def select_point(self,i):
        if self.require() and not(i==2 and self.demo.topic in ("Step 1: S to E", "Normalize")):
            cmds.select(self.demo.points[i]);cmds.setToolTo("Move")

    def select(self,key,rotate=False):
        if self.require():
            cmds.select(getattr(self.demo,key));cmds.setToolTo("Rotate" if rotate else "Move")

    def preset(self,*_):
        if self._building or not self.require() or self.demo.mode!="vectors":
            return
        index=self.preset_menu.currentIndex()
        _,preset,explanation=EXAMPLES[index]
        self.demo.preset(preset)
        self.example_hint.setToolTip(explanation)
        topic="Step 1: S to E" if index==0 else "Dot / projection" if index in (2,4) else "Cross / plane" if index==3 else "Normalize" if index==5 else "Vectors"
        self.topic_menu.setCurrentText(topic)
        self.change_topic();self.frame()

    def change_rig_mode(self,*_):
        if self.demo and self.demo.mode=="arm" and not self._building:
            enabled=self.rig_mode.currentIndex()==0
            self.arm_control(enabled,"target" if enabled else 0)

    def arm_control(self,enabled,control):
        if self.require():
            self.demo.set_ik(enabled)
            node=self.demo.points[control] if isinstance(control,int) else getattr(self.demo,control)
            cmds.select(node);cmds.setToolTo("Move" if enabled else "Rotate")
            self.refresh()

    def ik(self,enabled):
        self.arm_control(enabled,"target" if enabled else 0)

    def change_attachment(self,*_):
        if self._building or not self.require() or self.demo.mode!="arm":
            return
        enabled=self.attachment_check.isChecked()
        self.attachment_mode.setEnabled(enabled)
        if enabled:
            self.topic_menu.setCurrentText("Rig only")
        self.demo.attachment(self.attachment_mode.currentText() if enabled else None,visible=enabled)
        viewport_labels.ensure(self.demo,self.label_size.value())
        self.topic_menu.field_widget.setVisible(not enabled)
        self._render_key=None
        self.refresh();self.frame()

    def show_help(self,topic=None):
        dialog=self.QtWidgets.QDialog(self.sidebar)
        dialog.setWindowTitle("Week 5 | Help and references")
        dialog.resize(720,650)
        layout=self.QtWidgets.QVBoxLayout(dialog)
        browser=self.QtWidgets.QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(help_content.for_topic(topic))
        layout.addWidget(browser)
        dialog.show()
        self.help_dialog=dialog

    def edit_prop(self,rotate=False):
        if not self.require() or self.demo.mode!="arm" or not self.attachment_check.isChecked():return
        prop=self.demo.name("attachment_prop")
        mode=cmds.getAttr(prop+".attachmentMode")
        allowed=("World (unattached)","Hierarchy parent","Point constraint" if rotate else "Orient constraint")
        if mode not in allowed:return
        cmds.select(prop)
        cmds.setToolTo("RotateSuperContext" if rotate else "moveSuperContext")

    def attachment_math(self,prop,mode):
        v=calculations.vector
        wrist=self.demo.points[-1]
        position=cmds.xform(prop,q=True,ws=True,t=True)
        source=cmds.xform(wrist,q=True,ws=True,t=True)
        lines=["ATTACHMENT -> "+mode,"Wrist world position = "+v(source),"Prop world position = "+v(position),"Prop world rotation (Euler) = "+v(cmds.xform(prop,q=True,ws=True,rotation=True)),"Prop local scale = "+v(cmds.getAttr(prop+".scale")[0]),"Link = "+mode]
        constraint=self.demo.name("attachment_constraint")
        if mode=="Hierarchy parent":
            lines += ["M_prop_world = M_prop_local * M_wrist_world", "Prop local translation = "+v(cmds.getAttr(prop+".translate")[0])]
        elif mode=="World (unattached)":
            lines += ["No wrist input: prop translation and rotation are independent."]
        else:
            lines += ["DRIVEN CHANNELS -> evaluated native constraint"]
            if mode=="Point constraint":
                offset=cmds.getAttr(constraint+".offset")[0]
                lines += ["p_prop = p_wrist + offset (this unrotated root)",v(source)+" + "+v(offset)+" = "+v(position),"Rotation is independent."]
            elif mode=="Orient constraint":
                lines += ["R_prop = orientConstraint(R_wrist, offset)","Offset Euler angles = "+v(cmds.getAttr(constraint+".offset")[0]),"Translation is independent."]
            else:
                lines += ["(T_prop, R_prop) = parentConstraint(M_wrist, offset)","Target offset translation = "+v(cmds.getAttr(constraint+".target[0].targetOffsetTranslate")[0]),"Target offset rotation = "+v(cmds.getAttr(constraint+".target[0].targetOffsetRotate")[0]),"Scale is not constrained."]
            for channel,output in (("translate","constraintTranslate"),("rotate","constraintRotate")):
                if cmds.attributeQuery(output,node=constraint,exists=True):
                    lines += [output+" = "+v(cmds.getAttr(constraint+"."+output)[0]),"prop local "+channel+" = "+v(cmds.getAttr(prop+"."+channel)[0])]
        lines += ["APPLICATION: Constraint outputs are native Maya solver results, not a general derivation of its solver. Positions use scene linear units; Euler angles use scene angular units."]
        return "\n".join(lines)+"\n\n"+calculations.matrix(cmds.getAttr(prop+".worldMatrix[0]"),(0,0,0),"This point is the prop origin after applying the selected link.")

    def stop_preview(self):
        if hasattr(self,"preview_timer"):self.preview_timer.stop()

    def toggle_preview(self):
        if self.demo.mode!="rotations":return
        self.t.setValue(0)
        self.preview_started=time.monotonic()
        self.preview_timer.start()

    def preview_tick(self):
        if self.demo.mode!="rotations" or not self.demo.healthy():
            self.stop_preview();return
        t=min(1,(time.monotonic()-self.preview_started)/4)
        self.t.setValue(t)
        if t>=1:self.stop_preview()

    def bake_animation(self):
        from .animation import bake_comparison
        self.stop_preview()
        group=bake_comparison(start=int(cmds.currentTime(q=True)),frames=96)
        cmds.select(group)
        self.QtWidgets.QMessageBox.information(self.sidebar,"Baked comparison",
            "Created "+group+" in the main Maya scene. Left: Euler LERP; right: quaternion SLERP.\n"
            "Select/frame the group in Maya's main viewport. Scrub from the current frame through the next 96 frames, or set that playback range and press Play.\n"
            "This take is separate from the lesson and is saved with the scene. Lesson Reset does not delete it. Samples are exact at keyed frames; in-between Euler curves approximate SLERP.")

    def spin_changed(self,*_):
        self.slider.blockSignals(True)
        self.slider.setValue(round(self.t.value()*1000))
        self.slider.blockSignals(False)
        self.interpolate()

    def interpolate(self,*_):
        if self.demo and self.demo.mode=="rotations" and not self._building and self.require():
            if self.rotation_view.currentIndex()==2:
                cmds.setAttr(self.demo.hand+".translateX",4*self.t.value())
            else:
                self.demo.interpolate(self.t.value(),"slerp" if self.method.currentIndex()==0 else "euler")
                self.rotation_view.setCurrentIndex(1)
            self.refresh()

    def change_camera_view(self,*_):
        if self.demo and not self._building:
            self.frame()

    def change_label_size(self,*_):
        if self.demo and self.demo.healthy():
            viewport_labels.ensure(self.demo,self.label_size.value())
            cmds.refresh(force=True)

    def frame(self,*_):
        if not self.require():return
        camera=cmds.modelPanel(self.panel,query=True,camera=True)
        if getattr(self.demo,"space_case",None):
            spaces.frame(self.demo, self.camera_view.currentIndex())
            return
        position_view=self.demo.mode=="rotations" and self.rotation_view.currentIndex()==2
        style=self.camera_view.currentIndex()
        if style==0:
            style=1 if self.demo.mode=="vectors" and self.demo.topic!="Cross / plane" else 2 if position_view or self.demo.topic=="Cross / plane" else 3
        if style==1:
            cmds.setAttr(self.demo.camera+".translate",0,0,20)
            cmds.setAttr(self.demo.camera+".rotate",0,0,0)
        else:
            cmds.viewPlace(camera,eye=(12,9,18),lookAt=(0,0,0))
        cmds.camera(camera,edit=True,orthographic=style!=3)
        if position_view:
            # Keep the full travel in view at every t, without adding reference boxes.
            cmds.viewPlace(camera,eye=(2,0,16) if style==1 else (2,3,16),lookAt=(2,0,0))
            if style!=3:cmds.camera(camera,edit=True,orthographicWidth=10)
            return
        selection=cmds.ls(selection=True,long=True) or []
        nodes=[self.demo.hand,self.demo.name("start_pose"),self.demo.name("end_pose")] if self.demo.mode=="rotations" else list(self.demo.points)
        if self.demo.mode=="rotations" and self.rotation_view.currentIndex()!=1: nodes=[self.demo.hand]
        if self.demo.mode=="vectors" and self.demo.topic in ("Step 1: S to E", "Normalize"): nodes=nodes[:2] + ([self.demo.name("unit_vector_display")] if self.demo.topic=="Normalize" else [])
        if self.demo.topic=="Cross / plane":nodes.append(self.demo.name("plane_normal_display"))
        if self.demo.mode=="arm":
            nodes += [self.demo.target,self.demo.pole]
            if self.attachment_check.isChecked():nodes.append(self.demo.name("attachment_prop"))
        try:
            cmds.select(nodes);cmds.refresh(force=True)
            cmds.viewFit(camera,fitFactor=.7)
        finally:
            cmds.select([x for x in selection if cmds.objExists(x)],replace=True)

    def toggle_calculation(self,url):
        if url.scheme()=="section":
            index=int(url.path())
            self.collapsed.symmetric_difference_update({index})
            self._render_key=None
            self.refresh()

    def copy_math(self,summary_only=False):
        if not self.require():return
        self.refresh()
        text=presentation.clipboard_text(self.worked_text,self.display_data,self.demo.topic,summary_only)
        # Only advertise plain text; rich HTML makes PowerPoint import the tables.
        mime=self.QtCore.QMimeData()
        mime.setText(text)
        self.QtWidgets.QApplication.clipboard().setMimeData(mime)
        button=self.copy_result_button if summary_only else self.copy_math_button
        self.QtWidgets.QToolTip.showText(button.mapToGlobal(self.QtCore.QPoint(0,button.height())),"Copied as plain text. Paste into a PowerPoint text box.",button)

    def refresh(self,*_):
        if not hasattr(self,"output") or self.demo is None:return
        if not cmds.window(WINDOW,exists=True):
            if hasattr(self,"timer"):self.timer.stop()
            return
        if not self.demo.healthy():
            self.hint.setText("Lesson incomplete — reset to repair.")
            self.hint.show()
            return
        try:
            data=self.demo.readout()
            self.demo.update_point_labels(data)
            display_data=data
            extra_notes=[]
            if self.demo.mode=="arm":
                enabled=cmds.getAttr(self.demo.ik+".ikBlend")>.5
                self.quiet_index(self.rig_mode,0 if enabled else 1)
                self.ik_controls.setVisible(enabled);self.fk_controls.setVisible(not enabled)
                hint="IK: move the wrist target or elbow pole." if enabled else "FK: rotate the shoulder, elbow or wrist rings."
                if not cmds.ikSystem(query=True,solve=True):hint="Maya's global IK solver is disabled."
                target=cmds.xform(self.demo.target,query=True,worldSpace=True,translation=True)
                worked=calculations.vectors(data,self.demo.topic,target)
                if not enabled:extra_notes.append("FK is active; the wrist target does not drive the arm.")
                if self.attachment_check.isChecked():
                    prop=self.demo.name("attachment_prop")
                    mode=cmds.getAttr(prop+".attachmentMode")
                    worked=self.attachment_math(prop,mode)
                    self.prop_move.setEnabled(mode in ("World (unattached)","Hierarchy parent","Orient constraint"))
                    self.prop_rotate.setEnabled(mode in ("World (unattached)","Hierarchy parent","Point constraint"))
                    self.prop_note.setText("Position + rotation driven" if mode=="Parent constraint" else "")
                    self.prop_note.setVisible(mode=="Parent constraint")
                    self.prop_note.setToolTip("To change the offset: choose World (unattached), edit the prop, then relink.")
                    display_data=None
                    extra_notes.append("Attachment: "+mode+". Hierarchy parenting inherits the parent's transform; point follows position, orient follows rotation, and parent constraint follows both. Constraints use maintain offset here; no scale constraint is applied.")
            elif self.demo.mode=="rotations":
                hint="Compare local/world space, or change t and the interpolation method."
                display_data=None
                if getattr(self.demo,"space_case",None):
                    worked=spaces.worked(self.demo)
                    hint="Same point, different coordinate frames. Select P or the reference frame to explore."
                elif self.rotation_view.currentIndex()==0:
                    worked=calculations.matrix(cmds.getAttr(self.demo.hand+".worldMatrix[0]"))
                elif self.rotation_view.currentIndex()==2:
                    t=self.t.value()
                    worked="POSITION INTERPOLATION -> local position\np(t) = (1 - t) p0 + t p1\np0 = (0, 0, 0)\np1 = (4, 0, 0)\nt = " + calculations.number(t) + "\np(t) = " + calculations.vector((4*t,0,0))
                    actual=cmds.getAttr(self.demo.hand+".translate")[0]
                    worked+="\np_actual = " + calculations.vector(actual)
                    extra_notes.append("The slider predicts the local object origin. Manual movement may differ; change t to reapply the interpolation.")
                else:
                    worked=calculations.interpolation(self.t.value(),"slerp" if self.method.currentIndex()==0 else "euler")
                    extra_notes.append("Left/right reference boxes show the fixed endpoint orientations. The center box is editable; manual rotation can differ from the slider prediction. Change t to reapply interpolation.")
                    q=scene.om.MTransformationMatrix(scene.om.MMatrix(cmds.getAttr(self.demo.hand+".matrix"))).rotation(asQuaternion=True)
                    worked+="\nACTUAL ORIENTATION -> center object\nq_actual (x,y,z,w) = "+calculations.vector(tuple(q))
                    worked+="\nActual current local Euler angles (scene angular units): "+calculations.vector(cmds.xform(self.demo.hand,query=True,rotation=True,objectSpace=True))
            else:
                hint="S: tail of a. E: head of a / tail of b. W: head of b. E is not necessarily a midpoint."
                if self.demo.topic=="Step 1: S to E":hint="Start with S and E: a = E - S is the displacement from start to end."
                if self.demo.topic=="Normalize":hint="Normalize uses only S and E: compare a with its unit direction u, translated left only for visibility."
                worked=calculations.movement(data,*self.demo.movement) if getattr(self.demo,"movement",None) and not self.explore.isChecked() else calculations.vectors(data,self.demo.topic)
                preset_name=EXAMPLES[self.preset_menu.currentIndex()][1]
                local=[cmds.getAttr(point+".translate")[0] for point in self.demo.points]
                edited=any(abs(a-b)>1e-6 for actual,expected in zip(local,scene.PRESETS[preset_name]) for a,b in zip(actual,expected))
                self.example_hint.setText("Modified example" if edited else "")
                self.example_hint.setVisible(edited and self.explore.isChecked())
                self.example_hint.setToolTip("The points differ from the selected preset. Restore example resets them. " + EXAMPLES[self.preset_menu.currentIndex()][2])
                extra_notes.append("S and E name positions. a = E - S is the displacement from S to E." if self.demo.topic in ("Step 1: S to E", "Normalize") else "S, E and W name positions. a = E - S and b = W - E name vectors. The green a + b arrow goes directly from the start S to the end W.")
            self.hint.setToolTip(hint)
            self.hint.setText(hint if "disabled" in hint else "")
            self.hint.setVisible(bool(self.hint.text()))
            self.worked_text=worked
            self.display_data=display_data
            self.copy_result_button.setVisible(display_data is not None)
            key=(worked,self.demo.topic,tuple(sorted(self.collapsed)),tuple(extra_notes))
            if key!=self._render_key:
                self._render_key=key
                self.worked_html=presentation.document(worked,display_data,self.demo.topic,self.collapsed)
                value=self.output.verticalScrollBar().value()
                self.output.setHtml(self.worked_html)
                self.output.verticalScrollBar().setValue(value)
                _,notes=presentation.split(worked)
                self.explanations.setPlainText("\n\n".join(extra_notes+notes))
        except (RuntimeError,ValueError) as exc:
            self.hint.setText("Lesson changed — reset to repair.")
            self.hint.setToolTip(str(exc))
            self.hint.show()

    def capture_motion(self,*_):
        if not self.require():return
        from . import motion_capture
        options=motion_capture.choices(self.demo)
        if not options:
            self.QtWidgets.QMessageBox.information(self.sidebar,"Animated example","Choose a vector or coordinate/rotation lesson first.");return
        recipe,ok=self.QtWidgets.QInputDialog.getItem(self.sidebar,"Animated example","Motion",options,0,False)
        if not ok:return
        paths=cmds.fileDialog2(fileMode=3,caption="Choose animation output folder")
        if not paths:return
        progress=self.QtWidgets.QProgressDialog("Capturing the Maya viewport…","Cancel",0,72,self.sidebar)
        progress.setWindowModality(self.QtCore.Qt.WindowModal);progress.setMinimumDuration(0)
        def update(i,total):
            progress.setValue(i);self.QtWidgets.QApplication.processEvents();return not progress.wasCanceled()
        try:
            result=motion_capture.record(self,recipe,paths[0],progress=update)
            self.QtWidgets.QMessageBox.information(self.sidebar,"Animation saved",str(result)+"\nPNG frames and capture values are saved beside the GIF.")
        except (RuntimeError,ValueError,OSError) as exc:
            self.QtWidgets.QMessageBox.warning(self.sidebar,"Animation capture",str(exc))
        finally:progress.close()

    def capture(self,*_):
        if not self.require():return
        paths=cmds.fileDialog2(fileMode=3,caption="Choose capture output folder")
        if paths:
            from .capture import still
            result=still(self.demo,self.panel,paths[0],frame=self.frame)
            self.refresh()
            result.with_suffix(".txt").write_text(self.worked_text,encoding="utf-8")
            result.with_suffix(".html").write_text(presentation.document(self.worked_text,self.display_data,self.demo.topic,interactive=False),encoding="utf-8")
            cmds.inViewMessage(amg="Saved capture: "+str(result),pos="topCenter",fade=True)

    def run_lab(self, *_):
        if not self.require():
            return
        import importlib

        from . import lab_extension

        importlib.reload(lab_extension)
        name = self.demo.name("student_H")
        if cmds.objExists(name):
            cmds.setAttr(name+".visibility",False)
        try:
            result = lab_extension.elbow_projection(*self.demo.readout()["points"])
        except NotImplementedError as exc:
            self.lab_status.setText("Complete elbow_projection in lab_extension.py, save, then run again.")
            cmds.warning(str(exc))
            return
        if result is None:
            reference=self.demo.readout()["projection"]
            self.lab_status.setText("Student H: undefined. Reference H: " + ("undefined (zero guide)." if reference is None else str(reference)))
            cmds.warning("Student projection returned undefined. Inspect the guide inputs.")
            return
        if len(result) != 3:
            self.lab_status.setText("Return three components, or None for an undefined guide.")
            cmds.warning("Return three components, or None for undefined.")
            return
        with scene.edit_chunk("Week 5 student projection"):
            if not cmds.objExists(name):
                name = cmds.spaceLocator(name=name)[0]
                cmds.parent(name, self.demo.visuals)
            cmds.xform(name, worldSpace=True, translation=result)
            cmds.setAttr(name+".visibility",True)
        self.lab_status.setText("Student H: {}\nReference H: {}\nMath display: reference solution.".format(result,self.demo.readout()["projection"]))
        print("Student H:", result, "Reference H:", self.demo.readout()["projection"])
