"""Security repository — users, roles, audit logs, sessions, settings."""

from __future__ import annotations

import threading
import uuid
from abc import ABC, abstractmethod
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import delete, select, update

from auth.permissions import DEFAULT_ROLES, PERMISSIONS, resolve_user_permissions
from db.orm.models import AuditLogORM, DepartmentSettingORM, RoleORM, RolePermissionORM, UserORM, UserPasswordHistoryORM, UserRoleORM, UserSessionORM
from db.session import session_scope
from models.security import AuditLogEntry, DepartmentSettings, PasswordPolicy, Role, User, UserSession, UserStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SecurityRepository(ABC):
    @abstractmethod
    def seed_defaults(self) -> None: ...

    @abstractmethod
    def get_user_by_id(self, user_id: str) -> Optional[User]: ...

    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]: ...

    @abstractmethod
    def get_user_password_hash(self, user_id: str) -> Optional[str]: ...

    @abstractmethod
    def list_users(self, limit: int = 100) -> List[User]: ...

    @abstractmethod
    def create_user(self, user: User, password_hash: str) -> User: ...

    @abstractmethod
    def update_user(self, user: User, password_hash: Optional[str] = None) -> User: ...

    @abstractmethod
    def delete_user(self, user_id: str) -> None: ...

    @abstractmethod
    def list_roles(self) -> List[Role]: ...

    @abstractmethod
    def list_permissions(self) -> list: ...

    @abstractmethod
    def append_password_history(self, user_id: str, password_hash: str) -> None: ...

    @abstractmethod
    def get_password_history(self, user_id: str, limit: int = 5) -> List[str]: ...

    @abstractmethod
    def create_session(self, session: UserSession) -> UserSession: ...

    @abstractmethod
    def get_session_by_refresh_hash(self, refresh_hash: str) -> Optional[UserSession]: ...

    @abstractmethod
    def list_user_sessions(self, user_id: str) -> List[UserSession]: ...

    @abstractmethod
    def revoke_session(self, session_token: str) -> None: ...

    @abstractmethod
    def revoke_all_sessions(self, user_id: str, except_token: Optional[str] = None) -> int: ...

    @abstractmethod
    def touch_session(self, session_token: str) -> None: ...

    @abstractmethod
    def append_audit_log(self, entry: AuditLogEntry) -> AuditLogEntry: ...

    @abstractmethod
    def list_audit_logs(self, limit: int = 100, user_id: Optional[str] = None) -> List[AuditLogEntry]: ...

    @abstractmethod
    def get_settings(self) -> DepartmentSettings: ...

    @abstractmethod
    def save_settings(self, settings: DepartmentSettings) -> DepartmentSettings: ...

    @abstractmethod
    def user_count(self) -> int: ...

    @abstractmethod
    def clear_all(self) -> None: ...


def _hydrate_user(user: User, roles: List[Role]) -> User:
    role_map = {r.role_id: r for r in roles}
    role_names = []
    perms: set[str] = set()
    for rid in user.role_ids:
        role = role_map.get(rid)
        if role:
            role_names.append(role.name)
            perms.update(role.permissions)
    user.roles = role_names
    user.permissions = sorted(perms)
    return user


