# Kịch bản thuyết trình demo CareerBridge

**Thời lượng:** khoảng 16 phút demo + hỏi đáp. **Phải đi đúng thứ tự:** các con số trong kịch bản phụ thuộc vào thứ tự thao tác.

Mọi bước và con số dưới đây đã được chạy thử trên trình duyệt thật với dữ liệu seed mới. Lời thoại để trong khung trích dẫn, hãy nói theo cách của bạn.

| # | Checklist | Trạng thái | Minh chứng khi demo | Phút |
|---|---|---|---|---|
| 1 | Phân tích yêu cầu, thiết kế CSDL | Hoàn thành | Báo cáo mục 1, 22 bảng trên PostgreSQL | 2 |
| 2 | AI phân tích CV, tính điểm tương thích | Hoàn thành | Tải CV, xác nhận kỹ năng, gợi ý có giải thích | 4 |
| 3 | Dashboard BI | Hoàn thành | Dashboard với admin và nhà tuyển dụng | 3 |
| 4 | Frontend và tích hợp API | Hoàn thành | Luồng ứng tuyển, từ chối, thu hồi quyền | 3 |
| 5 | Kiểm thử và báo cáo đánh giá | Hoàn thành | 51 test, bảng đánh giá, học lại trọng số | 4 |

---

## Chuẩn bị trước giờ thuyết trình

**1. Khởi động và đưa dữ liệu về trạng thái sạch** (làm ngay trước khi lên, Docker Desktop phải đang chạy):

```powershell
cd C:\Users\haith\Downloads\CareerBridge
docker compose up -d --build
docker compose run --rm seed
docker compose restart backend
```

> **Bắt buộc phải có lệnh `restart backend` sau `seed`.** Nếu thiếu, lần đăng nhập đầu tiên sẽ báo lỗi 500.

Kiểm tra: mở <http://localhost:5173/api/health>, phải thấy `{"status":"ok"}`.

**2. Mở sẵn 3 trình duyệt riêng** (cùng một trình duyệt sẽ dùng chung phiên đăng nhập, nên phải tách):

| Cửa sổ | Tài khoản (mật khẩu `matkhau123`) | Trang mở sẵn |
|---|---|---|
| A: Chrome thường | `ungvien@careerbridge.vn` | `/ho-so` |
| B: Chrome ẩn danh | `ntd7@careerbridge.vn` | `/nha-tuyen-dung/tin` |
| C: Edge | `admin@careerbridge.vn` | `/bi` |

**3. Mở sẵn trên máy:** terminal ở thư mục dự án; file `docs/BaoCao.md`; file `docs/ket_qua_danh_gia.md`; thư mục `docs/demo/` để kéo CV mẫu.

> Sơ đồ ERD trong báo cáo dùng Mermaid: xem trên GitHub, hoặc cài extension "Markdown Preview Mermaid Support" cho VS Code. Nhớ kiểm tra trước.

**4. Dự phòng:** ảnh chụp từng màn hình nằm trong `docs/demo/screenshots/`. Nếu bước nào lỗi, mở ảnh tương ứng và nói tiếp, đừng dừng lại để sửa.

### Mở đầu (30 giây)

> Sinh viên mới ra trường thường không biết mình hợp việc nào và còn thiếu gì; nhà tuyển dụng lại phải đọc thủ công rất nhiều CV. CareerBridge dùng AI đọc CV, tính điểm phù hợp có giải thích, và dùng BI để trực quan hóa thị trường lao động.
>
> Em nói trước một điều quan trọng: **dữ liệu demo là dữ liệu mô phỏng**, gồm 181 ứng viên và 224 tin do script sinh ra. Vì vậy các con số chứng minh hệ thống hoạt động đúng, chứ không phải kết luận về thị trường thật.

---

## Checklist 1: Phân tích yêu cầu và thiết kế CSDL (2 phút)

