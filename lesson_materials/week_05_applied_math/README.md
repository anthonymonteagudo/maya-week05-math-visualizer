# Week 5 — Applied Math in Maya

Download or clone the repository, then open `lesson_materials/week_05_applied_math`.
Double-click **Launch Week 5.cmd** to open Maya with the tool; no Script Editor is required.
The Windows launcher expects Maya 2027 in its default installation folder. For another
installation location, use the Script Editor instructions below.
Use a centimeter scene.

See [TEACHING_CODE.md](TEACHING_CODE.md) for slide-ready excerpts from the live vector, matrix, arm hierarchy, IK, and interpolation code.
The builder checks units and leaves an incompatible scene unchanged. Maya 2027 is
the validation target; older-version compatibility is not yet certified.

Run in Maya's **Python** Script Editor:

```python
import sys

tools_root = r"C:\path\to\your\repository"  # Folder containing lesson_materials; replace this path.
if tools_root not in sys.path:
    sys.path.insert(0, tools_root)
from lesson_materials.week_05_applied_math import show

show()
```

## Class sequence

The default **Lecture step** menu follows the refreshed Week 5 deck, matching the 107-slide Student Edition, September 30 (live examples begin at slide 23).
Use **Previous / Next**, or choose a step directly. Each step has a short **Variation** menu.
Changing a step or variation loads its starting values; **Restore variation** repeats that setup.
Move a control, predict a result, then compare the viewport and math.

**View** offers Lesson default, Flat XY orthographic, Angled 3D orthographic, and
Angled 3D perspective. Early vector examples default to flat XY (X right, Y up).
Cross products default to angled orthographic so their Z normal is visible.
**Frame view** fits the example in the selected view; an explicit view choice
stays selected between steps. Flat XY collapses Z depth.

| Step | Slides | Focus |
|---|---|---|
| 01 · One displacement | 23–29 | Move S or E. Predict a = E − S, then introduce length and unit direction. |
| 02 · Two connected movements | 30 | Move E while S and W stay fixed. Does a + b change? |
| 03 · Direction and movement | 31–36 | Blue u is offset for comparison. Movement recipes show speed × time and the new position. |
| 04 · Coordinate spaces | 39–53 | A space defines an origin, basis axes and units. Move the point or reference frame; compare the same point in two spaces. |
| 05 · Dot: alignment | 56–59, 63–66 | Predict the sign of the dot product before reading the scalar and angle. |
| 06 · Projection and residual | 60–62 | Locate H on the S–W line. Check that r = E − H is perpendicular to the guide. |
| 07 · Cross: plane normal | 68–76 | Read the cross product before its unit normal. The normal arrow is drawn 3× for visibility. |
| 08 · Transforms and hierarchy | 78–88 | Change one transform. Track the yellow corner; its local coordinates are (0.9, 0.175, 0.5). |
| 09 · Orientations and rotation order | 89–93 | Compare the same two fixed-axis rotations in opposite orders. Gimbal lock and quaternion construction use the slides. |
| 10 · Position interpolation | 94 | Use t to move the object origin from local X=0 to X=4. Predict the halfway position. |
| 11 · Orientation interpolation | 95–96 | Compare Euler LERP and quaternion SLERP at the same t. The reference boxes show the endpoints. |
| 12 · Guided projection exercise | 97–101 | Edit and save lab_extension.py, then click Run student projection. Compare Student H and Reference H; check the known case and both edge cases. |
| 13 · Week 6 preview (optional) | 104 | A brief application preview. Rig construction, FK/IK, and constraints receive their deeper treatment next week. |

**Explore freely** exposes the original Lesson, Math overlay, and Example selectors.
Uncheck it to reload the selected lecture variation. The slide reference describes the lecture
route, not a claim that every slide has a live recreation. Coordinate spaces now include prepared world, local/parent, camera and tangent frames.
Material applications, gimbal lock, and several pencil-and-paper examples stay on the slides.

The dot step displays alignment alone. Projection adds its guide, H, and residual in the
following step. Matrix steps show one marked object; orientation interpolation adds the
endpoint reference boxes. Position interpolation has its own t slider and live local-position
calculation. The arm is a short optional Week 6 preview at the end.

The route is defined in `lecture.py`, separate from scene building and arithmetic, so its
numbered steps and variations can be adjusted like the Week 3 stage cards.

In step 12, **Run student projection** reloads the saved helper and places a locator
at the returned H. Its status compares **Student H** and **Reference H**. The main
math panel stays the reference solution. The starter intentionally reports that
the helper is unfinished until students implement it; return `None` for a zero
guide. Loading another example hides the previous student marker until it is run again.

