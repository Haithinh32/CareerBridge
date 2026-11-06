"""Dữ liệu tĩnh cho script seed: từ điển kỹ năng, khóa học, trường, doanh nghiệp, mẫu tin."""

# (tên chuẩn, nhóm, [từ đồng nghĩa / viết tắt])
SKILLS: list[tuple[str, str, list[str]]] = [
    ("Python", "Lập trình", ["python3", "py"]),
    ("Java", "Lập trình", ["java core", "java se"]),
    ("JavaScript", "Lập trình", ["js", "javascript es6", "es6", "ecmascript"]),
    ("TypeScript", "Lập trình", ["ts"]),
    ("C++", "Lập trình", ["cpp", "c plus plus"]),
    ("C#", "Lập trình", ["csharp", "c sharp"]),
    ("Golang", "Lập trình", ["go lang", "go language"]),
    ("PHP", "Lập trình", []),
    ("Kotlin", "Lập trình", []),
    ("Swift", "Lập trình", []),
    ("SQL", "Cơ sở dữ liệu", ["t-sql", "pl/sql", "truy van sql"]),
    ("PostgreSQL", "Cơ sở dữ liệu", ["postgres", "psql"]),
    ("MySQL", "Cơ sở dữ liệu", []),
    ("MongoDB", "Cơ sở dữ liệu", ["mongo"]),
    ("Redis", "Cơ sở dữ liệu", []),
    ("React", "Frontend", ["reactjs", "react.js"]),
    ("Vue.js", "Frontend", ["vuejs", "vue"]),
    ("Angular", "Frontend", ["angularjs"]),
    ("HTML/CSS", "Frontend", ["html", "css", "html5", "css3"]),
    ("Tailwind CSS", "Frontend", ["tailwind"]),
    ("Node.js", "Backend", ["nodejs", "node"]),
    ("Express", "Backend", ["expressjs", "express.js"]),
    ("Django", "Backend", []),
    ("FastAPI", "Backend", []),
    ("Spring Boot", "Backend", ["spring", "springboot"]),
    (".NET", "Backend", ["asp.net", "dotnet", ".net core"]),
    ("Laravel", "Backend", []),
    ("REST API", "Backend", ["restful", "restful api", "rest api"]),
    ("GraphQL", "Backend", []),
    ("Microservices", "Backend", ["micro services", "kien truc microservices"]),
    ("Docker", "DevOps", ["container", "docker compose"]),
    ("Kubernetes", "DevOps", ["k8s"]),
    ("AWS", "DevOps", ["amazon web services", "ec2", "s3"]),
    ("Azure", "DevOps", ["microsoft azure"]),
    ("Linux", "DevOps", ["ubuntu", "centos"]),
    ("CI/CD", "DevOps", ["ci cd", "github actions", "gitlab ci", "jenkins"]),
    ("Git", "Công cụ", ["github", "gitlab"]),
    ("Machine Learning", "AI/Dữ liệu", ["ml", "hoc may"]),
    ("Deep Learning", "AI/Dữ liệu", ["dl", "hoc sau", "neural network"]),
    ("NLP", "AI/Dữ liệu", ["xu ly ngon ngu tu nhien", "natural language processing"]),
    ("Computer Vision", "AI/Dữ liệu", ["thi giac may tinh", "opencv"]),
    ("TensorFlow", "AI/Dữ liệu", ["tf", "keras"]),
    ("PyTorch", "AI/Dữ liệu", ["torch"]),
    ("Pandas", "AI/Dữ liệu", []),
    ("Scikit-learn", "AI/Dữ liệu", ["sklearn", "scikit learn"]),
    ("Power BI", "AI/Dữ liệu", ["powerbi"]),
    ("Tableau", "AI/Dữ liệu", []),
    ("Excel", "Văn phòng", ["microsoft excel", "ms excel"]),
    ("Data Analysis", "AI/Dữ liệu", ["phan tich du lieu", "data analytics"]),
    ("Statistics", "AI/Dữ liệu", ["thong ke", "xac suat thong ke"]),
    ("Flutter", "Mobile", ["dart"]),
    ("React Native", "Mobile", ["reactnative"]),
    ("Android", "Mobile", ["android sdk"]),
    ("iOS", "Mobile", ["ios development"]),
    ("Figma", "Thiết kế", []),
    ("UI/UX Design", "Thiết kế", ["ui/ux", "ux", "ui design", "thiet ke giao dien"]),
    ("Manual Testing", "Kiểm thử", ["kiem thu thu cong", "test case", "manual test"]),
    ("Selenium", "Kiểm thử", []),
    ("Automation Testing", "Kiểm thử", ["kiem thu tu dong", "test automation", "automation test"]),
    ("Agile/Scrum", "Quy trình", ["agile", "scrum", "kanban"]),
    ("Digital Marketing", "Marketing", ["marketing so", "facebook ads", "google ads"]),
    ("SEO", "Marketing", ["toi uu cong cu tim kiem"]),
    ("Content Writing", "Marketing", ["viet content", "copywriting", "content marketing"]),
    ("Kế toán", "Tài chính", ["accounting", "ke toan tong hop"]),
    ("Tiếng Anh", "Ngoại ngữ", ["english", "ielts", "toeic"]),
    ("Tiếng Nhật", "Ngoại ngữ", ["japanese", "jlpt", "jlpt n2", "jlpt n3"]),
    ("Giao tiếp", "Kỹ năng mềm", ["communication", "ky nang giao tiep"]),
    ("Làm việc nhóm", "Kỹ năng mềm", ["teamwork", "lam viec nhom"]),
]