**Thông điệp:** thiết kế xuất phát từ nhu cầu của 4 nhóm người dùng, và các quy tắc nghiệp vụ được bảo vệ ngay ở tầng dữ liệu.

| # | Thao tác | Lời thoại | Kết quả phải thấy |
|---|---|---|---|
| 1 | Mở `docs/BaoCao.md`, mục 1.1-1.2 | "Hệ thống có 4 tác nhân: ứng viên, nhà tuyển dụng, nhà trường, quản trị viên. Từ đó em rút ra 11 yêu cầu chức năng." | Bảng tác nhân, bảng FR |
| 2 | Cuộn tới ERD, mục 1.4 | "Ba thực thể trung tâm là hồ sơ ứng viên, tin tuyển dụng và kỹ năng. Kỹ năng tách thành bảng riêng, có bảng từ đồng nghĩa, nên 'ReactJS' và 'React.js' đều quy về một kỹ năng; nhờ vậy cả so khớp lẫn thống kê BI mới chính xác." | Sơ đồ ERD |
| 3 | Chạy lệnh 1 bên dưới | "Thiết kế này đang chạy thật trên PostgreSQL với 22 bảng." | `(22 rows)` |
| 4 | Chạy lệnh 2 | "Dữ liệu mẫu đủ lớn để demo." | 199 / 181 / 12 / 224 / 68 / 495 |
| 5 | Chạy lệnh 3 | "Ràng buộc này chặn một ứng viên nộp trùng vào một tin, ngay cả khi hai request đến cùng lúc." | `UNIQUE (job_id, candidate_id)` |
| 6 | Mở `/dang-ky` ở cửa sổ **chưa đăng nhập**, chọn *Nhà tuyển dụng*, điền đủ, mã số thuế `0100101079`, bấm Đăng ký | "Mã này đúng 10 chữ số nhưng sai chữ số kiểm tra, nên hệ thống từ chối. Đây là cách lọc doanh nghiệp không có thật ngay từ đầu." | Thông báo *Mã số thuế không hợp lệ* |

```powershell
# Lệnh 1
docker compose exec db psql -U careerbridge -d careerbridge -c "\dt"
# Lệnh 2
docker compose exec db psql -U careerbridge -d careerbridge -c "select (select count(*) from users) users, (select count(*) from candidate_profiles) ung_vien, (select count(*) from companies) doanh_nghiep, (select count(*) from jobs) tin, (select count(*) from skills) ky_nang, (select count(*) from applications) ung_tuyen;"
# Lệnh 3
docker compose exec db psql -U careerbridge -d careerbridge -c "select pg_get_constraintdef(oid) from pg_constraint where conrelid='applications'::regclass and contype='u';"
```

**Câu hỏi có thể gặp**

- *Vì sao lịch sử trạng thái lưu JSON?* Mỗi hồ sơ có ít bước và luôn đọc cùng lúc. Lưu lịch sử giúp phễu vẫn tính được hồ sơ từng phỏng vấn rồi mới bị từ chối.
- *Có migration không?* Chưa, hiện tạo bảng bằng `create_all`. Trước khi triển khai thật cần thêm Alembic (đã ghi ở mục hạn chế của báo cáo).

**Dự phòng:** `00_dang_ky_sai_mst.png`

---

## Checklist 2: AI phân tích CV và tính điểm tương thích (4 phút)

**Thông điệp:** AI đề xuất, con người xác nhận, và mọi điểm số đều giải thích được.

*Cửa sổ A: ứng viên Nguyễn Minh An.*

