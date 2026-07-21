"""
app/db/seeds/seed_developers.py
Seed the top developers into the master database.
"""
import json
import logging
import uuid
from pathlib import Path

from app.db.models.models import Developer
from app.db.session import SessionLocal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_seed_data() -> list[dict]:
    return [
        {
            "name": "Lodha Group",
            "website": "https://www.lodhagroup.in",
            "city": "Mumbai",
            "state": "Maharashtra",
            "is_verified": True,
            "ranking": 1,
            "inventory_types": ["residential", "commercial", "villa"],
            "projects": [{"name": "Lodha Park", "city": "Mumbai", "status": "complete"}]
        },
        {
            "name": "Godrej Properties",
            "website": "https://www.godrejproperties.com",
            "city": "Mumbai",
            "state": "Maharashtra",
            "is_verified": True,
            "ranking": 2,
            "inventory_types": ["residential", "commercial", "plot"],
            "projects": [{"name": "Godrej Trees", "city": "Mumbai", "status": "complete"}]
        },
        {
            "name": "DLF",
            "website": "https://www.dlf.in",
            "city": "Gurgaon",
            "state": "Haryana",
            "is_verified": True,
            "ranking": 3,
            "inventory_types": ["residential", "commercial"],
            "projects": [{"name": "DLF Cyber City", "city": "Gurgaon", "status": "complete"}]
        },
        {
            "name": "Prestige Group",
            "website": "https://www.prestigeconstructions.com",
            "city": "Bangalore",
            "state": "Karnataka",
            "is_verified": True,
            "ranking": 4,
            "inventory_types": ["residential", "commercial"],
            "projects": [{"name": "Prestige Shantiniketan", "city": "Bangalore", "status": "complete"}]
        },
        {
            "name": "Sobha Limited",
            "website": "https://www.sobha.com",
            "city": "Bangalore",
            "state": "Karnataka",
            "is_verified": True,
            "ranking": 5,
            "inventory_types": ["residential", "villa"],
            "projects": [{"name": "Sobha City", "city": "Bangalore", "status": "ongoing"}]
        }
    ]

def seed_developers():
    db = SessionLocal()
    try:
        data = get_seed_data()
        
        # Check if already seeded
        if db.query(Developer).first():
            logger.info("Developers already seeded, skipping.")
            return

        for dev_data in data:
            developer = Developer(
                id=uuid.uuid4(),
                **dev_data
            )
            db.add(developer)
        
        db.commit()
        logger.info(f"Successfully seeded {len(data)} developers.")
    except Exception as e:
        logger.error(f"Error seeding developers: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Starting Developer seed process...")
    seed_developers()
    logger.info("Done.")
