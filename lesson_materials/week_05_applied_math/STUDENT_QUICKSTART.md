# Week 5: follow along with the lecture

1. Launch **Launch Week 5.cmd**. It opens a separate Maya session; keep your current work open.
2. Start at **01 · One displacement** (slides 23–29). Only S, E, and a = E − S appear. Move S or E and predict the result.
3. Use **Variation** to add length and unit direction. **Next** moves to two connected movements on slide 27.
4. Follow **Lecture step** in order, or select the step shown by your instructor. Its slide reference and short prompt tell you what to check.
5. Changing step or variation loads its starting values. **Restore variation** restores those values after an experiment; **Frame view** only changes the view.
6. Dot, projection, and cross have separate stops. Try each known case before its edge cases.
7. Transform steps show the yellow local corner. Position interpolation moves the object origin from X=0 to X=4; orientation interpolation compares Euler LERP and quaternion SLERP.
8. Use **Explore freely** for the original lesson, overlay, and example selectors. Uncheck it to return to the selected lecture variation.
9. The final arm step is an optional Week 6 preview. Keep rig construction and constraint workflows for their deeper treatment next week.
10. Increase **Label size** if needed. **Save viewport + math** exports a tightly cropped high-resolution PNG, its uncropped raw render, values, and worked calculation.

Use **?** for topic help. Validated in Maya 2027 with centimeter scenes.
Coordinate spaces has prepared world, local, parent, camera and tangent variations. Use Move space point P and Move/Rotate reference frame. Material applications, gimbal lock and some pencil-and-paper examples remain slide demonstrations.

## Guided code extension (instructor-led)

Open lab_extension.py and implement elbow_projection. It is deliberately unfinished. The complete built-in diagnostic provides a comparison, not your submitted implementation. After editing, run this in Maya's Python Script Editor with the tool open:

```python
from lesson_materials.week_05_applied_math import ui
ui._instance.run_lab()
```

This is an instructor development entry point; the main UI does not currently expose a full student lab workflow. Ask your instructor which extension and demonstration are required. Week 5 has no new assignment; continue the midterm.

The current Student Edition (September 30) has 107 slides. Step 04 spans slides 39–53, including the worked matrix foundation; step 08 applies transforms to the box on slides 78–88.