| # | Thao tác | Lời thoại | Kết quả phải thấy |
|---|---|---|---|
| 1 | Vào **Hồ sơ & CV**, kéo `docs/demo/CV_mau_Nguyen_Minh_An.docx` vào ô tải lên | "Em tải một CV thật, hệ thống hỗ trợ cả DOCX và PDF." | *AI đã trích 9 kỹ năng* |
| 2 | Chỉ vào *Kết quả phân tích* | "AI tách được 9 kỹ năng, kinh nghiệm 1 năm, học vấn và GPA 3.4, và 2 dự án kèm công nghệ của từng dự án." | Docker, Python, REST API, Tiếng Anh, FastAPI, Git, PostgreSQL, React, SQL |
| 3 | Chỉ vào dòng học vấn | "Một chi tiết thú vị: CV ghi ngành *Khoa học máy tính*. Khi bỏ dấu, cụm này chứa 'hoc may', nên phiên bản đầu đã gán nhầm kỹ năng Machine Learning. Em phát hiện lỗi này khi kiểm thử và đã sửa; giờ kết quả không còn Machine Learning." | Không có tag Machine Learning |
| 4 | Cuộn tới **Xác nhận kỹ năng**, chỉ các dòng *Chưa xác nhận* | "AI không tự quyết định. Kỹ năng trích ra phải được ứng viên xác nhận thì mới dùng để tính điểm." | 5 dòng *Chưa xác nhận* |
| 5 | Xóa dòng **TensorFlow**, bấm **Lưu & xác nhận** | "TensorFlow có sẵn trong hồ sơ cũ nhưng CV này không nhắc tới, nên em xóa đi." | *Đã lưu danh sách kỹ năng* |
| 6 | Vào **Gợi ý việc làm** | "Đây là các tin được xếp theo điểm phù hợp." | 65%, 52%, 52%, 51%, 42% |
| 7 | Ở tin đầu tiên, bấm nút **Phù hợp** (ngón tay cái) | "Phản hồi này sẽ thành dữ liệu huấn luyện, em sẽ quay lại ở phần cuối." | *Cảm ơn phản hồi của bạn* |
| 8 | Bấm **Xem chi tiết** ở tin *Thực tập sinh Lập trình viên Python Backend* | Xem lời thoại bên dưới | Điểm 65%, 6 thanh đặc trưng |
| 9 | Vào **Thiếu hụt kỹ năng** | "Từ 10 tin Backend Developer, mức sẵn sàng của An là 34%. Hệ thống chỉ ra cần học gì, ví dụ TypeScript có 40% tin yêu cầu, kèm khóa học miễn phí." | 34%, danh sách kỹ năng và khóa học |

**Lời thoại bước 8, đây là điểm nhấn của phần này:**

> Điểm này không phải hộp đen, có thể tính tay ngay trên màn hình. Kỹ năng đạt 100% nhân trọng số 45%; kinh nghiệm 100% nhân 15%; nội dung CV 17% nhân 15%; vị trí mục tiêu 25% nhân 10%; địa điểm và hình thức bằng 0. Tổng lại đúng khoảng 65%.
>
> Hệ thống cũng nói thẳng điểm chưa hợp: "Khác địa điểm: tin ở Hà Nội", vì An muốn làm ở TP.HCM.

**Nên chủ động nói trước** (đừng đợi hội đồng hỏi):

> Tin hạng 3 là Java, An chỉ có 1/3 kỹ năng bắt buộc mà vẫn đạt 52%, vì tin đó làm từ xa, khớp địa điểm và hình thức. Hạng 2 là tin Senior yêu cầu 4 năm kinh nghiệm. Đây là những hạn chế thật của công thức hiện tại, em đã ghi trong báo cáo.

**Câu hỏi có thể gặp**

- *Đây có phải Machine Learning không?* Có hai phần học máy: biểu diễn TF-IDF cho độ tương đồng văn bản và hồi quy logistic để học trọng số. Trích kỹ năng thì dựa trên từ điển, không phải NER, vì dễ giải thích và không cần dữ liệu gán nhãn lớn.
- *Kỹ năng ngoài từ điển thì sao?* Không nhận ra được, ví dụ "Firebase". Quản trị viên có thể bổ sung từ điển.
- *CV dạng ảnh scan?* Chưa đọc được, cần thêm OCR.
- *Vì sao không dùng LLM?* Em ưu tiên kết quả ổn định, giải thích được, chạy không tốn chi phí gọi API. LLM là một hướng mở rộng cho trích xuất, nhưng em chưa thử nghiệm.

