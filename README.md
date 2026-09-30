# Week 5 — Maya Math Visualizer

Interactive applied-math examples for technical-art students and peers. Move controls
in Maya and connect the visible result to live, worked calculations.

- Vectors: displacement, length, normalization, addition, dot product, projection, and cross product.
- Coordinate spaces and matrix transforms.
- Euler-angle interpolation and quaternion SLERP.
- Optional arm, IK, and attachment examples.
- Viewport PNGs, worked-math worksheets, and animated GIF capture.

## Download and launch

1. [Download the ZIP](https://github.com/anthonymonteagudo/maya-week05-math-visualizer/archive/refs/heads/main.zip) and extract it completely, or clone this repository.
2. On Windows with Maya 2027 installed in its default location, double-click **Launch Week 5.cmd** in the extracted repository.
3. The launcher opens a separate Maya session. Use a centimeter scene. Start at **01 · One displacement**, move S or E, and compare the viewport with the math panel.

Maya 2027 is the tested version. Older versions have not been certified. Maya is
required and is not included. The Python-only math tests can run without Maya.

For a different Maya installation location or operating system, open Maya's
**Script Editor → Python** tab, replace the path below with the extracted repository
folder (the one containing `lesson_materials`), and run:

```python
import sys

tools_root = r"C:\path\to\maya-week05-math-visualizer"
if tools_root not in sys.path:
    sys.path.insert(0, tools_root)

from lesson_materials.week_05_applied_math import show
show()
```

Keep the folder structure intact, including `viewport_labels_plugin.py`.
No pip installation is needed for the tool inside Maya 2027.

## Using the tool

Choose a **Lecture step**, try its **Variation** examples, and move the controls to
explore. **Restore variation** restores the example. **Explore freely** exposes the
lesson and overlay menus. The **?** buttons explain notation and math.

- [Student quick start](lesson_materials/week_05_applied_math/STUDENT_QUICKSTART.md)
- [Full tool guide and capture instructions](lesson_materials/week_05_applied_math/README.md)
- [Teaching code excerpts](lesson_materials/week_05_applied_math/TEACHING_CODE.md)
- [Design references](lesson_materials/week_05_applied_math/JETTELLY_DESIGN_NOTES.md)

Slide numbers refer to the instructor's Week 5 lecture deck; the deck is not
included or required to explore the tool. `lab_extension.py` is an intentionally
unfinished optional exercise; the built-in reference visualizations already work.
The dated readiness audit is historical instructor context.

## Tests

Run from the repository root using Python:

```text
python -m unittest tests.test_week05_math tests.test_week05_calculations
```

Run each Maya test suite in its own mayapy process (Windows default installation):

```bat
"C:\Program Files\Autodesk\Maya2027\bin\mayapy.exe" -m unittest tests.maya_standalone.test_week05
"C:\Program Files\Autodesk\Maya2027\bin\mayapy.exe" -m unittest tests.maya_standalone.test_week05_lecture
```

## Feedback

For bugs, include your Maya version, operating system, lecture step/variation,
reproduction steps, and the Script Editor error, if any.
