"""Vòng lặp chạy ngầm: thu thập tin -> quét chất lượng -> chụp chỉ số -> học lại trọng số."""

import asyncio
import logging

from core.config import SCHEDULER_INTERVAL_MINUTES
from core.database import session_factory
from services import ingest_service, matching_service, quality_service

logger = logging.getLogger(__name__)


async def run_pipeline_once() -> None:
    steps = (
        ("thu thập tin", ingest_service.run_ingestion),
        ("quét chất lượng tin", quality_service.scan_all_jobs),
        ("chụp chỉ số chất lượng", quality_service.take_snapshot),
        ("học lại trọng số khớp", matching_service.retrain_weights),
    )
    for name, step in steps:
        async with session_factory() as db:
            try:
                result = await step(db)
                logger.info("Tác vụ %s: %s", name, result.message)
            except Exception:  # một bước lỗi không được làm dừng cả vòng lặp
                logger.exception("Tác vụ %s thất bại", name)


async def scheduler_loop() -> None:
    while True:
        await run_pipeline_once()
        await asyncio.sleep(SCHEDULER_INTERVAL_MINUTES * 60)
