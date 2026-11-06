"""Thu thập tin từ feed đối tác (JSON) và các trang cho phép thu thập (tôn trọng robots.txt).

Định dạng một bản ghi feed (các khóa khác bị bỏ qua):
{"id": "...", "title": "...", "company": "...", "description": "...", "location": "...",
 "salary": "10-15 triệu", "deadline": "2026-12-31", "url": "...", "skills": ["Python", ...],
 "work_type": "full_time"}
Trang web thu thập cần nhúng JSON-LD schema.org/JobPosting - định dạng chuẩn mà nhiều trang
tuyển dụng công khai cho máy tìm kiếm.
"""

import json
import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ai.normalizer import detect_level, normalize_location, parse_salary, parse_years_required
from core.config import CRAWL_SEED_URLS, PARTNER_FEED_URLS
from enums.job import JobLevel, JobSource, WorkType
from models.job import Job, JobSkill
from schemas.analytics import TaskResultResponse
from services import quality_service, skill_service
from utils.time import utcnow

USER_AGENT = "CareerBridgeBot/1.0 (+https://careerbridge.local/bot)"
HTTP_TIMEOUT_SECONDS = 15
MAX_DESCRIPTION_LENGTH = 20_000
_JSON_LD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I
)
_TAG_RE = re.compile(r"<[^>]+>")


@dataclass
class RawJob:
    external_id: str
    title: str
    company_name: str
    description: str
    location: str | None = None
    salary: str | None = None
    deadline: str | None = None
    url: str | None = None
    skills: list[str] | None = None
    work_type: str | None = None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def raw_from_feed_item(item: dict) -> RawJob | None:
    if not item.get("title") or not item.get("id"):
        return None
    return RawJob(
        external_id=str(item["id"]),
        title=str(item["title"]).strip(),
        company_name=str(item.get("company") or "Không rõ").strip(),
        description=str(item.get("description") or ""),
        location=item.get("location"),
        salary=item.get("salary"),
        deadline=item.get("deadline"),
        url=item.get("url"),
        skills=item.get("skills") or [],
        work_type=item.get("work_type"),
    )


def raw_from_json_ld(data: dict, page_url: str) -> RawJob | None:
    if data.get("@type") != "JobPosting":
        return None
    org = data.get("hiringOrganization") or {}
    place = data.get("jobLocation") or {}
    if isinstance(place, list):
        place = place[0] if place else {}
    address = place.get("address") or {}
    salary = data.get("baseSalary") or {}
    value = salary.get("value") or {}
    salary_text = None
    if isinstance(value, dict) and (value.get("minValue") or value.get("maxValue")):
        currency = salary.get("currency", "VND")
        salary_text = f"{value.get('minValue', '')} - {value.get('maxValue', '')} {currency}"
    identifier = data.get("identifier")
    if isinstance(identifier, dict):
        identifier = identifier.get("value")
    return RawJob(
        external_id=str(identifier or page_url),
        title=str(data.get("title", "")).strip(),
        company_name=str(org.get("name") or "Không rõ") if isinstance(org, dict) else str(org),
        description=_TAG_RE.sub(" ", str(data.get("description", "")))[:MAX_DESCRIPTION_LENGTH],
        location=address.get("addressLocality") or address.get("addressRegion"),
        salary=salary_text,
        deadline=data.get("validThrough"),
        url=page_url,
        skills=[s.strip() for s in str(data.get("skills", "")).split(",") if s.strip()],
    )


