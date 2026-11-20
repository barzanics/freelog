"""What exactly were you looking at? Turns (application, window title) into a precise, human line stored with every screenshot.

* **File Explorer** (Windows): the real folder path of the *active tab* - found by asking the Shell for its windows, matching the foreground window handle and, for
  Windows 11 tabs, the tab whose name equals the title. Special places (This PC, Quick access) are reported by name.
* **Finder** (macOS): the front window's folder through AppleScript. **Linux file managers**: the path when the title carries one (Dolphin), else the folder name.
* **Browsers**: the active tab's title.  **Editors**: file and workspace.  **Terminals**: the title (usually the working directory or command).

All parsing is pure and unit-tested; the single place that talks to the system (PowerShell / osascript) takes an injectable ``runner``. Switch off with the setting
``shots_record_context`` - paths can be sensitive and this text only ever lives in your own database.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import urllib.parse
from typing import Any, Callable, Dict, Optional

BROWSERS = ("chrome", "msedge", "firefox", "brave", "opera", "vivaldi", "safari", "arc", "chromium")
EDITORS = ("code", "cursor", "pycharm", "idea", "webstorm", "clion", "sublime_text", "notepad++", "atom", "zed", "devenv", "rider", "goland", "phpstorm")
TERMINALS = ("windowsterminal", "wt", "cmd", "powershell", "pwsh", "conhost", "terminal", "iterm2", "konsole", "gnome-terminal", "alacritty", "kitty", "xterm", "tilix")
FILE_MANAGERS = ("explorer", "finder", "nautilus", "dolphin", "thunar", "nemo", "pcmanfm", "caja")
MAX_LEN = 300
_SUFFIX = re.compile(r"\s+[-–—|]\s+(Google Chrome|Microsoft Edge|Mozilla Firefox|Brave|Opera|Vivaldi|Safari|Chromium|Arc|Visual Studio Code|Cursor|File Explorer|Windows Explorer|"
                     r"Dolphin|Files|Thunar|Nemo)$", re.IGNORECASE)


def _name(app: str) -> str:
    a = (app or "").lower().strip()
    return a[:-4] if a.endswith(".exe") else a


def kind_of(app: str) -> str:
    a = _name(app)
    for kind, names in (("file_manager", FILE_MANAGERS), ("browser", BROWSERS), ("editor", EDITORS), ("terminal", TERMINALS)):
        if any(a == n or a.startswith(n) for n in names):
            return kind
    return "other"


def _clean(s: str) -> str:
    return re.sub(r"[\x00-\x1f\x7f]", " ", s or "").strip()[:MAX_LEN]


def path_from_location_url(url: str) -> str:
    """``file:///C:/Users/Ann/My%20Docs`` -> ``C:\\Users\\Ann\\My Docs``; ``file://server/share/x`` -> ``\\\\server\\share\\x``; anything else -> ''."""
    if not url or not url.lower().startswith("file:"):
        return ""
    u = urllib.parse.urlparse(url)
    p = urllib.parse.unquote(u.path)
    if u.netloc and u.netloc.lower() != "localhost":
        return "\\\\" + u.netloc + p.replace("/", "\\")
    if re.match(r"^/[A-Za-z]:", p):
        p = p[1:]
    return p.replace("/", "\\") if re.match(r"^[A-Za-z]:", p) else p


def explorer_script(hwnd: int, expected_name: str) -> str:
    """PowerShell that prints the folder of the Explorer window with handle ``hwnd`` (for tabbed Explorer: the tab named ``expected_name``) as one JSON line."""
    q = expected_name.replace("'", "''")
    return ("$sh = New-Object -ComObject Shell.Application; $best = $null; "
            f"foreach ($w in $sh.Windows()) {{ try {{ if ([int64]$w.HWND -eq {int(hwnd)}) {{ if ($best -eq $null) {{ $best = $w }}; if ($w.LocationName -eq '{q}') {{ $best = $w; break }} }} }} catch {{}} }}; "
            "if ($best -ne $null) { @{name=$best.LocationName; url=$best.LocationURL} | ConvertTo-Json -Compress }")


