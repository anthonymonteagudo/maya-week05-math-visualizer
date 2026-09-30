"""Open the Week 5 teaching tool after interactive Maya finishes starting."""
import json
import os
import sys
import traceback
from pathlib import Path
from maya import cmds

status_path = Path(os.environ.get('TEMP', '.')) / 'week05_maya_launch_status.json'
try:
    tools_root = str(Path(__file__).resolve().parents[2])
    if tools_root not in sys.path:
        sys.path.insert(0, tools_root)
    from lesson_materials.week_05_applied_math import show
    from lesson_materials.week_05_applied_math.ui import WINDOW
    tool = show()
    cmds.window(WINDOW, edit=True, topLeftCorner=(60, 60))
    cmds.showWindow(WINDOW)
    status_path.write_text(json.dumps({'status': 'ready', 'pid': os.getpid(), 'maya': cmds.about(version=True), 'window_exists': cmds.window(WINDOW, exists=True), 'window_visible': cmds.window(WINDOW, query=True, visible=True), 'fixture': tool.demo.root if tool.demo else None}), encoding='utf-8')
except Exception:
    status_path.write_text(json.dumps({'status':'error','pid':os.getpid(),'traceback':traceback.format_exc()}),encoding='utf-8')
    raise
