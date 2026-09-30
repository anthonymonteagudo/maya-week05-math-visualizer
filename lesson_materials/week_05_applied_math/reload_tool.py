"""Refresh the open teaching tool after a source update, preserving its scene."""
import importlib
import sys
from pathlib import Path

# Also works as a standalone file when this Maya session has no course path yet.
tools_root = str(Path(__file__).resolve().parents[2])
if tools_root not in sys.path:
    sys.path.insert(0, tools_root)
from lesson_materials.week_05_applied_math import calculations, presentation, help_content, scene, spaces, lecture, capture, viewport_labels, gif_export, motion_capture, ui


def main():
    if ui._instance:
        ui._instance.close()
    for module in (calculations, presentation, help_content, scene, spaces, lecture, capture, viewport_labels, gif_export, motion_capture, ui):
        importlib.reload(module)
    return ui.show()


if __name__ == '__main__':
    main()
