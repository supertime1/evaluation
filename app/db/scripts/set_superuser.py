#!/usr/bin/env python3
"""
Script to directly update a user to superuser status in the database.
Usage: python -m scripts.set_superuser email@example.com
"""

import asyncio
import sys
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db, engine
from app.models.user import User

async def set_user_as_superuser(email: str):
    """Set a user as superuser directly in the database."""
    print(f"Setting user {email} as superuser...")
    
    # Create session
    async with engine.begin() as conn:
        # Create a session with the connection
        session = AsyncSession(bind=conn)
        
        # Find user by email
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"Error: User with email {email} not found")
            return False
        
        # Update user to superuser
        user.is_superuser = True
        user.is_verified = True
        await session.commit()
        
        # Verify the update
        await session.refresh(user)
        print(f"User {email} is now a superuser: {user.is_superuser}")
        print(f"User {email} is now verified: {user.is_verified}")
        
        return True

async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.set_superuser email@example.com")
        return
    
    email = sys.argv[1]
    success = await set_user_as_superuser(email)
    
    if success:
        print(f"✅ Successfully set user {email} as superuser")
    else:
        print(f"❌ Failed to set user {email} as superuser")

if __name__ == "__main__":
    asyncio.run(main()) 