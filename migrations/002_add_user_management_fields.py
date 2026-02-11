"""
Migration: Add user management fields
Date: 2026-02-06
"""

async def up(db):
    users = db.users

    await users.update_many(
        {},
        {
            "$set": {
                "is_active": True,
                "invited_by": None,
                "invitation_token": None,
                "invitation_expires_at": None,
                "last_login": None,
                "password_reset_token": None,
                "password_reset_expires_at": None,
            }
        },
    )

    admin_count = await users.count_documents({"role": "admin"})
    if admin_count == 0:
        first_user = await users.find_one(sort=[("created_at", 1)])
        if first_user:
            await users.update_one(
                {"_id": first_user["_id"]},
                {"$set": {"role": "admin"}},
            )


async def down(db):
    users = db.users
    await users.update_many(
        {},
        {
            "$unset": {
                "is_active": "",
                "invited_by": "",
                "invitation_token": "",
                "invitation_expires_at": "",
                "last_login": "",
                "password_reset_token": "",
                "password_reset_expires_at": "",
            }
        },
    )