def _foreground_hwnd() -> int:
    try:
        import ctypes
        return int(ctypes.windll.user32.GetForegroundWindow())
    except Exception:  # noqa: BLE001
        return 0


def explorer_folder(title: str, runner: Callable[..., Any] = subprocess.run, hwnd: Optional[int] = None) -> Optional[Dict[str, str]]:
    """{'name', 'path'} of the folder shown in the active Explorer tab, or None."""
    expected = re.sub(_SUFFIX, "", title or "").strip()
    h = _foreground_hwnd() if hwnd is None else hwnd
    if not h:
        return None
    try:
        r = runner(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", explorer_script(h, expected)], capture_output=True, text=True, timeout=4)
        out = (r.stdout or "").strip()
        if not out:
            return None
        j = json.loads(out.splitlines()[-1])
        return {"name": _clean(j.get("name", "")), "path": _clean(path_from_location_url(j.get("url", "")))}
    except Exception:  # noqa: BLE001 - context is best effort
        return None


def finder_folder(runner: Callable[..., Any] = subprocess.run) -> Optional[str]:
    try:
        r = runner(["osascript", "-e", 'tell application "Finder" to POSIX path of (target of front window as alias)'], capture_output=True, text=True, timeout=4)
        return _clean(r.stdout) or None
    except Exception:  # noqa: BLE001
        return None


def parse_editor_title(title: str) -> str:
    """VS Code 'file.py - project - Visual Studio Code', JetBrains 'project – path/file.py', Sublime 'file (project) - Sublime Text'."""
    t = re.sub(_SUFFIX, "", _clean(title))
    parts = [p.strip() for p in re.split(r"\s+[-–—]\s+", t) if p.strip()]
    if len(parts) >= 2:
        return f"{parts[0]} · {parts[1]}"
    return t


def describe(app: str, title: str, platform: str = sys.platform, runner: Callable[..., Any] = subprocess.run, hwnd: Optional[int] = None) -> Dict[str, str]:
    """{'kind', 'path', 'detail', 'text'}: ``text`` is the one-line description saved with the screenshot (empty when there is nothing useful to add)."""
    kind, a, t = kind_of(app), _name(app), _clean(title)
    out = {"kind": kind, "path": "", "detail": "", "text": ""}
    if kind == "file_manager":
        label = {"explorer": "File Explorer", "finder": "Finder", "nautilus": "Files", "dolphin": "Dolphin", "thunar": "Thunar", "nemo": "Nemo"}.get(a, "File manager")
        folder = None
        if a == "explorer" and platform == "win32":
            folder = explorer_folder(t, runner, hwnd)
        elif a == "finder" and platform == "darwin":
            p = finder_folder(runner)
            folder = {"name": "", "path": p or ""}
        if folder and folder.get("path"):
            out["path"] = folder["path"]
        else:
            m = re.match(r"^(~?/[^—–|]+?)\s+[-–—|]\s+", t + " - ")                          # Dolphin & others put the full path in the title
            out["path"] = m.group(1).strip() if m else ""
            out["detail"] = (folder or {}).get("name") or re.sub(_SUFFIX, "", t)
        out["text"] = f"{label} · {out['path'] or out['detail']}".strip(" ·")
    elif kind == "browser":
        tab = re.sub(_SUFFIX, "", t)
        out["detail"], out["text"] = tab, (f"{a.capitalize() if a != 'msedge' else 'Edge'} · Tab: {tab}" if tab else "")
    elif kind == "editor":
        d = parse_editor_title(t)
        out["detail"], out["text"] = d, (f"{ {'code': 'VS Code', 'pycharm': 'PyCharm'}.get(a, a.capitalize()) } · {d}" if d else "")
    elif kind == "terminal":
        out["detail"], out["text"] = t, (f"Terminal · {t}" if t else "")
    return {k: _clean(v) for k, v in out.items()}