# (kỹ năng, tiêu đề, nền tảng, url, số giờ, miễn phí)
COURSES: list[tuple[str, str, str, str, int, bool]] = [
    ("Python", "Python for Everybody", "Coursera", "https://www.coursera.org/specializations/python", 60, False),
    ("Python", "Học Python cơ bản", "F8", "https://fullstack.edu.vn/", 20, True),
    ("SQL", "SQL for Data Science", "Coursera", "https://www.coursera.org/search?query=sql", 15, False),
    ("SQL", "SQL Tutorial", "W3Schools", "https://www.w3schools.com/sql/", 10, True),
    ("React", "React - The Complete Guide", "Udemy", "https://www.udemy.com/courses/search/?q=react", 48, False),
    ("React", "React Docs - Learn", "react.dev", "https://react.dev/learn", 12, True),
    ("Docker", "Docker for Beginners", "Docker Docs", "https://docs.docker.com/get-started/", 8, True),
    ("Docker", "Docker & Kubernetes", "Udemy", "https://www.udemy.com/courses/search/?q=docker", 22, False),
    ("Kubernetes", "Kubernetes Basics", "kubernetes.io", "https://kubernetes.io/docs/tutorials/kubernetes-basics/", 6, True),
    ("AWS", "AWS Cloud Practitioner Essentials", "AWS Skill Builder", "https://skillbuilder.aws/", 6, True),
    ("Machine Learning", "Machine Learning Specialization", "Coursera", "https://www.coursera.org/specializations/machine-learning-introduction", 90, False),
    ("Machine Learning", "Machine Learning Crash Course", "Google", "https://developers.google.com/machine-learning/crash-course", 15, True),
    ("Deep Learning", "Deep Learning Specialization", "Coursera", "https://www.coursera.org/specializations/deep-learning", 120, False),
    ("PyTorch", "Learn PyTorch", "pytorch.org", "https://pytorch.org/tutorials/", 10, True),
    ("TensorFlow", "TensorFlow Tutorials", "tensorflow.org", "https://www.tensorflow.org/tutorials", 10, True),
    ("Pandas", "Pandas - Kaggle Learn", "Kaggle", "https://www.kaggle.com/learn/pandas", 4, True),
    ("Power BI", "Power BI Data Analyst", "Microsoft Learn", "https://learn.microsoft.com/training/powerplatform/power-bi", 30, True),
    ("Tableau", "Tableau Training", "Tableau", "https://www.tableau.com/learn/training", 10, True),
    ("Data Analysis", "Google Data Analytics", "Coursera", "https://www.coursera.org/professional-certificates/google-data-analytics", 180, False),
    ("Statistics", "Statistics and Probability", "Khan Academy", "https://www.khanacademy.org/math/statistics-probability", 30, True),
    ("TypeScript", "TypeScript Handbook", "typescriptlang.org", "https://www.typescriptlang.org/docs/handbook/intro.html", 8, True),
    ("Node.js", "Node.js Learn", "nodejs.org", "https://nodejs.org/en/learn", 10, True),
    ("Spring Boot", "Spring Boot Guides", "spring.io", "https://spring.io/guides", 15, True),
    ("Java", "Java Programming MOOC", "University of Helsinki", "https://java-programming.mooc.fi/", 100, True),
    ("Git", "Pro Git", "git-scm.com", "https://git-scm.com/book/en/v2", 8, True),
    ("CI/CD", "GitHub Actions Docs", "GitHub", "https://docs.github.com/actions", 5, True),
    ("Linux", "Linux Journey", "linuxjourney.com", "https://linuxjourney.com/", 10, True),
    ("Figma", "Figma Learn", "Figma", "https://help.figma.com/hc/en-us/categories/360002051613", 6, True),
    ("UI/UX Design", "Google UX Design", "Coursera", "https://www.coursera.org/professional-certificates/google-ux-design", 200, False),
    ("Automation Testing", "Selenium WebDriver with Java", "Udemy", "https://www.udemy.com/courses/search/?q=selenium", 30, False),
    ("Selenium", "Selenium Documentation", "selenium.dev", "https://www.selenium.dev/documentation/", 6, True),
    ("Agile/Scrum", "Scrum Guide", "scrum.org", "https://scrumguides.org/", 2, True),
    ("Flutter", "Flutter Codelabs", "flutter.dev", "https://docs.flutter.dev/codelabs", 12, True),
    ("Digital Marketing", "Fundamentals of Digital Marketing", "Google Skillshop", "https://skillshop.withgoogle.com/", 40, True),
    ("Tiếng Anh", "IELTS Preparation", "British Council", "https://takeielts.britishcouncil.org/prepare-test", 40, True),
    ("Excel", "Excel Skills for Business", "Coursera", "https://www.coursera.org/specializations/excel", 40, False),
    ("REST API", "REST API Tutorial", "restfulapi.net", "https://restfulapi.net/", 4, True),
    ("Microservices", "Microservices Patterns", "microservices.io", "https://microservices.io/patterns/", 6, True),
    ("FastAPI", "FastAPI Tutorial", "fastapi.tiangolo.com", "https://fastapi.tiangolo.com/tutorial/", 8, True),
    ("Django", "Django Girls Tutorial", "djangogirls.org", "https://tutorial.djangogirls.org/", 10, True),
]

