from fastapi import HTTPException, status

ROLE_USER = "user"
ROLE_ADMIN = "admin"

GROUP_VIEW = "can_view"
GROUP_CREATE = "can_create"
GROUP_EDIT = "can_edit"
GROUP_DELETE = "can_delete"


def require_role(user_role: str, required_role: str) -> None:
    if user_role != required_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def require_group_permission(member, permission: str) -> None:
    if permission not in {
        GROUP_VIEW,
        GROUP_CREATE,
        GROUP_EDIT,
        GROUP_DELETE,
    }:
        raise ValueError(f"Unknown group permission: {permission}")

    if not getattr(member, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission for this action",
        )
