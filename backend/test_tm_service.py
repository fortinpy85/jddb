"""Test translation memory service directly"""

import traceback
import asyncio
from jd_ingestion.services.translation_memory_service import TranslationMemoryService
from jd_ingestion.database.connection import get_async_session


async def test():
    async for db in get_async_session():
        try:
            svc = TranslationMemoryService()
            result = await svc.create_project(
                name="Direct Test",
                source_language="en",
                target_language="fr",
                description="Testing directly",
                db=db,
            )
            print("Success:", result)
            break
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
            break


if __name__ == "__main__":
    asyncio.run(test())