SCHOOLS: list[str] = [
    "Trường Đại học Bách khoa Hà Nội",
    "Trường Đại học Công nghệ Thông tin - ĐHQG TP.HCM",
    "Trường Đại học Kinh tế Quốc dân",
    "Trường Đại học Bách khoa - Đại học Đà Nẵng",
    "Học viện Công nghệ Bưu chính Viễn thông",
]

# Tên doanh nghiệp hư cấu để không trùng với doanh nghiệp thật
COMPANIES: list[tuple[str, str, str]] = [
    ("Công ty TNHH Sao Mai Software", "Phần mềm", "Hà Nội"),
    ("Công ty CP Công nghệ Lúa Vàng", "Phần mềm", "Hồ Chí Minh"),
    ("Công ty TNHH Dữ liệu Mây Xanh", "Dữ liệu & AI", "Hồ Chí Minh"),
    ("Công ty CP Thanh toán Cánh Diều", "Fintech", "Hà Nội"),
    ("Công ty TNHH Giải pháp Sông Hàn", "Outsourcing", "Đà Nẵng"),
    ("Công ty CP Thương mại điện tử Chợ Phố", "Thương mại điện tử", "Hồ Chí Minh"),
    ("Công ty TNHH Game Bầu Trời", "Game", "Hà Nội"),
    ("Công ty CP Y tế số An Khang", "Healthtech", "Hồ Chí Minh"),
    ("Công ty TNHH Kiểm thử Chuẩn Việt", "Kiểm thử phần mềm", "Đà Nẵng"),
    ("Công ty CP Truyền thông Ánh Dương", "Marketing", "Hà Nội"),
    ("Công ty TNHH Giáo dục Hạt Giống", "Edtech", "Hồ Chí Minh"),
    ("Công ty CP Logistics Đường Dài", "Logistics", "Cần Thơ"),
]