**Dự phòng:** `02_ket_qua_cv.png`, `03_goi_y.png`, `04_chi_tiet_tin.png`, `06_thieu_hut.png`

---

## Checklist 3: Dashboard BI (3 phút)

**Thông điệp:** dashboard có đủ 3 nhóm chỉ số yêu cầu, và số liệu được phân quyền theo vai trò.

*Cửa sổ C: admin, trang `/bi`.*

| # | Thao tác | Lời thoại | Kết quả phải thấy |
|---|---|---|---|
| 1 | Chỉ hàng thẻ trên cùng | "Tổng quan toàn hệ thống." | 181 ứng viên, 67 tin mở, 495 ứng tuyển, 12 doanh nghiệp, lương TB 20.53 tr, trúng tuyển 10.9% |
| 2 | Biểu đồ **Số lượng ứng viên theo kỹ năng** | "Chỉ số thứ nhất. Git nhiều nhất với 82 ứng viên, tiếp theo là các kỹ năng mềm; SQL là kỹ năng chuyên môn cao nhất với 48." | Git 82, SQL 48 |
| 3 | Biểu đồ **Xu hướng lương**, chọn *Python* ở ô lọc | "Chỉ số thứ hai. Có thể lọc theo kỹ năng: từ 224 tin còn 55 tin có Python, và đường lương vẽ lại theo đúng nhóm đó." | Biểu đồ đổi, các tháng ít tin hơn |
| 4 | Biểu đồ **Tỷ lệ chuyển đổi**, bấm **Bảng** | "Chỉ số thứ ba. 495 hồ sơ, 391 được xem, 143 phỏng vấn, 54 trúng tuyển, tức 10.9%. Hồ sơ bị từ chối sau phỏng vấn vẫn được tính vào bước phỏng vấn, nên phễu phản ánh đúng bước xa nhất đã đạt." | 79.0% → 36.6% → 37.8% |
| 5 | Biểu đồ **Cung - cầu kỹ năng** | "So sánh % tin yêu cầu với % ứng viên có. Git thì cung 45%, cầu 16%; còn CI/CD thì cầu cao hơn cung. Nhà trường có thể dùng chính dữ liệu này." | Cột Git cam dài vượt trội |
| 6 | Cửa sổ B (`ntd7`), vào **BI Dashboard** | "Cùng dashboard, nhưng phễu và tỷ lệ trúng tuyển của nhà tuyển dụng chỉ tính tin của doanh nghiệp họ." | Ghi chú phạm vi, số khác cửa sổ C |
| 7 | Cửa sổ A (ứng viên), gõ `/bi` | "Ứng viên không có quyền vào trang này." | *Không có quyền truy cập trang này* |

> **Không được nói** "lương đang tăng" hay "thị trường đang thiếu CI/CD". Đây là dữ liệu mô phỏng và đường lương dao động mạnh. Hãy nói "hệ thống tính và hiển thị được", không rút ra kết luận thị trường.

**Câu hỏi có thể gặp**

- *Vì sao tự xây thay vì Power BI?* Để nhúng trực tiếp vào hệ thống, áp dụng phân quyền theo vai trò, và dùng chung API.
- *Dữ liệu lớn có chậm không?* Hiện gom nhóm bằng Python để chạy giống nhau trên SQLite và PostgreSQL. Với khối lượng lớn nên chuyển sang view hoặc materialized view; em chưa đo tải.
- *Vì sao kỹ năng mềm đứng đầu?* Do cách sinh dữ liệu mẫu, mỗi ứng viên được gán thêm vài kỹ năng mềm.

**Dự phòng:** `16_bi_admin.png`, `16b_bi_bang.png`, `17_bi_loc_python.png`, `13_bi_ntd.png`

