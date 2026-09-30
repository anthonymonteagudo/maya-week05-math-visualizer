# Tool and Week 5 deck audit — 28 September 2026

Reviewed the current Python tool and the saved 74-slide `Week 5 - Applied Math I - Revised Figures.pptx` in Course/Slides/Week05/Deck. Unsaved PowerPoint edits are outside this audit. The deck itself was not modified.

## Fixed in this pass

- Preset descriptions previously continued asserting dot=0 after a point was moved. The UI now identifies edited configurations and offers Reload selected example.
- Resetting vectors/arm previously reset the rotation slider while preserving the rotation object. Resets now affect only the relevant lesson's controls.
- The matrix lesson now displays a homogeneous direction with w=0 alongside the point with w=1, using the same components and world matrix (slides 27, 28, 47).
- Inline overlay help now chooses the displayed topic rather than always showing projection help.
- Captures clear and restore selection; JSON now records actual rotation matrices and visible attachment state.
- Added STUDENT_QUICKSTART.md with known answers, scope and recovery instructions.

## Coverage and missing pieces

| Slides | Current coverage | Recommended treatment |
|---|---|---|
| 7–23 vectors | Components, addition/subtraction, lengths, normalize, degeneracies are live. Deck A=(1,2,0), B=(4,6,0) differs from tool S=(0,0,0), E=(3,4,0), but displacement matches. | State the point-name and origin change before switching to the tool. Velocity/delta-time and scalar multiplication are explained in slides, not separate live controls. |
| 24–29 spaces | World inputs, parent rotation, local-to-world point/direction math. | Highest-value next addition: side-by-side local/world values with an inverse round trip. Camera and tangent spaces remain conceptual previews, not implemented Maya lessons. |
| 33–43 dot/cross | Raw dot, normalized angle, projection, cross magnitude and unit normal. Babylon supplies material tie-ins. | Explain that head-to-tail drawing does not change a free vector's direction; compare angle between a and b, not the interior elbow angle. Add a shared-tail angle arc only if it improves the lesson without clutter. |
| 45–55 matrices | Native hierarchy and forward mapping. | Inverse mapping, explicit scale/pivot controls and an order-comparison experiment are absent. Use prepared slide figures; do not promise those controls exist. |
| 57–63 rotations | Fixed XYZ endpoints, Euler-component LERP and quaternion SLERP, endpoint references, actual orientation. | No rotation-order selector, gimbal-lock experiment, axis-angle controls, or position LERP. Slide 61's older translating-object captures do not describe the current orientation-only slider. Highest-value next addition after spaces: position LERP, then a separate rotation-order/gimbal demo. |
| 64–67 lab | Deliberately unfinished lab_extension.py and instructor run_lab entry point. | Not yet a fully student-facing lab launcher. Distribute a guided worksheet or add a clearly labeled lab panel before asking novices to run it unaided. |

## Notation correction for the deck

Slide 66 names the residual `b=E-H`, while slides 35/41 and the tool use `b=W-E` for the forearm vector. Rename the residual to `r=E-H` or keep it explicitly as `E-H`. H is a point; H-S is a vector; a dot b is a scalar. g=W-S is the guide displacement, not its length. Quaternion w, homogeneous-coordinate w, and point W are unrelated symbols.

## Student readiness judgment

Ready for a guided instructor demo of vectors, arm relationships and orientation interpolation. Not yet a complete standalone replacement for every promised slide demonstration. Avoid adding all remaining topics into one dense panel. Prioritize (1) explicit local/world + inverse comparison, (2) position LERP, (3) lab launch/error/known-answer workflow, then (4) rotation order/gimbal lock as its own lesson.

Remaining technical limitations: camera-dependent label offsets can overlap after arbitrary edits; existing saved fixtures are not automatically migrated to changed scene builders (use a fresh launch/reset); only Maya 2027/cm is certified; constraint readouts report native solver outputs rather than deriving every solver step. Keep these distinctions in instructor notes.