# Mẫu vị trí: (tiêu đề, kỹ năng bắt buộc, kỹ năng ưu tiên, lương min-max triệu theo cấp)
JOB_TEMPLATES: list[tuple[str, list[str], list[str], tuple[int, int]]] = [
    ("Lập trình viên Python Backend", ["Python", "SQL", "REST API"], ["Django", "FastAPI", "Docker", "PostgreSQL"], (12, 25)),
    ("Lập trình viên Java", ["Java", "Spring Boot", "SQL"], ["Microservices", "Docker", "MySQL"], (12, 28)),
    ("Frontend Developer (React)", ["JavaScript", "React", "HTML/CSS"], ["TypeScript", "Tailwind CSS", "Git"], (10, 25)),
    ("Fullstack Developer Node.js", ["JavaScript", "Node.js", "React"], ["TypeScript", "MongoDB", "Docker"], (14, 30)),
    ("Data Analyst", ["SQL", "Excel", "Data Analysis"], ["Power BI", "Python", "Statistics", "Tableau"], (10, 22)),
    ("Kỹ sư Machine Learning", ["Python", "Machine Learning", "Scikit-learn"], ["Deep Learning", "PyTorch", "TensorFlow", "Docker"], (18, 40)),
    ("Kỹ sư AI - Xử lý ngôn ngữ tự nhiên", ["Python", "NLP", "Deep Learning"], ["PyTorch", "Machine Learning"], (20, 45)),
    ("DevOps Engineer", ["Linux", "Docker", "CI/CD"], ["Kubernetes", "AWS", "Git"], (18, 40)),
    ("Lập trình viên Mobile Flutter", ["Flutter"], ["Android", "iOS", "Git", "REST API"], (12, 28)),
    ("Tester / QA", ["Manual Testing"], ["Automation Testing", "Selenium", "SQL", "Agile/Scrum"], (8, 18)),
    ("Automation Tester", ["Automation Testing", "Selenium"], ["Java", "Python", "CI/CD"], (14, 28)),
    ("UI/UX Designer", ["Figma", "UI/UX Design"], ["HTML/CSS"], (10, 25)),
    ("Lập trình viên .NET", ["C#", ".NET", "SQL"], ["Azure", "Docker"], (12, 28)),
    ("Lập trình viên PHP Laravel", ["PHP", "Laravel", "MySQL"], ["Vue.js", "Git"], (10, 22)),
    ("Chuyên viên Digital Marketing", ["Digital Marketing", "SEO"], ["Content Writing", "Excel"], (8, 18)),
    ("Kế toán tổng hợp", ["Kế toán", "Excel"], ["Tiếng Anh"], (8, 16)),
    ("Business Intelligence Developer", ["SQL", "Power BI"], ["Python", "Data Analysis", "Tableau"], (14, 30)),
    ("Kỹ sư Cầu nối (BrSE)", ["Tiếng Nhật", "Java"], ["Agile/Scrum", "Giao tiếp"], (20, 40)),
]

LEVEL_SETTINGS: dict[str, tuple[str, float, float]] = {
    # cấp: (tiền tố tiêu đề, số năm kinh nghiệm, hệ số lương)
    "intern": ("Thực tập sinh", 0, 0.35),
    "fresher": ("Fresher", 0, 0.6),
    "junior": ("Junior", 1, 0.85),
    "middle": ("", 2, 1.15),
    "senior": ("Senior", 4, 1.6),
}

