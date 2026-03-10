"""Approval contract management for dangerous drive actions."""
import click

from modules.approval import issue_approval, list_approvals, load_approval, revoke_approval
from modules.errors import DriveError
from modules.output import emit, emit_error


@click.group()
def approval():
    """Issue, inspect, list, and revoke approval contracts."""
    pass


@approval.command("issue")
@click.option("--action", required=True, help="Action scope, e.g. proc.kill or session.kill")
@click.option("--target", required=True, help="Target scope, e.g. pid:1234 or session:worker")
@click.option("--ttl", type=int, default=None, help="Expiry in seconds from now.")
@click.option("--uses", type=int, default=1, help="Max uses. Set 1 for single-use.")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def issue_cmd(action: str, target: str, ttl: int | None, uses: int, as_json: bool):
    """Create a new approval contract."""
    try:
        contract = issue_approval(action=action, target=target, ttl_seconds=ttl, max_uses=uses)
        emit(
            contract.to_dict(),
            json=as_json,
            human_lines=[
                f"Issued approval: {contract.approval_id}",
                f"  action: {contract.action}",
                f"  target: {contract.target}",
                f"  expires_at: {contract.expires_at if contract.expires_at is not None else 'never'}",
                f"  max_uses: {contract.max_uses if contract.max_uses is not None else 'unbounded'}",
            ],
        )
    except DriveError as e:
        emit_error(e, json=as_json)


@approval.command("show")
@click.argument("approval_id")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def show_cmd(approval_id: str, as_json: bool):
    """Show a specific approval contract."""
    try:
        contract = load_approval(approval_id)
        emit(contract.to_dict(), json=as_json, human_lines=[
            f"Approval: {contract.approval_id}",
            f"  action: {contract.action}",
            f"  target: {contract.target}",
            f"  uses: {contract.uses}",
            f"  uses_remaining: {contract.uses_remaining if contract.uses_remaining is not None else 'unbounded'}",
            f"  expires_at: {contract.expires_at if contract.expires_at is not None else 'never'}",
            f"  revoked_at: {contract.revoked_at if contract.revoked_at is not None else 'active'}",
        ])
    except DriveError as e:
        emit_error(e, json=as_json)


@approval.command("list")
@click.option("--active-only", is_flag=True, help="Hide revoked approvals.")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def list_cmd(active_only: bool, as_json: bool):
    """List approval contracts."""
    try:
        approvals = list_approvals(include_revoked=not active_only)
        human_lines = "No approvals." if not approvals else [
            f"  {a.approval_id}  {a.action}  {a.target}  uses={a.uses}/{a.max_uses if a.max_uses is not None else 'inf'}  revoked={'yes' if a.revoked_at else 'no'}"
            for a in approvals
        ]
        emit(
            {"ok": True, "approvals": [a.to_dict()["approval"] for a in approvals]},
            json=as_json,
            human_lines=human_lines,
        )
    except DriveError as e:
        emit_error(e, json=as_json)


@approval.command("revoke")
@click.argument("approval_id")
@click.option("--json", "as_json", is_flag=True, help="Output JSON.")
def revoke_cmd(approval_id: str, as_json: bool):
    """Revoke an approval contract."""
    try:
        contract = revoke_approval(approval_id)
        emit(contract.to_dict(), json=as_json, human_lines=f"Revoked approval: {contract.approval_id}")
    except DriveError as e:
        emit_error(e, json=as_json)
