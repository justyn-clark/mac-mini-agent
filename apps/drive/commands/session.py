"""Session management: create, list, kill, and inspect."""
import click

from modules import tmux
from modules.approval import validate_approval
from modules.errors import DriveError
from modules.output import emit, emit_error


@click.group()
def session():
    """Manage tmux sessions."""
    pass


@session.command()
@click.argument("name")
@click.option("--window", default=None, help="Name for the initial window.")
@click.option("--dir", "start_dir", default=None, help="Working directory.")
@click.option("--detach", is_flag=True, help="Create headless (no Terminal window).")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def create(name: str, window: str | None, start_dir: str | None, detach: bool, as_json: bool):
    """Create a new tmux session.

    Opens a new Terminal window attached to the session by default.
    Use --detach for headless sessions.
    """
    try:
        tmux.create_session(
            name, window_name=window, start_directory=start_dir, detach=detach
        )
        emit(
            {"ok": True, "action": "create", "session": name, "detach": detach},
            json=as_json,
            human_lines=f"Created session: {name}" + (" (detached)" if detach else " (Terminal window opened)"),
        )
    except DriveError as e:
        emit_error(e, json=as_json)


@session.command("list")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def list_cmd(as_json: bool):
    """List all tmux sessions."""
    try:
        sessions = tmux.list_sessions()
        if as_json:
            emit(
                {"ok": True, "sessions": [s.to_dict() for s in sessions]},
                json=True,
                human_lines="",
            )
        else:
            if not sessions:
                click.echo("No tmux sessions.")
            else:
                for s in sessions:
                    attached = " (attached)" if s.attached else ""
                    click.echo(
                        f"  {s.name:<20} {s.windows} window(s)  {s.created}{attached}"
                    )
    except DriveError as e:
        emit_error(e, json=as_json)


@session.command()
@click.argument("name")
@click.option("--approval", default=None, help="Optional approval contract id for session.kill/session:<name>.")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def kill(name: str, approval: str | None, as_json: bool):
    """Kill a tmux session."""
    try:
        if approval:
            validate_approval(approval, action="session.kill", target=f"session:{name}", consume=True)
        tmux.kill_session(name)
        emit(
            {"ok": True, "action": "kill", "session": name, "approval": approval},
            json=as_json,
            human_lines=f"Killed session: {name}",
        )
    except DriveError as e:
        emit_error(e, json=as_json)


@session.command("inspect")
@click.argument("name")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def inspect_cmd(name: str, as_json: bool):
    """Inspect one tmux session: windows, panes, PIDs, and cwd."""
    try:
        snapshot = tmux.inspect_session(name)
        if as_json:
            emit({"ok": True, **snapshot.to_dict()}, json=True, human_lines="")
            return

        lines = [
            f"Session: {snapshot.session.name}",
            f"  windows: {snapshot.session.windows}",
            f"  created: {snapshot.session.created}",
            f"  attached: {'yes' if snapshot.session.attached else 'no'}",
        ]
        for window in snapshot.windows:
            marker = "*" if window.active else "-"
            lines.append(f"{marker} window {window.window_index}: {window.name} [{window.layout}]")
            for pane in window.panes:
                active = "*" if pane.active else "-"
                lines.append(
                    f"    {active} pane {pane.pane_index} pid={pane.pane_pid} cmd={pane.current_command} cwd={pane.current_path}"
                )
        emit({"ok": True, **snapshot.to_dict()}, json=False, human_lines=lines)
    except DriveError as e:
        emit_error(e, json=as_json)
