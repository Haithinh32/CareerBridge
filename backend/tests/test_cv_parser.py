from ai.cv_parser import estimate_years_experience, parse_cv, split_sections
from ai.skill_extractor import SkillDictionary, SkillEntry

SAMPLE_CV = """Nguyễn Văn A
Email: nguyenvana@gmail.com | SĐT: 0912 345 678

MỤC TIÊU
Trở thành kỹ sư Machine Learning.

HỌC VẤN
Trường Đại học Bách khoa Hà Nội - Kỹ sư Khoa học máy tính (2020 - 2025)
GPA: 3.45/4

KINH NGHIỆM LÀM VIỆC
Thực tập sinh AI tại Công ty X (06/2024 - 12/2024)
- Xây dựng mô hình học máy dự đoán churn bằng Python

DỰ ÁN
Hệ thống gợi ý việc làm
- Backend Node.js, frontend ReactJS, triển khai bằng Docker
Chatbot tư vấn tuyển sinh
- Dùng Python và ML

KỸ NĂNG
Python, SQL, JS, Tiếng Anh (IELTS 7.0)
"""


def test_skill_extraction_uses_aliases(dictionary: SkillDictionary) -> None:
    found = {s.name for s in dictionary.extract(SAMPLE_CV)}
    assert {"Python", "SQL", "JavaScript", "React", "Node.js", "Docker",
            "Machine Learning", "Tiếng Anh"} <= found


def test_longer_term_wins(dictionary: SkillDictionary) -> None:
    found = {s.name for s in dictionary.extract("Kinh nghiệm React Native 1 năm")}
    assert found == {"React Native"}


def test_no_false_positive_inside_words(dictionary: SkillDictionary) -> None:
    # 'ml' không được khớp trong 'html', 'js' không khớp trong 'json'
    assert dictionary.extract("Viết HTML và đọc file JSON") == []


def test_no_false_positive_from_vietnamese_phrases(dictionary: SkillDictionary) -> None:
    # Bỏ dấu làm 'khoa học máy tính' chứa 'hoc may', 'học sau đại học' trùng 'hoc sau' (học sâu)
    deep_learning = SkillDictionary([SkillEntry(1, "Deep Learning", "AI", ("hoc sau",))])
    assert dictionary.extract("Cử nhân KHOA HỌC MÁY TÍNH, ngành Khoa học máy tính") == []
    assert dictionary.extract("Khoa hoc may tinh") == []
    assert deep_learning.extract("Đang học sau đại học") == []


def test_real_mentions_survive_false_friend_filter(dictionary: SkillDictionary) -> None:
    deep_learning = SkillDictionary([SkillEntry(1, "Deep Learning", "AI", ("hoc sau",))])
    found = dictionary.extract("Ngành Khoa học máy tính, nghiên cứu mô hình học máy")
    assert [s.name for s in found] == ["Machine Learning"]
    assert [s.name for s in deep_learning.extract("Nghiên cứu học sâu")] == ["Deep Learning"]


def test_special_characters(dictionary: SkillDictionary) -> None:
    assert {s.name for s in dictionary.extract("Lập trình C++ và cpp")} == {"C++"}


def test_split_sections() -> None:
    sections = split_sections(SAMPLE_CV)
    assert {"education", "experience", "projects", "skills", "summary"} <= set(sections)
    assert "Bách khoa" in sections["education"]


def test_parse_cv(dictionary: SkillDictionary) -> None:
    parsed = parse_cv(SAMPLE_CV, dictionary)
    assert parsed.email == "nguyenvana@gmail.com"
    assert parsed.phone == "0912345678"
    assert parsed.education[0]["degree"] == "Kỹ sư"
    assert parsed.education[0]["start_year"] == 2020
    assert parsed.education[0]["end_year"] == 2025
    assert parsed.education[0]["gpa"] == 3.45
    assert [p["name"] for p in parsed.projects] == [
        "Hệ thống gợi ý việc làm", "Chatbot tư vấn tuyển sinh",
    ]
    assert set(parsed.projects[0]["skills"]) == {"Node.js", "React", "Docker"}
    assert parsed.years_experience == 0.5


def test_explicit_years_preferred() -> None:
    assert estimate_years_experience("Có 2 năm kinh nghiệm lập trình", "") == 2.0
