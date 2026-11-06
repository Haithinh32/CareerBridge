# CareerBridge — Hệ thống tìm việc thông minh tích hợp AI và BI

Nền tảng kết nối tuyển dụng cho sinh viên và người mới đi làm. AI phân tích CV, tính điểm
tương thích (Matching Score) có giải thích; BI Dashboard trực quan hóa thị trường lao động.

- **Backend:** FastAPI · SQLModel · PostgreSQL (SQLite khi phát triển) · scikit-learn
- **Frontend:** React 19 · Vite · Ant Design · Recharts
- Báo cáo đồ án: [docs/BaoCao.md](docs/BaoCao.md)
- Kịch bản demo: [docs/KichBanThuyetTrinh.md](docs/KichBanThuyetTrinh.md)

## Chạy bằng Docker (khuyên dùng)

Yêu cầu: Docker Desktop. Chạy PostgreSQL, backend và frontend.

```bash
docker compose up -d --build
docker compose run --rm seed      # tạo dữ liệu mẫu (XÓA dữ liệu cũ)
docker compose restart backend    # bắt buộc sau khi seed lại
```

Giao diện: <http://localhost:5173> · API: <http://localhost:8000/docs>

```bash
docker compose run --rm test      # chạy pytest
docker compose run --rm evaluate  # đánh giá mô hình -> docs/ket_qua_danh_gia.md
docker compose down               # dừng (thêm -v để xóa cả dữ liệu)
```

## Cài đặt thủ công

Yêu cầu: Python 3.11-3.13 (các phiên bản thư viện đang pin chưa hỗ trợ 3.14 trở lên), Node.js 20+.

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # macOS/Linux: cp .env.example .env
python -m scripts.seed            # tạo dữ liệu mẫu (XÓA dữ liệu cũ)
uvicorn main:app --reload         # http://localhost:8000/docs

# Frontend (cửa sổ terminal khác)
cd frontend
npm install
npm run dev                       # http://localhost:5173
```

Dùng PostgreSQL: đặt `DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/careerbridge` trong `backend/.env`.

## Tài khoản demo (mật khẩu `matkhau123`)

| Vai trò | Email |
|---|---|
| Ứng viên | `ungvien@careerbridge.vn` |
| Nhà tuyển dụng | `ntd1@careerbridge.vn` … `ntd12@careerbridge.vn` |
| Nhà trường | `truong1@careerbridge.vn` … `truong5@careerbridge.vn` |
| Quản trị viên | `admin@careerbridge.vn` |

## Kiểm thử và đánh giá

```bash
cd backend
pytest                            # unit test AI + kiểm thử tích hợp API
python -m evaluation.evaluate     # đo trích xuất CV và chất lượng xếp hạng -> docs/ket_qua_danh_gia.md
```

## Cấu trúc

```
backend/
  ai/            Mô hình AI thuần (không phụ thuộc CSDL): cv_parser, skill_extractor, matcher,
                 weight_learner, normalizer, quality_checker, data_quality
  api/           Router HTTP
  services/      Nghiệp vụ (gọi ai/ và CSDL)
  models/        Bảng SQLModel        schemas/   Request/response
  enums/ constants/ exceptions/ security/ utils/ tasks/ (lịch chạy ngầm)
  scripts/       seed dữ liệu mẫu      evaluation/  tập nhãn + script đánh giá
  tests/
frontend/src/
  pages/{auth,jobs,candidate,employer,school,admin,bi}  components/  constants/  config/api.js
docs/            Báo cáo
```

## Tác vụ chạy ngầm

Đặt `ENABLE_SCHEDULER=true` để chạy định kỳ: thu thập tin (feed đối tác + trang cho phép thu thập,
kiểm tra robots.txt) → làm sạch, chuẩn hóa → gắn cờ chất lượng → chụp chỉ số chất lượng → học lại
trọng số khớp từ phản hồi. Quản trị viên cũng có thể chạy từng bước trong trang *Chất lượng dữ liệu*.
