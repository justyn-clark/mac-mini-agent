"""Approval contracts for dangerous or irreversible drive actions.

Contracts are durable JSON files with explicit expiry, revocation, and use limits.
They are designed to be shared across command surfaces instead of inventing one-off
approval flags per command.
"""
from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from modules.errors import (
    ApprovalExhaustedError,
    ApprovalExpiredError,
    ApprovalNotFoundError,
    ApprovalRevokedError,
)

APPROVAL_DIR = Path.home() / ".mac-mini-agent" / "approvals"


@dataclass
class ApprovalContract:
    approval_id: str
    action: str
    target: str
    created_at: int
    expires_at: int | None
    revoked_at: int | None
    max_uses: int | None
    uses: int
    metadata: dict

    @property
    def uses_remaining(self) -> int | None:
        if self.max_uses is None:
            return None
        return max(self.max_uses - self.uses, 0)

    @property
    def single_use(self) -> bool:
        return self.max_uses == 1

    def to_dict(self) -> dict:
        return {
            "ok": True,
            "approval": {
                "id": self.approval_id,
                "action": self.action,
                "target": self.target,
                "created_at": self.created_at,
                "expires_at": self.expires_at,
                "revoked_at": self.revoked_at,
                "max_uses": self.max_uses,
                "uses": self.uses,
                "uses_remaining": self.uses_remaining,
                "single_use": self.single_use,
                "metadata": self.metadata,
            },
        }


def _ensure_dir() -> None:
    APPROVAL_DIR.mkdir(parents=True, exist_ok=True)


def _path(approval_id: str) -> Path:
    return APPROVAL_DIR / f"{approval_id}.json"


def issue_approval(
    *,
    action: str,
    target: str,
    ttl_seconds: int | None = None,
    max_uses: int | None = 1,
    metadata: dict | None = None,
) -> ApprovalContract:
    _ensure_dir()
    now = int(time.time())
    approval_id = secrets.token_hex(8)
    contract = ApprovalContract(
        approval_id=approval_id,
        action=action,
        target=target,
        created_at=now,
        expires_at=(now + ttl_seconds) if ttl_seconds else None,
        revoked_at=None,
        max_uses=max_uses,
        uses=0,
        metadata=metadata or {},
    )
    _write(contract)
    return contract


def load_approval(approval_id: str) -> ApprovalContract:
    path = _path(approval_id)
    if not path.exists():
        raise ApprovalNotFoundError(approval_id)
    data = json.loads(path.read_text())
    return ApprovalContract(
        approval_id=data["approval_id"],
        action=data["action"],
        target=data["target"],
        created_at=data["created_at"],
        expires_at=data.get("expires_at"),
        revoked_at=data.get("revoked_at"),
        max_uses=data.get("max_uses"),
        uses=data.get("uses", 0),
        metadata=data.get("metadata") or {},
    )


def _write(contract: ApprovalContract) -> None:
    payload = {
        "approval_id": contract.approval_id,
        "action": contract.action,
        "target": contract.target,
        "created_at": contract.created_at,
        "expires_at": contract.expires_at,
        "revoked_at": contract.revoked_at,
        "max_uses": contract.max_uses,
        "uses": contract.uses,
        "metadata": contract.metadata,
    }
    _path(contract.approval_id).write_text(json.dumps(payload, indent=2, sort_keys=True))


def revoke_approval(approval_id: str) -> ApprovalContract:
    contract = load_approval(approval_id)
    contract.revoked_at = int(time.time())
    _write(contract)
    return contract


def validate_approval(
    approval_id: str,
    *,
    action: str | None = None,
    target: str | None = None,
    consume: bool = False,
) -> ApprovalContract:
    contract = load_approval(approval_id)
    now = int(time.time())

    if contract.revoked_at is not None:
        raise ApprovalRevokedError(approval_id)
    if contract.expires_at is not None and now > contract.expires_at:
        raise ApprovalExpiredError(approval_id)
    if contract.max_uses is not None and contract.uses >= contract.max_uses:
        raise ApprovalExhaustedError(approval_id)
    if action is not None and contract.action != action:
        raise ApprovalRevokedError(approval_id, reason=f"action mismatch: expected {contract.action}, got {action}")
    if target is not None and contract.target != target:
        raise ApprovalRevokedError(approval_id, reason=f"target mismatch: expected {contract.target}, got {target}")

    if consume:
        contract.uses += 1
        _write(contract)

    return contract


def list_approvals(include_revoked: bool = True) -> list[ApprovalContract]:
    _ensure_dir()
    approvals: list[ApprovalContract] = []
    for path in sorted(APPROVAL_DIR.glob("*.json")):
        try:
            contract = load_approval(path.stem)
        except ApprovalNotFoundError:
            continue
        if not include_revoked and contract.revoked_at is not None:
            continue
        approvals.append(contract)
    approvals.sort(key=lambda a: a.created_at, reverse=True)
    return approvals
