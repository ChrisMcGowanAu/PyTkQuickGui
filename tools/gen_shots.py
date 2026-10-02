"""Generate the ttk and Flet programs for one project, ready to screenshot.

Usage: gen_shots.py <project.json> <outdir>

Files are written as tk.py and flet_run.py, with the window title set to a
unique probe name so screenshots.sh can find the right window.  flet_run.py is
deliberately *not* called flet.py: a script of that name shadows the flet
package when it runs.
"""

import contextlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import pytkquickgui as app  # noqa: E402  # pylint: disable=wrong-import-position

project_path = os.path.abspath(sys.argv[1])
outdir = os.path.abspath(sys.argv[2])
name = os.path.basename(os.path.dirname(project_path))
os.makedirs(outdir, exist_ok=True)

work = os.path.join(outdir, "_work")
os.makedirs(work, exist_ok=True)

app.rootWin.withdraw()
app.myVars.initVars()
app.getConfigPath = lambda: work
app.buildMainGui()
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
    io.StringIO()
):
    app.loadProject(name, project_path)
# Keep the tool's saves inside the scratch directory, not next to the project.
app.myVars.projectPath = work
app.myVars.projectFileName = os.path.join(work, name)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
    io.StringIO()
):
    py_path = app.buildPython()
    flet_path = app.buildFlet()

with open(py_path, encoding="utf-8") as handle:
    tk_source = handle.read()
with open(flet_path, encoding="utf-8") as handle:
    flet_source = handle.read()

tk_source = tk_source.replace(f"title = '{name}'", f"title = 'probe-{name}-tk'", 1)
flet_source = flet_source.replace(
    f"PROJECT_NAME = '{name}'", f"PROJECT_NAME = 'probe-{name}-flet'", 1
)

with open(os.path.join(outdir, "tk.py"), "w", encoding="utf-8") as handle:
    handle.write(tk_source)
with open(os.path.join(outdir, "flet_run.py"), "w", encoding="utf-8") as handle:
    handle.write(flet_source)
print(f"{name}: tk.py {len(tk_source)}B, flet_run.py {len(flet_source)}B")
