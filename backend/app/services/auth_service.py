from flask import request
from app.extensions import db
from app.models.user import AuditLog


class AuthService:
    """Only _log_audit is actually used -- every other method that used to
    live here (register, login, logout, refresh_token, get_current_user,
    update_profile, change_password, list_users, get_user, delete_user,
    get_sessions, revoke_session, get_audit_logs) duplicated logic that's
    implemented directly in app/api/auth.py and app/api/users.py instead,
    was never called from anywhere, and (register() in particular) was
    broken against the current UserRole enum. Removed rather than kept as
    unreachable dead code."""

    @staticmethod
    def _log_audit(user_id, action, resource_type, resource_id=None, description=None,
                   old_values=None, new_values=None, status='success', error_message=None,
                   duration_ms=None, metadata=None):
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                description=description,
                old_values=old_values,
                new_values=new_values,
                ip_address=request.remote_addr if request else None,
                user_agent=request.user_agent.string if request else None,
                status=status,
                error_message=error_message,
                duration_ms=duration_ms,
                audit_metadata=metadata
            )
            db.session.add(audit)
            db.session.commit()
        except Exception:
            db.session.rollback()