---

## Checklist 4: Giao diện và tích hợp API AI/BI (3 phút)

**Thông điệp:** một luồng đi xuyên hai vai trò, giao diện, API, AI và CSDL khớp với nhau.

| # | Cửa sổ | Thao tác | Lời thoại | Kết quả phải thấy |
|---|---|---|---|---|
| 1 | A | Quay lại tin vừa xem (**Gợi ý** → *Xem chi tiết* tin đầu), bấm **Ứng tuyển** → **Nộp hồ sơ** | "Hộp thoại nói rõ doanh nghiệp được xem hồ sơ trong phạm vi vị trí này." | *Đã nộp hồ sơ* |
| 2 | A | Vào **Hồ sơ đã nộp** | "Điểm được lưu lại tại thời điểm nộp." | 65%, *Đã nộp* |
| 3 | B | Mở `/nha-tuyen-dung/tin/45/ung-vien`, chọn lọc **Đã ứng tuyển** | "Phía nhà tuyển dụng, AI xếp hạng ứng viên cho tin này. An đứng đầu trong 5 hồ sơ." | An hạng 1, 64%, rồi 59%, 58%, 53%, 31% |
| 4 | B | Bấm mũi tên mở rộng dòng của An | "Nhà tuyển dụng cũng thấy lý do xếp hạng, không chỉ con số." | Kỹ năng khớp, lý do |
| 5 | B | Bấm **Xem hồ sơ**, rồi quay lại | "Khi hồ sơ được mở, trạng thái tự chuyển và ứng viên biết điều đó." | Trạng thái thành *Đã xem* |
| 6 | B | Rê chuột vào **Cập nhật** → **Từ chối** | "Em từ chối ứng viên. Theo nguyên tắc bảo vệ dữ liệu, doanh nghiệp phải mất quyền xem." | *Đã chuyển sang "Từ chối"* |
| 7 | B | Bấm **Xem hồ sơ** lại ở dòng của An | "Giờ không xem được nữa." | *Không thể xem hồ sơ* |
| 8 | A | Vào **Quyền riêng tư** | "Ứng viên thấy minh bạch ai có quyền và vì sao bị thu hồi." | *Đã thu hồi - Doanh nghiệp đã từ chối hồ sơ* |
| 9 | A | Tắt **Phân tích CV tự động**, vào **Hồ sơ & CV**, tải lại CV | "Đồng ý tách theo từng mục đích. Rút đồng ý thì AI không được xử lý CV nữa, chặn ở backend chứ không chỉ ở giao diện." | Cảnh báo *Bạn cần bật...* |
| 10 | A | **Bật lại** công tắc đó | | *Đã đồng ý* |
| 11 | Bất kỳ | Mở <http://localhost:8000/docs> | "Toàn bộ API có tài liệu tự sinh; frontend chỉ gọi qua các endpoint này." | Swagger UI |

**Câu hỏi có thể gặp**

- *Vì sao ở đây 64% mà phía ứng viên 65%?* TF-IDF được tính trên tập văn bản của từng lần xếp hạng: một bên so với tất cả tin, một bên so với tất cả ứng viên. Vì vậy đặc trưng nội dung lệch nhẹ. Thứ tự trong mỗi danh sách vẫn nhất quán; đây là đánh đổi của thiết kế hiện tại.
- *Doanh nghiệp còn xem được An qua tin khác không?* Có, nếu An bật "cho phép tìm thấy" và doanh nghiệp có tin đang mở khác, vì thu hồi theo phạm vi vị trí. Có nên chặn toàn doanh nghiệp hay không là quyết định nghiệp vụ, em đã ghi trong báo cáo.
- *Vì sao trường và ngành của An không khớp CV?* Hồ sơ demo được seed sẵn thông tin ngẫu nhiên ("Kế toán"), còn CV chỉ cập nhật kỹ năng và kinh nghiệm, không ghi đè thông tin ứng viên đã khai.
- *Có dùng được trên điện thoại không?* Có, giao diện responsive; em đã kiểm tra màn hình 390px không bị tràn ngang.

