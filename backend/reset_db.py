"""Script to reset database - DROP all project tables and recreate them."""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def reset_database():
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env")
        return
        
    print(f"🔗 Connecting to Database...")
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        print("🗑️ Dropping existing tables (findings, ports, targets, embeddings)...")
        tables = ["findings", "ports", "targets", "embeddings"]
        for table in tables:
            try:
                await conn.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                print(f"   - Dropped {table}")
            except Exception as e:
                print(f"   - Error dropping {table}: {e}")
        
        print("🏗️ Creating new tables with refined schema...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database reset successfully!")

if __name__ == "__main__":
    if not DATABASE_URL or "xxx" in DATABASE_URL:
        print("❌ LỖI: Bạn chưa cập nhật DATABASE_URL thực tế trong file .env!")
    else:
        asyncio.run(reset_database())