async def import_raw_jobs(
    db: AsyncSession, raws: list[RawJob], source: JobSource
) -> dict[str, int]:
    """Làm sạch, chuẩn hóa, ánh xạ kỹ năng qua từ điển, rồi chạy kiểm tra chất lượng."""
    dictionary = await skill_service.load_dictionary(db)
    stats = {"created": 0, "updated": 0, "skipped": 0}
    for raw in raws:
        if not raw.title or len(raw.description) < 20:
            stats["skipped"] += 1
            continue
        existing = (
            await db.exec(
                select(Job).where(Job.external_id == raw.external_id, Job.source == source)
            )
        ).first()
        job = existing or Job(
            title=raw.title, description=raw.description, company_name=raw.company_name,
            source=source, external_id=raw.external_id, posted_at=utcnow(),
        )
        job.title, job.description, job.company_name = raw.title, raw.description, raw.company_name
        job.location_raw, job.location = raw.location, normalize_location(raw.location)
        job.salary_raw = raw.salary
        job.salary_min, job.salary_max = parse_salary(raw.salary)
        job.deadline = _parse_date(raw.deadline)
        job.source_url = raw.url
        job.min_years_experience = parse_years_required(raw.description)
        job.level = detect_level(raw.title, raw.description) or JobLevel.JUNIOR
        if raw.work_type in {wt.value for wt in WorkType}:
            job.work_type = WorkType(raw.work_type)
        elif normalize_location(raw.location) == "Từ xa":
            job.work_type = WorkType.REMOTE
        job.updated_at = utcnow()
        db.add(job)
        await db.flush()

        skill_ids = dictionary.extract_ids(" , ".join(raw.skills or []))
        required_ids = skill_ids or dictionary.extract_ids(f"{raw.title}\n{raw.description}")
        for row in (await db.exec(select(JobSkill).where(JobSkill.job_id == job.id))).all():
            await db.delete(row)
        await db.flush()
        for skill_id in required_ids:
            db.add(JobSkill(job_id=job.id, skill_id=skill_id, is_required=True))
        await db.flush()

        await quality_service.evaluate_job(db, job, commit=False)
        stats["updated" if existing else "created"] += 1
    await db.commit()
    return stats


async def ingest_partner_feeds(db: AsyncSession, urls: list[str] | None = None) -> dict[str, int]:
    raws: list[RawJob] = []
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
        for url in urls if urls is not None else PARTNER_FEED_URLS:
            try:
                res = await client.get(url, headers={"User-Agent": USER_AGENT})
                res.raise_for_status()
                payload = res.json()
            except (httpx.HTTPError, json.JSONDecodeError):
                continue
            items = payload.get("jobs", []) if isinstance(payload, dict) else payload
            raws.extend(r for r in (raw_from_feed_item(i) for i in items) if r)
    return await import_raw_jobs(db, raws, JobSource.PARTNER_FEED)


async def _allowed_by_robots(client: httpx.AsyncClient, url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        res = await client.get(robots_url, headers={"User-Agent": USER_AGENT})
    except httpx.HTTPError:
        return False
    if res.status_code == 404:
        return True
    if res.status_code != 200:
        return False
    parser = RobotFileParser()
    parser.parse(res.text.splitlines())
    return parser.can_fetch(USER_AGENT, url)


async def crawl_sites(db: AsyncSession, urls: list[str] | None = None) -> dict[str, int]:
    """Chỉ tải các trang mà robots.txt cho phép; mỗi trang đọc JobPosting trong JSON-LD."""
    raws: list[RawJob] = []
    blocked = 0
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
        for url in urls if urls is not None else CRAWL_SEED_URLS:
            if not await _allowed_by_robots(client, url):
                blocked += 1
                continue
            try:
                res = await client.get(url, headers={"User-Agent": USER_AGENT})
                res.raise_for_status()
            except httpx.HTTPError:
                continue
            for block in _JSON_LD_RE.findall(res.text):
                try:
                    data = json.loads(block)
                except json.JSONDecodeError:
                    continue
                for item in data if isinstance(data, list) else [data]:
                    raw = raw_from_json_ld(item, urljoin(url, item.get("url", "")))
                    if raw:
                        raws.append(raw)
    stats = await import_raw_jobs(db, raws, JobSource.CRAWLER)
    stats["blocked_by_robots"] = blocked
    return stats


async def run_ingestion(db: AsyncSession) -> TaskResultResponse:
    feed = await ingest_partner_feeds(db)
    crawl = await crawl_sites(db)
    return TaskResultResponse(
        message="Đã thu thập tin từ feed đối tác và trang web",
        details={"partner_feed": feed, "crawler": crawl},
    )