TARGET_POSITIONS: dict[str, str] = {
    "Lập trình viên Python Backend": "Backend Developer",
    "Lập trình viên Java": "Java Developer",
    "Frontend Developer (React)": "Frontend Developer",
    "Fullstack Developer Node.js": "Fullstack Developer",
    "Data Analyst": "Data Analyst",
    "Kỹ sư Machine Learning": "Machine Learning Engineer",
    "Kỹ sư AI - Xử lý ngôn ngữ tự nhiên": "AI Engineer",
    "DevOps Engineer": "DevOps Engineer",
    "Lập trình viên Mobile Flutter": "Mobile Developer",
    "Tester / QA": "Tester",
    "Automation Tester": "Automation Tester",
    "UI/UX Designer": "UI/UX Designer",
    "Lập trình viên .NET": ".NET Developer",
    "Lập trình viên PHP Laravel": "PHP Developer",
    "Chuyên viên Digital Marketing": "Digital Marketing",
    "Kế toán tổng hợp": "Kế toán",
    "Business Intelligence Developer": "BI Developer",
    "Kỹ sư Cầu nối (BrSE)": "BrSE",
}

MAJORS: list[str] = [
    "Công nghệ thông tin", "Khoa học máy tính", "Kỹ thuật phần mềm", "Hệ thống thông tin",
    "Khoa học dữ liệu", "Kinh tế", "Marketing", "Kế toán",
]

FIRST_NAMES: list[str] = [
    "An", "Bình", "Châu", "Dũng", "Giang", "Hà", "Hải", "Hiếu", "Hoa", "Hùng", "Khánh",
    "Linh", "Long", "Mai", "Minh", "Nam", "Ngọc", "Phong", "Phương", "Quang", "Quân", "Sơn",
    "Thảo", "Thành", "Trang", "Trung", "Tú", "Tuấn", "Vy", "Yến",
]
LAST_NAMES: list[str] = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ", "Đặng", "Bùi", "Đỗ",
]
MIDDLE_NAMES: list[str] = ["Văn", "Thị", "Minh", "Đức", "Thu", "Hoàng", "Ngọc", "Quốc", "Thanh"]

SALARY_FORMATS: list[str] = [
    "{lo} - {hi} triệu", "{lo}-{hi}tr", "Từ {lo} triệu", "Up to {hi}tr",
    "{lo_full} - {hi_full} VNĐ", "Thỏa thuận",
]
LOCATION_FORMATS: dict[str, list[str]] = {
    "Hà Nội": ["Hà Nội", "HN", "Cầu Giấy, Hà Nội", "Hanoi"],
    "Hồ Chí Minh": ["TP.HCM", "Hồ Chí Minh", "Quận 1, TP. Hồ Chí Minh", "Sài Gòn", "HCM"],
    "Đà Nẵng": ["Đà Nẵng", "Da Nang"],
    "Cần Thơ": ["Cần Thơ"],
}

# Tin có vấn đề để minh họa chức năng phát hiện tin kém chất lượng
BAD_JOBS: list[dict] = [
    {
        "title": "Tuyển CTV online việc nhẹ lương cao",
        "company": "Hộ kinh doanh Phát Tài",
        "description": "Việc nhẹ lương cao, làm tại nhà, thu nhập 20-30 triệu/tháng không cần kinh "
        "nghiệm. Ứng viên cần đóng phí hồ sơ 500k và đặt cọc đồng phục. Chỉ liên hệ qua Zalo.",
        "salary": "20 - 30 triệu", "location": "Toàn quốc", "level": "fresher", "years": 0,
    },
    {
        "title": "Fresher Java Developer",
        "company": "Công ty TNHH Sao Mai Software",
        "description": "Tuyển Fresher Java. Yêu cầu ít nhất 3 năm kinh nghiệm Java, Spring Boot, "
        "Microservices, đã từng làm leader nhóm. Ưu tiên có kinh nghiệm AWS và Kubernetes.",
        "salary": "8 - 10 triệu", "location": "Hà Nội", "level": "fresher", "years": 3,
    },
    {
        "title": "Nhân viên nhập liệu tại nhà",
        "company": "Kinh doanh online Ánh Kim",
        "description": "Nhận hàng tại nhà, like share đánh giá sản phẩm, chuyển khoản trước để "
        "kích hoạt tài khoản. Thu nhập khủng 15 triệu/tuần.",
        "salary": "Thỏa thuận", "location": "Remote", "level": "intern", "years": 0,
    },
]
