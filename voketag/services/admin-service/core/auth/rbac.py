"""
RBAC - Role-Based Access Control.
Roles: SuperAdmin > Admin > Compliance > FactoryManager > Viewer
"""

from typing import List

ADMIN_ROLES = ["super_admin", "admin", "compliance", "factory_manager", "viewer"]

ROLE_ORDER = {
    "super_admin": 4,
    "admin": 3,
    "compliance": 2,
    "factory_manager": 1,
    "viewer": 0,
}


def role_has_permission(user_role: str, required_role: str) -> bool:
    """Check if user_role has at least the permission level of required_role."""
    return ROLE_ORDER.get(user_role, -1) >= ROLE_ORDER.get(required_role, 0)


def require_roles(required_roles: List[str]):
    """Return a dep that requires user to have one of the roles."""
    def _check(current_user: dict) -> dict:
        role = (current_user.get("role") or "").lower().replace(" ", "_")
        if role not in ADMIN_ROLES:
            role = "admin"
        for r in required_roles:
            rn = r.lower().replace(" ", "_")
            if role_has_permission(role, rn):
                return current_user
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return _check