## Structure

| File | Teaching / implementation role |
| --- | --- |
| `math_core.py` | Readable pure-Python vector operations, presets and guards |
| `scene.py` | Native Maya node graph, drawing, fixture and arm generation |
| `ui.py` | Manipulation shortcuts, readouts, interpolation and lab runner |
| `capture.py` | Viewport image export and provenance |
| `lab_extension.py` | Student-owned projection exercise; deliberately unfinished |

The dot angle uses consecutive S→E and E→W arrows. It is 106.26° in the default
preset; the interior elbow angle is its supplement, 73.74°. A cross-product normal
is perpendicular to the bend plane and is not a pole-control position.

The solver uses Maya's rotate-plane IK. The lab's geometric helper is not a no-flip
IK solver. A straight arm is a geometric degeneracy, distinct from Euler gimbal lock.

## Scope and recovery

The **Lesson** menu switches between Vectors, Arm rig, and Spaces & rotations.
Switching reuses each lesson and preserves its edits; other managed lessons hide.
**RESET THIS LESSON** replaces only its generated nodes with a clean setup, even
after a control is deleted. Reset is undoable. Unrelated scene objects are retained.
Reopening the UI discovers the managed lessons saved with the scene. Old fixtures
from the earlier tool are left intact; the dedicated viewport isolates the active lesson.

Arm joint translations, scales, and joint orientations are locked. Decorative
geometry is protected from ordinary selection and transforms. This does not prevent
deliberate deletion, unlocking, or graph rewiring; reset is the recovery path.
The arm does not stretch: a target beyond 10 cm gives a straight arm. A collinear
pole or fully straight arm has no unique bend plane; move the pole off the shoulder–wrist
line or reset. If Maya's global IK solver is disabled, the UI reports it.

The timer updates text only and stops with the window. Native nodes drive the
visuals, including playback. Dedicated capture camera/panel avoids changing the
artist's viewport camera. Choose one **Math overlay** at a time; the arm defaults
to **Rig only** and the marked hand appears only in Spaces & rotations.

This version does not include skinning, animation-key matching, automatic old-rig
migration, a full gimbal-ring visualizer, or material graphs. Those remain explicit
extensions. No existing Week 3 script needs changing to launch these demos.

## Teaching clarity

The **Math display** pane remains below the viewport, separate from the controls.
It follows the selected overlay and shows formula, numeric substitution, result,
and the practical interpretation. Moving Maya controls supplies the calculator's inputs.
It covers displacement/addition, magnitude/normalization, dot/angle/projection,
cross/plane normal, and arm reach. In the rotation lesson, choose local-to-world
point multiplication or Euler/quaternion interpolation. The yellow marker supplies
the local point. All values are sampled from the scene; display rounding does not
alter calculations. Capture also writes the current worked steps to a `.txt` sidecar.
This is a live worked-example calculator, not a general symbolic equation solver.

The math pane separates inputs, an emphasized live result, and calculation cards.
S/E/W labels follow their scene points. A green S-to-W arrow shows vector addition;
H marks the projection foot. IK and FK controls have separate collapsible groups.
The fixed **Save viewport + math** footer exports PNG, JSON, text, and a formatted
HTML worksheet. The math pane can scroll independently of the viewport.

Examples apply immediately and explain the expected dot/cross/undefined result. Optional coordinate-space controls move or rotate all three points together; the camera stays fixed. Euler LERP blends the three angles independently; quaternion SLERP blends orientations. Use t=0.5 to compare their different intermediate orientations. See JETTELLY_DESIGN_NOTES.md for source-page notes and scope decisions.

## Refined controls and math

The sidebar is a Qt scroll area with a fixed capture footer; the overlay selector
is near the top. In Explore freely, Vectors offers six math overlays, starting with Step 1: S to E and including Dot / alignment. Rig only is exclusive to Arm rig.
Step 1: S to E and Normalize hide W, its label, its selection manipulator, and its button. S/E/W are
positions (start/middle/end, or shoulder/elbow/wrist); a/b are vector arrows.

Calculation headings can be clicked to collapse their steps. Explanations are in
an independently toggled panel. The palette is neutral gray with color reserved
for links to viewport arrows. HTML exports include all steps with static headings.

