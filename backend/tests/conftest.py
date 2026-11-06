import os
import tempfile

# Phải đặt trước khi import ứng dụng để engine trỏ tới CSDL tạm
_tmp_dir = tempfile.mkdtemp(prefix="careerbridge-test-")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_tmp_dir}/test.db"
os.environ["UPLOAD_DIR"] = f"{_tmp_dir}/uploads"
os.environ["ENABLE_SCHEDULER"] = "false"

import pytest  # noqa: E402

from ai.skill_extractor import SkillDictionary, SkillEntry  # noqa: E402


@pytest.fixture
def dictionary() -> SkillDictionary:
    return SkillDictionary(
        [
            SkillEntry(1, "Python", "Lập trình", ("python3",)),
            SkillEntry(2, "JavaScript", "Lập trình", ("js",)),
            SkillEntry(3, "React", "Frontend", ("reactjs", "react.js")),
            SkillEntry(4, "React Native", "Mobile", ()),
            SkillEntry(5, "SQL", "Cơ sở dữ liệu", ()),
            SkillEntry(6, "Docker", "DevOps", ()),
            SkillEntry(7, "Machine Learning", "AI", ("ml", "hoc may")),
            SkillEntry(8, "C++", "Lập trình", ("cpp",)),
            SkillEntry(9, "Node.js", "Backend", ("nodejs",)),
            SkillEntry(10, "Tiếng Anh", "Ngoại ngữ", ("ielts",)),
        ]
    )
