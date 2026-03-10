"""Subprocess wrappers for tmux CLI.

All tmux interaction flows through this module.
Command files import from here; they never call subprocess directly.
"""
import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass, field

from modules.errors import (
    SessionExistsError,
    SessionNotFoundError,
    TmuxCommandError,
    TmuxNotFoundError,
)


def require_tmux() -> str:
    """Return path to tmux binary or raise TmuxNotFoundError."""
    path = shutil.which("tmux")
    if path is None:
        raise TmuxNotFoundError()
    return path


def _run(
    args: list[str], *, check: bool = True, capture: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run a tmux command. All subprocess calls are centralized here."""
    tmux = require_tmux()
    cmd = [tmux] + args
    try:
        result = subprocess.run(
            cmd, capture_output=capture, text=True, timeout=10
        )
        if check and result.returncode != 0:
            raise TmuxCommandError(cmd=args, stderr=result.stderr.strip())
        return result
    except subprocess.TimeoutExpired:
        raise TmuxCommandError(cmd=args, stderr="tmux command timed out after 10s")
    except FileNotFoundError:
        raise TmuxNotFoundError()


# --- Session operations ---


def session_exists(name: str) -> bool:
    """Check if a tmux session exists."""
    result = _run(["has-session", "-t", name], check=False)
    return result.returncode == 0


def require_session(name: str) -> None:
    """Raise SessionNotFoundError if session does not exist."""
    if not session_exists(name):
        raise SessionNotFoundError(name)


@dataclass
class SessionInfo:
    name: str
    windows: int
    created: str
    attached: bool

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "windows": self.windows,
            "created": self.created,
            "attached": self.attached,
        }


@dataclass
class PaneInfo:
    pane_id: str
    pane_index: int
    pane_pid: int
    title: str
    current_command: str
    current_path: str
    active: bool

    def to_dict(self) -> dict:
        return {
            "pane_id": self.pane_id,
            "pane_index": self.pane_index,
            "pane_pid": self.pane_pid,
            "title": self.title,
            "current_command": self.current_command,
            "current_path": self.current_path,
            "active": self.active,
        }


@dataclass
class WindowInfo:
    window_id: str
    window_index: int
    name: str
    layout: str
    active: bool
    panes: list[PaneInfo] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "window_id": self.window_id,
            "window_index": self.window_index,
            "name": self.name,
            "layout": self.layout,
            "active": self.active,
            "panes": [p.to_dict() for p in self.panes],
        }


@dataclass
class SessionSnapshot:
    session: SessionInfo
    windows: list[WindowInfo]

    def to_dict(self) -> dict:
        return {
            "session": self.session.to_dict(),
            "windows": [w.to_dict() for w in self.windows],
        }


def open_terminal_window(command: str) -> None:
    """Open a new Terminal.app window and run a command in it.

    Uses AppleScript on macOS to tell Terminal.app to execute a script.
    The new window inherits the current working directory.
    """
    if platform.system() != "Darwin":
        return  # silently skip on non-macOS
    cwd = os.getcwd()
    shell_command = f"cd '{cwd}' && {command}"
    escaped = shell_command.replace("\\", "\\\\").replace('"', '\\"')
    subprocess.run(
        [
            "osascript",
            "-e",
            f'tell application "Terminal" to do script "{escaped}"',
        ],
        capture_output=True,
        text=True,
    )


def create_session(
    name: str,
    *,
    window_name: str | None = None,
    start_directory: str | None = None,
    detach: bool = False,
) -> None:
    """Create a tmux session.

    By default opens a new Terminal.app window attached to the session
    so the user can watch live. Use detach=True for headless sessions.
    """
    if session_exists(name):
        raise SessionExistsError(name)

    if detach:
        args = ["new-session", "-d", "-s", name]
        if window_name:
            args.extend(["-n", window_name])
        if start_directory:
            args.extend(["-c", start_directory])
        _run(args)
    else:
        # Open a new Terminal window with tmux session attached.
        # -A: attach if exists, create if not.
        tmux_cmd = f"tmux new-session -A -s {name}"
        if window_name:
            tmux_cmd += f" -n {window_name}"
        if start_directory:
            tmux_cmd += f" -c '{start_directory}'"
        open_terminal_window(tmux_cmd)
        # Wait for the session to appear (Terminal + tmux startup time)
        _wait_for_session(name, timeout=5.0)


def _wait_for_session(name: str, timeout: float = 5.0) -> None:
    """Poll until a tmux session exists or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if session_exists(name):
            return
        time.sleep(0.2)
    raise TmuxCommandError(
        cmd=["new-session", "-s", name],
        stderr=f"Session '{name}' did not appear within {timeout}s",
    )


def list_sessions() -> list[SessionInfo]:
    """List all tmux sessions. Empty list if no server running."""
    result = _run(
        [
            "list-sessions",
            "-F",
            "#{session_name}\t#{session_windows}\t#{session_created_string}\t#{session_attached}",
        ],
        check=False,
    )
    if result.returncode != 0:
        return []
    sessions = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 4:
            sessions.append(
                SessionInfo(
                    name=parts[0],
                    windows=int(parts[1]),
                    created=parts[2],
                    attached=parts[3] != "0",
                )
            )
    return sessions


def kill_session(name: str) -> None:
    """Kill a tmux session."""
    require_session(name)
    _run(["kill-session", "-t", name])


def get_session_info(name: str) -> SessionInfo:
    """Get one tmux session record."""
    require_session(name)
    result = _run(
        [
            "list-sessions",
            "-F",
            "#{session_name}\t#{session_windows}\t#{session_created_string}\t#{session_attached}",
        ]
    )
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 4 and parts[0] == name:
            return SessionInfo(
                name=parts[0],
                windows=int(parts[1]),
                created=parts[2],
                attached=parts[3] != "0",
            )
    raise SessionNotFoundError(name)


def list_windows(session: str) -> list[WindowInfo]:
    """List windows for a tmux session."""
    require_session(session)
    result = _run(
        [
            "list-windows",
            "-t",
            session,
            "-F",
            "#{window_id}\t#{window_index}\t#{window_name}\t#{window_layout}\t#{window_active}",
        ]
    )
    windows: list[WindowInfo] = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 5:
            windows.append(
                WindowInfo(
                    window_id=parts[0],
                    window_index=int(parts[1]),
                    name=parts[2],
                    layout=parts[3],
                    active=parts[4] != "0",
                )
            )
    return windows


def list_panes(session: str, window: str | None = None) -> list[PaneInfo]:
    """List panes for a session or one specific window."""
    require_session(session)
    target = f"{session}:{window}" if window is not None else session
    result = _run(
        [
            "list-panes",
            "-t",
            target,
            "-F",
            "#{pane_id}\t#{pane_index}\t#{pane_pid}\t#{pane_title}\t#{pane_current_command}\t#{pane_current_path}\t#{pane_active}\t#{window_index}",
        ]
    )
    panes: list[PaneInfo] = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 8:
            panes.append(
                PaneInfo(
                    pane_id=parts[0],
                    pane_index=int(parts[1]),
                    pane_pid=int(parts[2]),
                    title=parts[3],
                    current_command=parts[4],
                    current_path=parts[5],
                    active=parts[6] != "0",
                )
            )
    return panes


def inspect_session(session: str) -> SessionSnapshot:
    """Return a full tmux discovery snapshot: session, windows, and panes."""
    info = get_session_info(session)
    windows = list_windows(session)
    panes = _run(
        [
            "list-panes",
            "-t",
            session,
            "-F",
            "#{pane_id}\t#{pane_index}\t#{pane_pid}\t#{pane_title}\t#{pane_current_command}\t#{pane_current_path}\t#{pane_active}\t#{window_index}",
        ]
    )
    panes_by_window: dict[int, list[PaneInfo]] = {}
    for line in panes.stdout.strip().splitlines():
        parts = line.split("\t")
        if len(parts) >= 8:
            window_index = int(parts[7])
            pane = PaneInfo(
                pane_id=parts[0],
                pane_index=int(parts[1]),
                pane_pid=int(parts[2]),
                title=parts[3],
                current_command=parts[4],
                current_path=parts[5],
                active=parts[6] != "0",
            )
            panes_by_window.setdefault(window_index, []).append(pane)
    for window_info in windows:
        window_info.panes = sorted(panes_by_window.get(window_info.window_index, []), key=lambda p: p.pane_index)
    return SessionSnapshot(session=info, windows=windows)


# --- Pane operations ---


def resolve_target(session: str, pane: str | None = None) -> str:
    """Build a tmux target string."""
    if pane is not None:
        return f"{session}:.{pane}"
    return f"{session}:"


def send_keys(
    session: str,
    keys: str,
    *,
    pane: str | None = None,
    enter: bool = True,
    literal: bool = False,
) -> None:
    """Send keystrokes to a tmux pane."""
    require_session(session)
    target = resolve_target(session, pane)
    args = ["send-keys", "-t", target]
    if literal:
        args.append("-l")
    args.append(keys)
    _run(args)
    # When literal mode is on, "Enter" would be sent as text.
    # Send Enter as a separate non-literal key press.
    if enter:
        _run(["send-keys", "-t", target, "Enter"])


def capture_pane(
    session: str,
    *,
    pane: str | None = None,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    """Capture pane content (and optionally scrollback)."""
    require_session(session)
    target = resolve_target(session, pane)
    args = ["capture-pane", "-p", "-t", target]
    if start_line is not None:
        args.extend(["-S", str(start_line)])
    if end_line is not None:
        args.extend(["-E", str(end_line)])
    result = _run(args)
    return result.stdout.rstrip("\n")