Arm rig > Attachment / constraint example adds an optional gray prop. Compare no
wrist link, hierarchy parenting, point constraint, orient constraint, and parent
constraint. The constrained cases preserve the current pose with maintain offset.
Move the IK target or rotate an FK joint to observe following. Its math display
shows the prop origin transformed by its world matrix. This is a transform-following
example, not skinning or a production attachment system. Reset removes its generated
nodes along with the rest of that lesson.


### Teaching display

- S/E/W are color-matched positions: tail of a, connection of a and b, head of b. E is not necessarily a midpoint. Viewport point labels show their live world coordinates.
- The gray guide is g = W - S; pink E - H is the projection residual, not the scalar dot product.
- The unit cross-product normal is drawn at 3x length for readability; numerical n remains unit length. Frame view includes that arrow.
- FK includes a wrist rotation control.
- The prop is selectable. Move/Rotate buttons expose channels left free by the link. To reposition a parent-constrained prop, choose World (unattached), move it, then relink with the new maintained offset.
- Constraint math shows selected native offsets and evaluated driven channels separately from the general local-to-world calculation. It is not a derivation of Maya's full constraint solver.
- Help / documentation and F1 explain notation, controls, interpolation, and links to official references.


### Visual relationships update

Projection labels H with its world coordinates, H-S as the purple projected displacement, and g=W-S as the full S-to-W guide. Orientation interpolation shows separated start/current/end objects; their spacing is for comparison and does not represent translational interpolation. Symbol definitions distinguish quaternion w from homogeneous w and the wrist point W. q_actual reports the center object orientation even after manual edits.

Props start at the hand grip and show local axes, a wrist-to-prop link and the selected attachment mode. Orient-only links deliberately allow the prop to leave the hand when its translation changes. Inline question buttons open focused help; the footer retains the full guide.


Student handoff: [Quick start](STUDENT_QUICKSTART.md). Instructor review: [Coverage and readiness audit](AUDIT_STUDENT_READINESS.md). The audit maps the saved 74-slide Revised Figures deck to implemented features and explicitly lists unimplemented demonstrations.


### Preview and baked animation

In Spaces & rotations, Play preview runs t from 0 to 1 over four seconds; Stop freezes the current pose. Switching lessons or closing the window stops preview. Bake Euler + SLERP comparison creates a separate keyed pair in the main Maya scene, starting at the current frame for 96 frames. Set the playback range to that interval and use Maya Play. The take is independent of lesson Reset and saves with the scene. SLERP samples are exact at keyed frames; linear Euler segments between keys approximate the continuous path. No existing animation or timeline range is overwritten.

[Illustrated math help and references](HELP.html) uses the same topic text as the new in-tool help. Cross formulas now show a component formula before each substituted calculation, with a/teal and b/gold operands. The pole guide indicates elbow-to-pole relationship, not a plane normal. The smaller prop starts below the palm.


## Label size and slide captures

**Label size** controls all in-scene point, vector, and reference-pose text (12–48 px;
default 24 px). Arial bold is used for legibility. The tool automatically loads its local
`viewport_labels_plugin.py`; keep this file beside the tool when sharing the folder.
Native annotation anchors and text values remain in the scene underneath the resizable display.

**Save viewport + math** renders at 3840×2160, scales label text for the export,
antialiases and thickens curves, then removes unused outer margins with padding.
The final PNG keeps original rendered pixels; it is not upscaled. A `_raw.png`
retains the uncropped viewport render. JSON records raw resolution, crop bounds,
processing, and final dimensions. The camera, label sizes, selection, background,
and antialiasing settings are restored after capture. Captures use a black background.

PNG captures remain raster images; native PowerPoint shapes remain resolution-independent.
Use the tightly cropped PNG at its intended slide size rather than enlarging a small screenshot.


The coordinate-space comparison keeps P independent of the reference frame after loading. Move the reference to change coordinates without moving P. The parent recipe initially places P using a rotated frame; the later box hierarchy is genuinely parented. The camera fixture is separate from the teaching viewport camera. Unit arrows are translated left for comparison only. Step 03 movement recipes compute speed, elapsed time, travel and the new position in the math panel.


## Animated teaching examples
Use **Save animated example** at the bottom of the tool. Choose a motion supported by the current lecture step and an output folder. The tool records a fixed-camera loop, crops all frames with the same content bounds, and saves an animated GIF, original PNG frames, capture.json values, and an HTML preview. The scene, camera, background, selection and display settings are restored, including on cancellation. Connected/keyed inputs are rejected. Loops ease motion and hold endpoints; they illustrate paths, not constant speed. View GIFs in a browser or PowerPoint Slide Show. Reload the tool after a source update.
