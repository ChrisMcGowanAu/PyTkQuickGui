#!/usr/bin/env bash
# Regenerate the example screenshots in docs/.
#
#   tools/screenshots.sh                # every project in examples/
#   tools/screenshots.sh tabs sudoku3   # just these
#
# For each project it generates the ttk and Flet programs, runs each one,
# screenshots the real window and writes docs/example_<name>_tk.png and
# _flet.png.  It needs a desktop session and these X11 tools: xwininfo, xprop,
# wmctrl, ImageMagick's import.  Nothing here is needed to use the tool, only to
# refresh the stills.
set -u

ROOT=$(cd "$(dirname "$0")/.." && pwd)
VENV_PY="$ROOT/venv/bin/python"
WORK=$(mktemp -d)
PYTHON=${PYTHON:-$VENV_PY}

if [ ! -x "$PYTHON" ]; then
    echo "no interpreter at $PYTHON - run from a checkout with a venv, or set PYTHON" >&2
    exit 1
fi
for tool in xwininfo xprop wmctrl import; do
    command -v "$tool" >/dev/null || { echo "missing $tool" >&2; exit 1; }
done

if [ "$#" -gt 0 ]; then
    names="$*"
else
    names=$(cd "$ROOT/examples" && ls -d */ | tr -d /)
fi

# capture <title> <out.png> <command...>
# Flet draws through a GL surface that "import -window <id>" captures as blank,
# so the root window is captured and cropped to the client area from xwininfo.
# The Flet desktop client is a separate process that outlives the Python
# process, so the whole process group is killed, then the window's own
# _NET_WM_PID - otherwise stale windows pile up and later shots measure the
# wrong one.
capture() {
    local title="$1" out="$2"
    shift 2
    local before candidate wid="" pid info gx gy gw gh owner
    before=$(xwininfo -root -tree | awk '/^ *0x[0-9a-f]+ /{print $1}')

    setsid "$@" >"$WORK/capture.log" 2>&1 &
    pid=$!
    for _ in $(seq 1 120); do
        for candidate in $(xwininfo -root -tree | awk -v t="$title" \
                '/^ *0x[0-9a-f]+ / && index($0, "\"" t "\"") {print $1}'); do
            case " $before " in *" $candidate "*) ;; *) wid=$candidate ;; esac
        done
        [ -n "$wid" ] && break
        sleep 0.5
    done

    stop() {
        kill -9 -"$pid" 2>/dev/null
        if [ -n "${wid:-}" ]; then
            owner=$(xprop -id "$wid" _NET_WM_PID 2>/dev/null | awk '{print $NF}')
            [ -n "$owner" ] && kill -9 "$owner" 2>/dev/null
        fi
    }
    if [ -z "$wid" ]; then
        echo "  FAIL $title: no window after 60s"
        tail -3 "$WORK/capture.log" | sed 's/^/    /'
        stop
        return 1
    fi

    wmctrl -i -r "$wid" -b add,above 2>/dev/null   # raise above whatever is on top
    wmctrl -i -a "$wid" 2>/dev/null
    sleep 3
    info=$(xwininfo -id "$wid")
    gx=$(awk '/Absolute upper-left X/ {print $NF}' <<<"$info")
    gy=$(awk '/Absolute upper-left Y/ {print $NF}' <<<"$info")
    gw=$(awk '/^  Width/  {print $NF}' <<<"$info")
    gh=$(awk '/^  Height/ {print $NF}' <<<"$info")
    import -window root "$WORK/root.png" 2>/dev/null
    local status=$?
    stop
    sleep 1
    for _ in $(seq 1 10); do
        xwininfo -id "$wid" >/dev/null 2>&1 || break
        kill -9 "$wid" 2>/dev/null
        sleep 0.5
    done
    [ $status -ne 0 ] && { echo "  FAIL $title: capture failed"; return 1; }

    python3 - "$WORK/root.png" "$out" "$gx" "$gy" "$gw" "$gh" <<'PY'
import sys
from PIL import Image
root, out, x, y, w, h = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
Image.open(root).convert("RGB").crop((x, y, x + w, y + h)).save(out)
print(f"  {out} {w}x{h}")
PY
}

status=0
for name in $names; do
    project="$ROOT/examples/$name/$name.json"
    if [ ! -f "$project" ]; then
        echo "$name: no $project"
        status=1
        continue
    fi
    out="$WORK/$name"
    mkdir -p "$out"
    "$PYTHON" "$ROOT/tools/gen_shots.py" "$project" "$out" || { status=1; continue; }
    capture "probe-$name-tk" "$ROOT/docs/example_${name}_tk.png" \
        "$PYTHON" "$out/tk.py" || status=1
    capture "probe-$name-flet" "$ROOT/docs/example_${name}_flet.png" \
        "$PYTHON" "$out/flet_run.py" || status=1
done
rm -rf "$WORK"
echo "done"
exit $status