**Dự phòng:** `05_ung_tuyen.png`, `10b_xep_hang_tin_demo.png`, `11_xep_hang_giai_thich.png`, `10d_thu_hoi_quyen.png`, `10e_ung_vien_thay_thu_hoi.png`, `07b_chan_consent.png`

---

## Checklist 5: Kiểm thử và báo cáo đánh giá mô hình (4 phút)

**Thông điệp:** đây là phần cần trung thực nhất. Mô hình vượt xa ngẫu nhiên, nhưng chưa chứng minh được hơn baseline kỹ năng.

| # | Thao tác | Lời thoại | Kết quả phải thấy |
|---|---|---|---|
| 1 | Terminal: `docker compose run --rm test` | "51 test unit và tích hợp API. Ngoài ra em chạy Playwright trên trình duyệt thật, đi qua cả 4 vai trò: 45/45 bước đạt, không có lỗi JavaScript." | `51 passed` |
| 2 | Mở `docs/BaoCao.md`, bảng lỗi ở mục 5.1 | "Điều đáng nói là kiểm thử đầu-cuối tìm ra những lỗi mà unit test bỏ sót: gán nhầm Machine Learning, bộ lọc kỹ năng không có tác dụng, và doanh nghiệp lấy lại được quyền xem sau khi đã từ chối. Tất cả đã sửa." | Bảng lỗi |
| 3 | Mở `docs/ket_qua_danh_gia.md`, phần 1 | "Trích kỹ năng đạt F1 0,99 trên 10 CV. Nhưng em không xem đây là con số thực tế, vì chính tập này đã không phát hiện được lỗi Khoa học máy tính." | P 1,000 / R 0,981 / F1 0,990 |
| 4 | Phần 2, bảng xếp hạng | Xem lời thoại bên dưới | Bảng 5 phương pháp |
| 5 | Cửa sổ C: **Chất lượng dữ liệu** → **Học lại trọng số** | "Hồi quy logistic học từ 829 phản hồi được phép sử dụng, trọng số chuyển sang phiên bản 1: kỹ năng giảm từ 45% xuống 36,6%, nội dung CV tăng từ 15% lên 26,1%." | *Trọng số · v1*, AUC 0.8898 |
| 6 | Cửa sổ A: **Gợi ý việc làm**, tải lại trang | "Xếp hạng thay đổi ngay: tin Java thiếu 2 kỹ năng bắt buộc tụt từ hạng 3 xuống 4, điểm từ 52% còn 36%. Thay đổi hợp lý, nhưng em đo lại thì NDCG@5 là 0,960, **không cải thiện**. AUC 0,89 cũng chỉ đo trên phản hồi mô phỏng." | 56%, 48%, 41%, 36%, 36% |

**Lời thoại bước 4, nói chậm phần này:**

> So với ngẫu nhiên, mô hình lai cải thiện rõ rệt: NDCG@5 đạt 0,962 so với 0,234, và hạng 1 luôn đúng trên cả 10 CV.
>
> Nhưng em muốn nói thẳng: **mô hình lai không thắng baseline chỉ dùng kỹ năng**, 0,962 so với 0,974. So từng CV với Jaccard thì thắng 1, hòa 6, thua 3; kiểm định dấu cho p khoảng 0,63, nên với 10 CV không thể kết luận bên nào tốt hơn.
>
> Nguyên nhân có thể là tập đánh giá quá dễ: mỗi tin thuộc một ngành rõ ràng nên chỉ kỹ năng đã đủ, trong khi địa điểm có thể đẩy tin khác ngành lên trên.
>
> Vậy em vẫn chọn mô hình lai vì lý do gì? Vì nó giải thích được theo nhiều tiêu chí và phản ánh mong muốn của người dùng như địa điểm, hình thức làm việc. Đây là lợi ích về trải nghiệm mà tập đánh giá này không đo được, và em chưa có dữ liệu người dùng thật để chứng minh. Bước tiếp theo là mở rộng tập đánh giá và thử nghiệm với sinh viên thật.

