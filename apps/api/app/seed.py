from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product

CATEGORIES = (
    "Electronics",
    "Home & Kitchen",
    "Office",
    "Outdoors",
    "Fitness",
    "Accessories",
    "Books",
    "Games",
)
ADJECTIVES = (
    "Essential",
    "Premium",
    "Compact",
    "Smart",
    "Classic",
    "Ergonomic",
    "Portable",
    "Modern",
)
NOUNS = (
    "Desk Lamp",
    "Travel Pack",
    "Wireless Hub",
    "Storage Set",
    "Water Bottle",
    "Notebook",
    "Speaker",
    "Organizer",
)


async def seed_products(session: AsyncSession, count: int = 1000) -> int:
    """Seed a fresh catalog. Existing catalogs are left untouched."""
    existing = await session.scalar(select(func.count(Product.id)))
    if existing:
        return 0

    products = []
    for index in range(1, count + 1):
        category = CATEGORIES[(index - 1) % len(CATEGORIES)]
        adjective = ADJECTIVES[(index * 3) % len(ADJECTIVES)]
        noun = NOUNS[(index * 5) % len(NOUNS)]
        price = Decimal(799 + ((index * 137) % 49200)) / 100
        products.append(
            Product(
                sku=f"PRD-{index:05d}",
                name=f"{adjective} {noun} {index}",
                description=(
                    f"Mock {category.lower()} product {index} "
                    "for development and testing."
                ),
                category=category,
                price=price,
                stock=(index * 17) % 501,
                is_active=index % 13 != 0,
            )
        )
    session.add_all(products)
    await session.commit()
    return len(products)
