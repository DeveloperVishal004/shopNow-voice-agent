import csv
import os
import asyncio
from loguru import logger
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

# Must do this dance since we might run seed.py directly
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.config import settings
from backend.db.models import Order
from backend.db.database import Base

DATABASE_URL = f"sqlite+aiosqlite:///{settings.database_url}"

async def seed_orders():
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "Orderlist.csv")
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found at {csv_path}")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(bind=engine, autoflush=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
    async with SessionLocal() as session:
        # Check if already seeded
        result = await session.execute(select(Order).limit(1))
        existing = result.scalar_one_or_none()
        
        if existing:
            logger.info("Database is already seeded with orders. Skipping seed.")
            return

        logger.info(f"Seeding database from {csv_path}...")
        
        added_count = 0
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map CSV columns to Order model fields
                # Order id,Product,Purchaser,Price,Units Purchased,Total cost,Seller,Buy Date,Payment status,Payment Mode,Delivery status,Refund status
                
                # Mocking a customer_id and phone for the DB schema since it's missing in CSV
                customer_id = f"CUST-{row['Order id'].replace('ORD-', '')}"
                
                # Making up dummy phone based on ID to let the phone-lookup fallback work for tests
                # E.g. ORD-1001 -> +919876501001
                phone_suffix = row['Order id'].replace("ORD-", "").zfill(4)
                customer_phone = f"+9198765{phone_suffix}"
                
                # N/A handling
                delivery_date = "" if row['Delivery status'] in ("Processing", "Cancelled", "Out for Delivery") else "2026-03-20"
                refund_status = "none" if row['Refund status'] == "N/A" else row['Refund status'].lower()
                status = row['Delivery status'].lower()
                
                order = Order(
                    id=row['Order id'],
                    customer_id=customer_id,
                    customer_name=row['Purchaser'],
                    customer_phone=customer_phone,
                    status=status,
                    item_name=row['Product'],
                    price=str(row['Price']),
                    units_purchased=str(row['Units Purchased']),
                    total_cost=str(row['Total cost']),
                    seller=row['Seller'],
                    payment_status=row['Payment status'],
                    payment_mode=row['Payment Mode'],
                    order_date=row['Buy Date'],
                    delivery_date=delivery_date,
                    return_eligible="yes" if status == "delivered" else "no",
                    refund_status=refund_status
                )
                session.add(order)
                added_count += 1
                
        await session.commit()
        logger.info(f"Successfully inserted {added_count} orders into the database.")

if __name__ == "__main__":
    asyncio.run(seed_orders())
