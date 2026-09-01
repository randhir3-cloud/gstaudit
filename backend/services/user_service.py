"""User management service."""

from __future__ import annotations

import uuid
from typing import List, Optional

from auth.password import hash_password, validate_password, verify_password
from models.security import Role, User, UserCreateRequest, UserStatus, UserUpdateRequest
from repositories.security_repository import get_security_repository
from services.audit_log_service import log_audit_event


def _repo():
    return get_security_repository()


def list_users(limit: int = 100) -> List[User]:
    return _repo().list_users(limit=limit)


def list_roles() -> List[Role]:
    return _repo().list_roles()


def list_permissions():
    return _repo().list_permissions()


def create_user(request: UserCreateRequest, actor: User) -> User:
    repo = _repo()
    if repo.get_user_by_username(request.username):
        raise ValueError("Username already exists")
    policy = repo.get_settings().password_policy
    validate_password(request.password, policy)
    user = User(
        user_id=str(uuid.uuid4()),
        username=request.username,
        email=request.email,
        full_name=request.full_name,
        department=request.department,
        office=request.office,
        designation=request.designation,
        role_ids=request.role_ids or ["role_officer"],
        status=request.status,
        must_change_password=True,
        created_at=User.now_iso(),
        updated_at=User.now_iso(),
    )
    pwd_hash = hash_password(request.password)
    saved = repo.create_user(user, pwd_hash)
    log_audit_event(actor, "user_created", resource_type="user", resource_id=saved.user_id, details={"username": saved.username})
    return saved


def update_user(user_id: str, request: UserUpdateRequest, actor: User) -> User:
    repo = _repo()
    user = repo.get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    if request.email is not None:
        user.email = request.email
    if request.full_name is not None:
        user.full_name = request.full_name
    if request.department is not None:
        user.department = request.department
    if request.office is not None:
        user.office = request.office
    if request.designation is not None:
        user.designation = request.designation
    if request.role_ids is not None:
        user.role_ids = request.role_ids
    if request.status is not None:
        user.status = request.status
    pwd_hash = None
    if request.password:
        policy = repo.get_settings().password_policy
        history = repo.get_password_history(user_id)
        validate_password(request.password, policy, history)
        old_hash = repo.get_user_password_hash(user_id)
        if old_hash:
            repo.append_password_history(user_id, old_hash)
        pwd_hash = hash_password(request.password)
        user.password_changed_at = User.now_iso()
        user.must_change_password = False
    saved = repo.update_user(user, pwd_hash)
    log_audit_event(actor, "user_updated", resource_type="user", resource_id=user_id)
    return saved


def delete_user(user_id: str, actor: User) -> None:
    if user_id == actor.user_id:
        raise ValueError("Cannot delete your own account")
    _repo().delete_user(user_id)
    log_audit_event(actor, "user_deleted", resource_type="user", resource_id=user_id)
