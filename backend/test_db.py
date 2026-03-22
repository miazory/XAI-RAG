import asyncio
import os
import sys

# Tambahkan backend ke path
sys.path.insert(0, r"d:\S3 Peneliatian\XAI RAG\backend")

from app.database import get_db, init_db, AsyncSessionLocal
from app.models.user import User
import uuid

async def test_insert():
    async with AsyncSessionLocal() as session:
        try:
            # Try to query first
            from sqlalchemy import select
            res = await session.execute(select(User).limit(1))
            print("Query passed")
            
            # Try to insert
            new_user = User(
                id=str(uuid.uuid4()),
                name="Test Script User",
                email="test_script@gmail.com",
                hashed_password="fakehash",
                role="petani",
            )
            session.add(new_user)
            await session.commit()
            print("Insert passed!")
        except Exception as e:
            print(f"Error occurred: {type(e).__name__} - {e}")

asyncio.run(test_insert())
