"""
Product repository with PostgreSQL COPY bulk operations.
Optimized for high-volume inserts.
"""

from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import asyncpg

from factory_service.domain.product.models import Product
from factory_service.config.settings import settings
from factory_service.core.logging_config import get_logger

logger = get_logger(__name__)


class ProductRepository:
    """Product repository with bulk operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def bulk_create(self, products_data: List[Dict]) -> int:
        """
        Bulk create products using PostgreSQL COPY.
        Retries COPY up to 3 times before falling back to INSERT.

        Args:
            products_data: List of product dictionaries

        Returns:
            Number of products inserted
        """
        if not products_data:
            return 0

        import asyncio

        max_copy_retries = 3
        last_error = None

        for attempt in range(max_copy_retries):
            try:
                if attempt > 0:
                    await asyncio.sleep(1 * attempt)  # Backoff: 1s, 2s
                logger.info(
                    f"Bulk creating {len(products_data)} products using COPY "
                    f"(attempt {attempt + 1}/{max_copy_retries})..."
                )

                connection = await self.session.connection()
                raw_connection = await connection.get_raw_connection()

                records = [
                    (
                        str(p["id"]),
                        str(p["batch_id"]),
                        p["token"],
                        p["verification_url"],
                        p.get("name"),
                        p.get("category"),
                        p.get("serial_number"),
                        p["created_at"],
                    )
                    for p in products_data
                ]

                await raw_connection.driver_connection.copy_records_to_table(
                    table_name="products",
                    records=records,
                    columns=[
                        "id",
                        "batch_id",
                        "token",
                        "verification_url",
                        "name",
                        "category",
                        "serial_number",
                        "created_at",
                    ],
                    schema_name="public",
                )

                logger.info(f"Successfully inserted {len(products_data)} products using COPY")
                return len(products_data)

            except Exception as e:
                last_error = e
                logger.warning(
                    f"COPY attempt {attempt + 1}/{max_copy_retries} failed: {e}"
                )

        logger.error(f"All COPY attempts failed, falling back to INSERT: {last_error}")
        return await self._bulk_create_fallback(products_data)
    
    async def _bulk_create_fallback(self, products_data: List[Dict]) -> int:
        """
        Fallback bulk create using INSERT (slower but more compatible).
        
        Args:
            products_data: List of product dictionaries
        
        Returns:
            Number of products inserted
        """
        logger.info(f"Using INSERT fallback for {len(products_data)} products...")
        
        products = [
            Product(
                id=p["id"],
                batch_id=p["batch_id"],
                token=p["token"],
                verification_url=p["verification_url"],
                name=p.get("name"),
                category=p.get("category"),
                serial_number=p.get("serial_number"),
                created_at=p["created_at"],
            )
            for p in products_data
        ]
        
        self.session.add_all(products)
        await self.session.flush()
        
        return len(products)
    
    async def get_product(self, product_id: UUID) -> Optional[Product]:
        """Get product by ID."""
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()
    
    async def get_product_by_token(self, token: str) -> Optional[Product]:
        """Get product by token."""
        result = await self.session.execute(
            select(Product).where(Product.token == token)
        )
        return result.scalar_one_or_none()
    
    async def list_products(
        self,
        batch_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Product]:
        """
        List products with pagination.
        
        Args:
            batch_id: Optional filter by batch
            skip: Number of records to skip
            limit: Maximum number of records
        
        Returns:
            List of products
        """
        query = select(Product)
        
        if batch_id:
            query = query.where(Product.batch_id == batch_id)
        
        query = query.offset(skip).limit(limit).order_by(Product.created_at.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def count_products(self, batch_id: Optional[UUID] = None) -> int:
        """Count products, optionally filtered by batch."""
        query = select(func.count(Product.id))
        
        if batch_id:
            query = query.where(Product.batch_id == batch_id)
        
        result = await self.session.execute(query)
        return result.scalar() or 0
    
    async def delete_products_by_batch(self, batch_id: UUID) -> int:
        """
        Delete all products in a batch.
        
        Args:
            batch_id: Batch ID
        
        Returns:
            Number of products deleted
        """
        # Count before delete
        count = await self.count_products(batch_id)
        
        # Delete
        result = await self.session.execute(
            Product.__table__.delete().where(Product.batch_id == batch_id)
        )
        
        return count
