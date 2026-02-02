"""Script to reset database - DROP all project tables and recreate them."""

import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

async def reset_database():
    print(f"🔗 Connecting to: {DATABASE_URL.split('@')[-1]}") # Chỉ hiện host để bảo mật
    engine = create_async_engine(DATABASE_URL)
    
    async with engine.begin() as conn:
        print("🗑️ Dropping existing tables (findings, ports, targets, embeddings)...")
        # Danh sách các bảng cần xóa
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
    if not os.getenv("DATABASE_URL") or "xxx" in os.getenv("DATABASE_URL"):
        print("❌ LỖI: Bạn chưa cập nhật DATABASE_URL thực tế trong file .env!")
    else:
        asyncio.run(reset_database())