class MemorySecurityRepository(SecurityRepository):
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._users: dict[str, User] = {}
        self._passwords: dict[str, str] = {}
        self._pwd_history: dict[str, list[str]] = {}
        self._roles: dict[str, Role] = {r.role_id: deepcopy(r) for r in DEFAULT_ROLES}
        self._sessions: dict[str, UserSession] = {}
        self._refresh_map: dict[str, str] = {}
        self._audit_logs: list[AuditLogEntry] = []
        self._settings = DepartmentSettings()
        self._seeded = False

    def seed_defaults(self) -> None:
        with self._lock:
            if self._seeded:
                return
            self._seeded = True

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return None
            return _hydrate_user(deepcopy(user), list(self._roles.values()))

    def get_user_by_username(self, username: str) -> Optional[User]:
        with self._lock:
            for user in self._users.values():
                if user.username.lower() == username.lower():
                    return _hydrate_user(deepcopy(user), list(self._roles.values()))
            return None

    def get_user_password_hash(self, user_id: str) -> Optional[str]:
        with self._lock:
            return self._passwords.get(user_id)

    def list_users(self, limit: int = 100) -> List[User]:
        with self._lock:
            items = [_hydrate_user(deepcopy(u), list(self._roles.values())) for u in self._users.values()]
            return items[:limit]

    def create_user(self, user: User, password_hash: str) -> User:
        with self._lock:
            self._users[user.user_id] = deepcopy(user)
            self._passwords[user.user_id] = password_hash
            return _hydrate_user(deepcopy(user), list(self._roles.values()))

    def update_user(self, user: User, password_hash: Optional[str] = None) -> User:
        with self._lock:
            user.updated_at = User.now_iso()
            self._users[user.user_id] = deepcopy(user)
            if password_hash:
                self._passwords[user.user_id] = password_hash
            return _hydrate_user(deepcopy(user), list(self._roles.values()))

    def delete_user(self, user_id: str) -> None:
        with self._lock:
            self._users.pop(user_id, None)
            self._passwords.pop(user_id, None)

    def list_roles(self) -> List[Role]:
        with self._lock:
            return [deepcopy(r) for r in self._roles.values()]

    def list_permissions(self) -> list:
        return PERMISSIONS

    def append_password_history(self, user_id: str, password_hash: str) -> None:
        with self._lock:
            self._pwd_history.setdefault(user_id, []).insert(0, password_hash)

    def get_password_history(self, user_id: str, limit: int = 5) -> List[str]:
        with self._lock:
            return list(self._pwd_history.get(user_id, [])[:limit])

    def create_session(self, session: UserSession) -> UserSession:
        with self._lock:
            self._sessions[session.session_token] = deepcopy(session)
            if session.refresh_token_hash:
                self._refresh_map[session.refresh_token_hash] = session.session_token
            return deepcopy(session)

    def get_session_by_refresh_hash(self, refresh_hash: str) -> Optional[UserSession]:
        with self._lock:
            token = self._refresh_map.get(refresh_hash)
            if not token:
                return None
            return deepcopy(self._sessions.get(token))

    def list_user_sessions(self, user_id: str) -> List[UserSession]:
        with self._lock:
            return [deepcopy(s) for s in self._sessions.values() if s.user_id == user_id and s.is_active]

    def revoke_session(self, session_token: str) -> None:
        with self._lock:
            s = self._sessions.get(session_token)
            if s:
                s.is_active = False

    def revoke_all_sessions(self, user_id: str, except_token: Optional[str] = None) -> int:
        count = 0
        with self._lock:
            for s in self._sessions.values():
                if s.user_id == user_id and s.is_active and s.session_token != except_token:
                    s.is_active = False
                    count += 1
        return count

    def touch_session(self, session_token: str) -> None:
        with self._lock:
            s = self._sessions.get(session_token)
            if s:
                s.last_activity_at = User.now_iso()

    def append_audit_log(self, entry: AuditLogEntry) -> AuditLogEntry:
        with self._lock:
            self._audit_logs.insert(0, deepcopy(entry))
            if len(self._audit_logs) > 5000:
                self._audit_logs = self._audit_logs[:5000]
            return deepcopy(entry)

    def list_audit_logs(self, limit: int = 100, user_id: Optional[str] = None) -> List[AuditLogEntry]:
        with self._lock:
            items = self._audit_logs
            if user_id:
                items = [e for e in items if e.user_id == user_id]
            return [deepcopy(e) for e in items[:limit]]

    def get_settings(self) -> DepartmentSettings:
        with self._lock:
            return deepcopy(self._settings)

    def save_settings(self, settings: DepartmentSettings) -> DepartmentSettings:
        with self._lock:
            self._settings = deepcopy(settings)
            return deepcopy(self._settings)

    def user_count(self) -> int:
        with self._lock:
            return len(self._users)

    def clear_all(self) -> None:
        with self._lock:
            self._users.clear()
            self._passwords.clear()
            self._sessions.clear()
            self._refresh_map.clear()
            self._audit_logs.clear()
            self._seeded = False


