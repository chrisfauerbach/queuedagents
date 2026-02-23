import json
import logging
from pathlib import Path

from sqlalchemy import func, select

from shared.database import async_session
from shared.models import Prompt

logger = logging.getLogger(__name__)

SEED_FILE = Path(__file__).parent / "seed_prompts.json"


async def seed_prompts() -> None:
    async with async_session() as session:
        count = await session.scalar(select(func.count()).select_from(Prompt))
        if count > 0:
            logger.info("Prompts table has %d rows, skipping seed", count)
            return

        data = json.loads(SEED_FILE.read_text())
        for item in data:
            session.add(Prompt(
                name=item["name"],
                prompt=item["prompt"],
                system_prompt=item.get("system_prompt"),
                temperature=item.get("temperature", 0.7),
                max_tokens=item.get("max_tokens", 2048),
            ))
        await session.commit()
        logger.info("Seeded %d prompts from %s", len(data), SEED_FILE.name)
