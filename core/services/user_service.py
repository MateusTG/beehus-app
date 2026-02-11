from datetime import timedelta
from typing import Optional

from core.auth import generate_secure_token, get_password_hash
from core.config import settings
from core.models.mongo_models import User
from core.services.email_service import send_invitation_email, send_password_reset_email
from core.utils.date_utils import get_now


def _require_admin(user: User) -> None:
    if user.role != "admin":
        raise PermissionError("Admin privileges required")


async def ensure_admin_exists() -> None:
    existing_admin = await User.find_one(User.role == "admin")
    if existing_admin:
        return

    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        print("Admin bootstrap skipped: ADMIN_EMAIL or ADMIN_PASSWORD missing.")
        return

    existing_user = await User.find_one(User.email == settings.ADMIN_EMAIL)
    if existing_user:
        existing_user.role = "admin"
        existing_user.is_active = True
        if settings.ADMIN_FULL_NAME and not existing_user.full_name:
            existing_user.full_name = settings.ADMIN_FULL_NAME
        await existing_user.save()
        print(f"Admin user promoted: {settings.ADMIN_EMAIL}")
        return

    admin_user = User(
        email=settings.ADMIN_EMAIL,
        password_hash=get_password_hash(settings.ADMIN_PASSWORD),
        full_name=settings.ADMIN_FULL_NAME,
        role="admin",
        is_active=True,
    )
    await admin_user.save()
    print(f"Admin user created: {settings.ADMIN_EMAIL}")


async def create_invitation(admin_user: User, email: str, full_name: Optional[str], role: str) -> dict:
    _require_admin(admin_user)

    existing = await User.find_one(User.email == email)
    if existing:
        raise ValueError("Email already registered")

    if role not in ["admin", "user"]:
        raise ValueError("Invalid role")

    token = generate_secure_token()
    expires_at = get_now() + timedelta(hours=48)
    placeholder_password = get_password_hash(generate_secure_token())

    user = User(
        email=email,
        password_hash=placeholder_password,
        full_name=full_name,
        role=role,
        invited_by=admin_user.id,
        invitation_token=token,
        invitation_expires_at=expires_at,
        is_active=True,
    )
    await user.save()

    base_url = settings.FRONTEND_URL.rstrip("/")
    invitation_link = f"{base_url}/accept-invitation?token={token}"
    invited_by_name = admin_user.full_name or admin_user.email
    email_sent = await send_invitation_email(
        to_email=email,
        invitation_link=invitation_link,
        invited_by=invited_by_name,
        full_name=full_name or "",
    )

    return {
        "invitation_token": token,
        "invitation_link": invitation_link,
        "expires_at": expires_at,
        "email_sent": email_sent,
    }


async def accept_invitation(token: str, password: str, full_name: Optional[str] = None) -> User:
    user = await User.find_one(User.invitation_token == token)
    if not user:
        raise ValueError("Invalid invitation token")

    if user.invitation_expires_at and user.invitation_expires_at < get_now():
        raise ValueError("Invitation expired")

    user.password_hash = get_password_hash(password)
    user.invitation_token = None
    user.invitation_expires_at = None
    if full_name:
        user.full_name = full_name
    await user.save()
    return user


async def request_password_reset(email: str) -> dict:
    user = await User.find_one(User.email == email)
    if not user or not user.is_active or user.invitation_token:
        return {"email_sent": False}

    token = generate_secure_token()
    expires_at = get_now() + timedelta(hours=1)
    user.password_reset_token = token
    user.password_reset_expires_at = expires_at
    await user.save()

    base_url = settings.FRONTEND_URL.rstrip("/")
    reset_link = f"{base_url}/reset-password?token={token}"
    email_sent = await send_password_reset_email(user.email, reset_link)

    return {"email_sent": email_sent}


async def reset_password(token: str, new_password: str) -> bool:
    user = await User.find_one(User.password_reset_token == token)
    if not user:
        raise ValueError("Invalid reset token")

    if user.password_reset_expires_at and user.password_reset_expires_at < get_now():
        raise ValueError("Reset token expired")

    user.password_hash = get_password_hash(new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    await user.save()
    return True


async def list_users(requesting_user: User) -> list[User]:
    _require_admin(requesting_user)
    return await User.find_all().to_list()


async def update_user(admin_user: User, user_id: str, updates: dict) -> User:
    _require_admin(admin_user)

    user = await User.get(user_id)
    if not user:
        raise ValueError("User not found")

    if "full_name" in updates and updates["full_name"] is not None:
        user.full_name = updates["full_name"]
    if "role" in updates and updates["role"] is not None:
        if updates["role"] not in ["admin", "user"]:
            raise ValueError("Invalid role")
        user.role = updates["role"]

    await user.save()
    return user


async def deactivate_user(admin_user: User, user_id: str) -> bool:
    _require_admin(admin_user)
    user = await User.get(user_id)
    if not user:
        raise ValueError("User not found")
    user.is_active = False
    await user.save()
    return True


async def activate_user(admin_user: User, user_id: str) -> bool:
    _require_admin(admin_user)
    user = await User.get(user_id)
    if not user:
        raise ValueError("User not found")
    user.is_active = True
    await user.save()
    return True


async def get_user_activity(user_id: str) -> dict:
    user = await User.get(user_id)
    if not user:
        raise ValueError("User not found")
    return {"last_login": user.last_login}