class PostgresSecurityRepository(SecurityRepository):
    def seed_defaults(self) -> None:
        with session_scope() as db:
            if db.scalar(select(UserORM).limit(1)):
                return
            for role in DEFAULT_ROLES:
                db.merge(RoleORM(role_id=role.role_id, name=role.name, label=role.label, description=role.description, is_system=role.is_system))
                for perm in role.permissions:
                    db.merge(RolePermissionORM(role_id=role.role_id, permission_code=perm))

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with session_scope() as db:
            row = db.get(UserORM, uuid.UUID(user_id))
            if not row:
                return None
            return self._to_user(row, db)

    def get_user_by_username(self, username: str) -> Optional[User]:
        with session_scope() as db:
            row = db.scalar(select(UserORM).where(UserORM.username == username))
            if not row:
                return None
            return self._to_user(row, db)

    def get_user_password_hash(self, user_id: str) -> Optional[str]:
        with session_scope() as db:
            row = db.get(UserORM, uuid.UUID(user_id))
            return row.password_hash if row else None

    def list_users(self, limit: int = 100) -> List[User]:
        with session_scope() as db:
            rows = db.scalars(select(UserORM).limit(limit)).all()
            return [self._to_user(r, db) for r in rows]

    def create_user(self, user: User, password_hash: str) -> User:
        with session_scope() as db:
            row = UserORM(
                user_id=uuid.UUID(user.user_id),
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                department=user.department,
                office=user.office,
                designation=user.designation,
                status=user.status.value,
                password_hash=password_hash,
                must_change_password=user.must_change_password,
            )
            db.add(row)
            for rid in user.role_ids:
                db.add(UserRoleORM(user_id=row.user_id, role_id=rid))
            db.flush()
            return self._to_user(row, db)

    def update_user(self, user: User, password_hash: Optional[str] = None) -> User:
        with session_scope() as db:
            row = db.get(UserORM, uuid.UUID(user.user_id))
            if not row:
                raise ValueError("User not found")
            row.email = user.email
            row.full_name = user.full_name
            row.department = user.department
            row.office = user.office
            row.designation = user.designation
            row.status = user.status.value
            row.must_change_password = user.must_change_password
            row.last_login_at = datetime.fromisoformat(user.last_login_at) if user.last_login_at else row.last_login_at
            if password_hash:
                row.password_hash = password_hash
                row.password_changed_at = _utcnow()
            db.execute(delete(UserRoleORM).where(UserRoleORM.user_id == row.user_id))
            for rid in user.role_ids:
                db.add(UserRoleORM(user_id=row.user_id, role_id=rid))
            db.flush()
            return self._to_user(row, db)

    def delete_user(self, user_id: str) -> None:
        with session_scope() as db:
            db.execute(delete(UserORM).where(UserORM.user_id == uuid.UUID(user_id)))

    def list_roles(self) -> List[Role]:
        with session_scope() as db:
            rows = db.scalars(select(RoleORM)).all()
            result = []
            for r in rows:
                perms = db.scalars(select(RolePermissionORM.permission_code).where(RolePermissionORM.role_id == r.role_id)).all()
                result.append(Role(role_id=r.role_id, name=r.name, label=r.label, description=r.description or "", permissions=list(perms), is_system=r.is_system))
            return result

    def list_permissions(self) -> list:
        return PERMISSIONS

    def append_password_history(self, user_id: str, password_hash: str) -> None:
        with session_scope() as db:
            db.add(UserPasswordHistoryORM(user_id=uuid.UUID(user_id), password_hash=password_hash))

    def get_password_history(self, user_id: str, limit: int = 5) -> List[str]:
        with session_scope() as db:
            rows = db.scalars(
                select(UserPasswordHistoryORM.password_hash)
                .where(UserPasswordHistoryORM.user_id == uuid.UUID(user_id))
                .order_by(UserPasswordHistoryORM.created_at.desc())
                .limit(limit)
            ).all()
            return list(rows)

    def create_session(self, session: UserSession) -> UserSession:
        with session_scope() as db:
            db.add(
                UserSessionORM(
                    session_token=session.session_token,
                    user_id=uuid.UUID(session.user_id),
                    refresh_token_hash=session.refresh_token_hash,
                    ip_address=session.ip_address,
                    user_agent=session.user_agent,
                    is_active=session.is_active,
                    expires_at=datetime.fromisoformat(session.expires_at) if session.expires_at else _utcnow() + timedelta(days=7),
                )
            )
        return session

    def get_session_by_refresh_hash(self, refresh_hash: str) -> Optional[UserSession]:
        with session_scope() as db:
            row = db.scalar(select(UserSessionORM).where(UserSessionORM.refresh_token_hash == refresh_hash, UserSessionORM.is_active.is_(True)))
            return self._to_session(row) if row else None

    def list_user_sessions(self, user_id: str) -> List[UserSession]:
        with session_scope() as db:
            rows = db.scalars(select(UserSessionORM).where(UserSessionORM.user_id == uuid.UUID(user_id), UserSessionORM.is_active.is_(True))).all()
            return [self._to_session(r) for r in rows]

    def revoke_session(self, session_token: str) -> None:
        with session_scope() as db:
            db.execute(update(UserSessionORM).where(UserSessionORM.session_token == session_token).values(is_active=False))

    def revoke_all_sessions(self, user_id: str, except_token: Optional[str] = None) -> int:
        with session_scope() as db:
            q = update(UserSessionORM).where(UserSessionORM.user_id == uuid.UUID(user_id), UserSessionORM.is_active.is_(True))
            if except_token:
                q = q.where(UserSessionORM.session_token != except_token)
            result = db.execute(q.values(is_active=False))
            return result.rowcount or 0

    def touch_session(self, session_token: str) -> None:
        with session_scope() as db:
            db.execute(update(UserSessionORM).where(UserSessionORM.session_token == session_token).values(last_activity_at=_utcnow()))

    def append_audit_log(self, entry: AuditLogEntry) -> AuditLogEntry:
        with session_scope() as db:
            db.add(
                AuditLogORM(
                    log_id=uuid.UUID(entry.log_id),
                    user_id=uuid.UUID(entry.user_id) if entry.user_id and entry.user_id != "system-bypass" else None,
                    username=entry.username,
                    action=entry.action,
                    resource_type=entry.resource_type,
                    resource_id=entry.resource_id,
                    dealer_name=entry.dealer_name,
                    gstin=entry.gstin,
                    session_id=entry.session_id,
                    ip_address=entry.ip_address,
                    user_agent=entry.user_agent,
                    result=entry.result,
                    details=entry.details,
                )
            )
        return entry

    def list_audit_logs(self, limit: int = 100, user_id: Optional[str] = None) -> List[AuditLogEntry]:
        with session_scope() as db:
            q = select(AuditLogORM).order_by(AuditLogORM.timestamp.desc()).limit(limit)
            if user_id:
                q = q.where(AuditLogORM.user_id == uuid.UUID(user_id))
            rows = db.scalars(q).all()
            return [self._to_audit(r) for r in rows]

    def get_settings(self) -> DepartmentSettings:
        with session_scope() as db:
            row = db.get(DepartmentSettingORM, "department")
            if not row:
                return DepartmentSettings()
            return DepartmentSettings.model_validate(row.payload)

    def save_settings(self, settings: DepartmentSettings) -> DepartmentSettings:
        with session_scope() as db:
            db.merge(DepartmentSettingORM(key="department", payload=settings.model_dump()))
        return settings

    def user_count(self) -> int:
        with session_scope() as db:
            rows = db.scalars(select(UserORM.user_id)).all()
            return len(rows)

    def clear_all(self) -> None:
        with session_scope() as db:
            db.execute(delete(AuditLogORM))
            db.execute(delete(UserSessionORM))
            db.execute(delete(UserPasswordHistoryORM))
            db.execute(delete(UserRoleORM))
            db.execute(delete(UserORM))
            db.execute(delete(RolePermissionORM))
            db.execute(delete(RoleORM))
            db.execute(delete(DepartmentSettingORM))

    def _to_user(self, row: UserORM, db) -> User:
        role_ids = db.scalars(select(UserRoleORM.role_id).where(UserRoleORM.user_id == row.user_id)).all()
        roles = db.scalars(select(RoleORM).where(RoleORM.role_id.in_(role_ids))).all() if role_ids else []
        role_names = [r.name for r in roles]
        perms: set[str] = set()
        for r in roles:
            codes = db.scalars(select(RolePermissionORM.permission_code).where(RolePermissionORM.role_id == r.role_id)).all()
            perms.update(codes)
        return User(
            user_id=str(row.user_id),
            username=row.username,
            email=row.email or "",
            full_name=row.full_name or "",
            department=row.department or "",
            office=row.office or "",
            designation=row.designation or "",
            role_ids=list(role_ids),
            roles=role_names,
            permissions=sorted(perms),
            status=UserStatus(row.status),
            must_change_password=row.must_change_password,
            password_changed_at=row.password_changed_at.isoformat() if row.password_changed_at else None,
            last_login_at=row.last_login_at.isoformat() if row.last_login_at else None,
            created_at=row.created_at.isoformat() if row.created_at else "",
            updated_at=row.updated_at.isoformat() if row.updated_at else "",
        )

    @staticmethod
    def _to_session(row: UserSessionORM) -> UserSession:
        return UserSession(
            session_token=row.session_token,
            user_id=str(row.user_id),
            refresh_token_hash=row.refresh_token_hash,
            ip_address=row.ip_address or "",
            user_agent=row.user_agent or "",
            is_active=row.is_active,
            last_activity_at=row.last_activity_at.isoformat() if row.last_activity_at else "",
            created_at=row.created_at.isoformat() if row.created_at else "",
            expires_at=row.expires_at.isoformat() if row.expires_at else "",
        )

    @staticmethod
    def _to_audit(row: AuditLogORM) -> AuditLogEntry:
        return AuditLogEntry(
            log_id=str(row.log_id),
            timestamp=row.timestamp.isoformat() if row.timestamp else "",
            user_id=str(row.user_id) if row.user_id else "",
            username=row.username or "",
            action=row.action,
            resource_type=row.resource_type or "",
            resource_id=row.resource_id or "",
            dealer_name=row.dealer_name or "",
            gstin=row.gstin or "",
            session_id=row.session_id or "",
            ip_address=row.ip_address or "",
            user_agent=row.user_agent or "",
            result=row.result or "success",
            details=row.details or {},
        )


_security_repo: Optional[SecurityRepository] = None
_security_lock = threading.Lock()


def get_security_repository() -> SecurityRepository:
    global _security_repo
    if _security_repo is None:
        with _security_lock:
            if _security_repo is None:
                from config.settings import get_settings

                if get_settings().is_postgres:
                    _security_repo = PostgresSecurityRepository()
                else:
                    _security_repo = MemorySecurityRepository()
    return _security_repo


def reset_security_repository() -> None:
    global _security_repo
    _security_repo = None
