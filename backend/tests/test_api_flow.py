"""Kiểm thử tích hợp luồng chính qua HTTP, gồm thu hồi quyền xem hồ sơ (Điều 25)."""

import io
from collections.abc import AsyncIterator
from datetime import timedelta

import docx
import pytest
from httpx import ASGITransport, AsyncClient

from core.database import drop_db, engine, init_db, session_factory
from main import app
from models.skill import Skill, SkillAlias
from services import skill_service
from utils.time import today

PASSWORD = "matkhau123"
VALID_TAX_CODE = "0100101072"


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    await drop_db()
    await init_db()
    skill_service.invalidate_dictionary()
    async with session_factory() as db:
        for name, aliases in [("Python", ["py"]), ("SQL", []), ("Docker", []), ("React", [])]:
            skill = Skill(name=name, category="IT")
            db.add(skill)
            await db.flush()
            for alias in aliases:
                db.add(SkillAlias(skill_id=skill.id, alias=alias))
        await db.commit()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    # Mỗi test có event loop riêng: đóng pool để kết nối không bị dùng lại sang loop khác
    await engine.dispose()


async def _register(client: AsyncClient, **payload: str) -> dict[str, str]:
    res = await client.post("/api/auth/dang-ky", json={"password": PASSWORD, **payload})
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _docx_bytes(text: str) -> bytes:
    document = docx.Document()
    for line in text.splitlines():
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


async def test_full_flow(client: AsyncClient) -> None:
    employer = await _register(
        client, email="hr@a.vn", full_name="HR", role="employer",
        company_name="Công ty A", tax_code=VALID_TAX_CODE,
    )
    candidate = await _register(client, email="sv@a.vn", full_name="Sinh viên", role="candidate")
    skills = {s["name"]: s["id"] for s in (await client.get("/api/ky-nang")).json()["items"]}

    # Đăng tin
    res = await client.post("/api/tin-tuyen-dung", headers=employer, json={
        "title": "Backend Developer Python",
        "description": "Phát triển REST API bằng Python, tối ưu truy vấn SQL, đóng gói Docker. "
                       "Làm việc cùng đội sản phẩm trong môi trường Agile.",
        "location": "TP.HCM", "salary_min": 15_000_000, "salary_max": 25_000_000,
        "deadline": (today() + timedelta(days=30)).isoformat(),
        "skills": [{"skill_id": skills["Python"], "is_required": True},
                   {"skill_id": skills["SQL"], "is_required": True},
                   {"skill_id": skills["Docker"], "is_required": False}],
    })
    assert res.status_code == 201, res.text
    job = res.json()
    assert job["status"] == "open"
    assert job["location"] == "Hồ Chí Minh"

    # Phân tích CV cần đồng ý trước
    cv = _docx_bytes("KỸ NĂNG\nPy, SQL, React\nDỰ ÁN\nWeb bán hàng\n- Dùng React và SQL")
    files = {"file": ("cv.docx", cv, "application/octet-stream")}
    res = await client.post("/api/ung-vien/tai-lieu", headers=candidate, files=files)
    assert res.status_code == 403
    assert res.json()["code"] == "CONSENT_REQUIRED"

    for purpose in ("cv_analysis", "job_recommendation"):
        res = await client.put(f"/api/quyen-rieng-tu/dong-y/{purpose}", headers=candidate,
                               json={"is_granted": True})
        assert res.status_code == 200
    res = await client.post("/api/ung-vien/tai-lieu", headers=candidate, files=files)
    assert res.status_code == 201, res.text
    extracted = {s["name"] for s in res.json()["extracted_skills"]}
    assert extracted == {"Python", "SQL", "React"}

    # Xác nhận kỹ năng (bỏ React), rồi xem gợi ý kèm giải thích
    res = await client.put("/api/ung-vien/ky-nang", headers=candidate, json={
        "skills": [{"skill_id": skills["Python"]}, {"skill_id": skills["SQL"]}],
    })
    assert {s["name"] for s in res.json()["skills"]} == {"Python", "SQL"}
    res = await client.get("/api/goi-y/viec-lam", headers=candidate)
    rec = res.json()["items"][0]
    assert rec["job"]["id"] == job["id"]
    assert [s["name"] for s in rec["match"]["missing_optional_skills"]] == ["Docker"]
    assert rec["match"]["missing_required_skills"] == []

    # Ứng tuyển -> doanh nghiệp xem được hồ sơ
    res = await client.post(f"/api/tin-tuyen-dung/{job['id']}/ung-tuyen", headers=candidate,
                            json={})
    assert res.status_code == 201
    application = res.json()
    res = await client.post(f"/api/tin-tuyen-dung/{job['id']}/ung-tuyen", headers=candidate,
                            json={})
    assert res.status_code == 409

    res = await client.get(f"/api/tin-tuyen-dung/{job['id']}/xep-hang-ung-vien", headers=employer)
    assert res.json()["items"][0]["is_applicant"] is True
    candidate_id = application["candidate_id"]
    res = await client.get(f"/api/ho-so-ung-vien/{candidate_id}", headers=employer)
    assert res.status_code == 200
    res = await client.get("/api/ung-vien/ung-tuyen", headers=candidate)
    assert res.json()["items"][0]["status"] == "viewed"

    # Từ chối -> tự động mất quyền xem hồ sơ
    res = await client.patch(f"/api/ung-tuyen/{application['id']}/trang-thai", headers=employer,
                             json={"status": "rejected"})
    assert res.status_code == 200
    res = await client.get(f"/api/ho-so-ung-vien/{candidate_id}", headers=employer)
    assert res.status_code == 403
    assert res.json()["code"] == "PROFILE_ACCESS_REVOKED"
    grants = (await client.get("/api/quyen-rieng-tu/quyen-truy-cap", headers=candidate)).json()
    assert grants["items"][0]["revoke_reason"] == "candidate_rejected"

    # Phễu chuyển đổi của doanh nghiệp
    funnel = (await client.get("/api/bi/ty-le-chuyen-doi", headers=employer)).json()["items"]
    assert [stage["count"] for stage in funnel] == [1, 1, 0, 0]


async def test_role_and_input_checks(client: AsyncClient) -> None:
    res = await client.post("/api/auth/dang-ky", json={
        "email": "x@a.vn", "password": PASSWORD, "full_name": "X", "role": "employer",
        "company_name": "B", "tax_code": "0100101079",
    })
    assert res.status_code == 400
    candidate = await _register(client, email="sv2@a.vn", full_name="SV", role="candidate")
    assert (await client.get("/api/quan-tri/tin-cach-ly", headers=candidate)).status_code == 403
    assert (await client.get("/api/ung-vien/ho-so")).status_code == 401