**Nếu còn thời gian (1 phút), cửa sổ C:**

- **Tin cách ly:** "Hệ thống tự cách ly 19 tin: nghi lừa đảo, thiếu thông tin, tin trùng." Tin trùng nhiều (16 cờ) vì dữ liệu mẫu sinh từ khuôn mẫu.
- **Chất lượng dữ liệu:** cảnh báo "Độ tươi mới tụt từ 45% xuống 21%". Nói rõ: lịch sử 10 ngày trước là mô phỏng để minh họa cơ chế cảnh báo.

**Câu hỏi có thể gặp**

- *Sao không chỉnh trọng số để Hybrid thắng?* Chỉnh theo chính tập kiểm thử sẽ làm số đẹp nhưng vô nghĩa. Muốn tối ưu cần một tập kiểm định riêng.
- *Con số có từng bị chỉnh không?* Có một lần sửa phương pháp. Script ban đầu khi hòa điểm giữ tin id nhỏ lên trước, làm baseline được lợi ngẫu nhiên (Jaccard từ 0,986 xuống 0,968 sau khi sửa). Em lấy trung bình trên 200 thứ tự xáo trộn và công khai cả hai con số. Kết luận không đổi.
- *Vì sao P@3 chỉ 0,5?* Trung bình mỗi CV có 2 tin phù hợp, nên P@3 tối đa chỉ 0,667.
- *Ai gán nhãn?* Do người làm đồ án tự gán, đây là một nguồn thiên lệch. Cần nhiều người gán độc lập.
- *Trọng số mới có được kiểm tra trước khi áp dụng không?* Chưa, hiện có hiệu lực ngay. Hướng cải tiến là chỉ kích hoạt khi chỉ số trên tập kiểm định không giảm.

**Dự phòng:** `19_chat_luong.png`, `20_trong_so_moi.png`, `03b_goi_y_sau_hoc_lai.png`, `18_cach_ly.png`

### Kết luận (30 giây)

> CareerBridge đã hoàn thành đầu-cuối: từ CSDL, AI đọc CV và tính điểm có giải thích, dashboard BI, đến giao diện cho 4 vai trò. Về hiệu quả, mô hình vượt xa ngẫu nhiên nhưng chưa chứng minh được hơn baseline kỹ năng. Vì vậy ưu tiên tiếp theo của em không phải thêm thuật toán, mà là dữ liệu đánh giá tốt hơn và thử nghiệm với người dùng thật.

---

## Xử lý sự cố khi demo

| Hiện tượng | Xử lý nhanh |
|---|---|
| Đăng nhập báo lỗi 500 | `docker compose restart backend` |
| Con số lệch kịch bản, hoặc An đã ứng tuyển rồi | Đã có thao tác cũ. Chạy lại: `docker compose run --rm seed; docker compose restart backend`, rồi đăng nhập lại cả 3 cửa sổ |
| Cổng 5432, 8000 hoặc 5173 đang bận | Tắt chương trình dùng cổng đó, hoặc đổi cổng trong `docker-compose.yml` |
| `docker` báo không kết nối được | Mở Docker Desktop, đợi khởi động xong |
| Xếp hạng khác kịch bản | Có thể đã học lại trọng số trước đó; chạy seed lại như trên |
| Bất kỳ lỗi nào khác khi đang trình bày | Mở ảnh trong `docs/demo/screenshots/`, nói tiếp, xử lý sau |

Dữ liệu seed cố định nên các điểm số lặp lại được. Riêng ngày tháng và các số phụ thuộc thời gian (như độ tươi mới, số tin theo tháng) có thể đổi nhẹ theo ngày chạy seed.
