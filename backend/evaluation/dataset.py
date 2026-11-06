"""Tập dữ liệu đánh giá gán nhãn thủ công, ĐỘC LẬP với thuật toán.

- expected_skills: kỹ năng người đánh giá đọc CV và ghi nhận (dùng đo trích xuất CV)
- relevance: mức phù hợp do người đánh giá gán, 2 = rất phù hợp, 1 = phù hợp một phần,
  không liệt kê = không phù hợp (dùng đo chất lượng xếp hạng)
"""

JOBS: list[dict] = [
    {"id": 1, "title": "Backend Developer Python", "location": "Hồ Chí Minh", "work_type": "full_time",
     "years": 0, "required": ["Python", "SQL", "REST API"], "optional": ["Django", "FastAPI", "Docker"],
     "description": "Xây dựng REST API cho hệ thống thương mại điện tử bằng Python (Django/FastAPI), "
                    "thiết kế cơ sở dữ liệu PostgreSQL, viết unit test, đóng gói bằng Docker."},
    {"id": 2, "title": "Java Developer (Spring Boot)", "location": "Hà Nội", "work_type": "full_time",
     "years": 1, "required": ["Java", "Spring Boot", "SQL"], "optional": ["Microservices", "MySQL"],
     "description": "Phát triển hệ thống core banking bằng Java Spring Boot theo kiến trúc "
                    "microservices, làm việc với MySQL và Oracle."},
    {"id": 3, "title": "Frontend Developer ReactJS", "location": "Hồ Chí Minh", "work_type": "full_time",
     "years": 0, "required": ["JavaScript", "React", "HTML/CSS"], "optional": ["TypeScript", "Tailwind CSS"],
     "description": "Xây dựng giao diện web bằng React, tối ưu hiệu năng, chuyển thiết kế Figma thành "
                    "component tái sử dụng, phối hợp với backend qua REST API."},
    {"id": 4, "title": "Data Analyst", "location": "Hà Nội", "work_type": "full_time",
     "years": 0, "required": ["SQL", "Excel", "Data Analysis"], "optional": ["Power BI", "Python", "Statistics"],
     "description": "Phân tích dữ liệu bán hàng, viết truy vấn SQL, xây dựng báo cáo Power BI và "
                    "trình bày insight cho ban giám đốc."},
    {"id": 5, "title": "Machine Learning Engineer", "location": "Hồ Chí Minh", "work_type": "full_time",
     "years": 1, "required": ["Python", "Machine Learning", "Scikit-learn"], "optional": ["PyTorch", "Deep Learning", "Docker"],
     "description": "Huấn luyện và triển khai mô hình học máy cho bài toán gợi ý sản phẩm và dự đoán "
                    "rời bỏ khách hàng, theo dõi chất lượng mô hình trên production."},
    {"id": 6, "title": "DevOps Engineer", "location": "Hà Nội", "work_type": "full_time",
     "years": 1, "required": ["Linux", "Docker", "CI/CD"], "optional": ["Kubernetes", "AWS"],
     "description": "Vận hành hạ tầng cloud, xây dựng pipeline CI/CD, quản lý container bằng "
                    "Kubernetes, giám sát hệ thống Linux."},
    {"id": 7, "title": "Mobile Developer Flutter", "location": "Đà Nẵng", "work_type": "full_time",
     "years": 0, "required": ["Flutter"], "optional": ["Android", "iOS", "REST API"],
     "description": "Phát triển ứng dụng di động đa nền tảng bằng Flutter, tích hợp API và đưa ứng "
                    "dụng lên App Store, Google Play."},
    {"id": 8, "title": "Tester / QA Engineer", "location": "Hồ Chí Minh", "work_type": "full_time",
     "years": 0, "required": ["Manual Testing"], "optional": ["Automation Testing", "Selenium", "SQL"],
     "description": "Viết test case, thực hiện kiểm thử chức năng và hồi quy cho ứng dụng web, báo "
                    "cáo lỗi trên Jira, tham gia quy trình Scrum."},
    {"id": 9, "title": "UI/UX Designer", "location": "Hồ Chí Minh", "work_type": "hybrid",
     "years": 0, "required": ["Figma", "UI/UX Design"], "optional": ["HTML/CSS"],
     "description": "Nghiên cứu người dùng, thiết kế wireframe và prototype trên Figma, xây dựng "
                    "design system cho sản phẩm web và mobile."},
    {"id": 10, "title": "Chuyên viên Digital Marketing", "location": "Hà Nội", "work_type": "full_time",
     "years": 0, "required": ["Digital Marketing", "SEO"], "optional": ["Content Writing", "Excel"],
     "description": "Lên kế hoạch và chạy quảng cáo Facebook Ads, Google Ads, tối ưu SEO website, "
                    "đo lường hiệu quả chiến dịch."},
    {"id": 11, "title": "Fullstack Developer Node.js/React", "location": "Từ xa", "work_type": "remote",
     "years": 1, "required": ["JavaScript", "Node.js", "React"], "optional": ["TypeScript", "MongoDB"],
     "description": "Phát triển sản phẩm SaaS từ backend Node.js Express đến frontend React, làm "
                    "việc từ xa với đội ngũ quốc tế."},
    {"id": 12, "title": "BI Developer", "location": "Hồ Chí Minh", "work_type": "full_time",
     "years": 0, "required": ["SQL", "Power BI"], "optional": ["Python", "Data Analysis"],
     "description": "Xây dựng data mart và dashboard Power BI, viết truy vấn SQL phức tạp, tự động "
                    "hóa báo cáo bằng Python."},
    {"id": 13, "title": "AI Engineer - NLP", "location": "Hà Nội", "work_type": "full_time",
     "years": 1, "required": ["Python", "NLP", "Deep Learning"], "optional": ["PyTorch", "Machine Learning"],
     "description": "Nghiên cứu và phát triển mô hình xử lý ngôn ngữ tự nhiên tiếng Việt: phân loại "
                    "văn bản, trích xuất thông tin, chatbot."},
    {"id": 14, "title": "Kế toán tổng hợp", "location": "Hồ Chí Minh", "work_type": "full_time",
     "years": 1, "required": ["Kế toán", "Excel"], "optional": ["Tiếng Anh"],
     "description": "Hạch toán, lập báo cáo tài chính, quyết toán thuế, làm việc với kiểm toán."},
]

CANDIDATES: list[dict] = [
    {"id": 1, "location": "Hồ Chí Minh", "work_types": ["full_time"], "years": 0,
     "target": "Backend Developer",
     "cv": "MỤC TIÊU\nTrở thành lập trình viên backend.\nKỸ NĂNG\nPython3, Django, Postgres, "
           "RESTful API, Git\nDỰ ÁN\nWebsite đặt vé xem phim\n- Backend bằng Django, deploy bằng "
           "docker compose\n- Thiết kế cơ sở dữ liệu, viết truy vấn SQL",
     "expected_skills": ["Python", "Django", "PostgreSQL", "REST API", "Git", "Docker", "SQL"],
     "relevance": {1: 2, 12: 1, 6: 1}},
    {"id": 2, "location": "Hà Nội", "work_types": ["full_time", "internship"], "years": 0,
     "target": "Data Analyst",
     "cv": "HỌC VẤN\nĐại học Kinh tế Quốc dân - Cử nhân Hệ thống thông tin\nKỸ NĂNG\nSQL, Microsoft "
           "Excel, PowerBI, Pandas, xác suất thống kê\nDỰ ÁN\nPhân tích dữ liệu bán lẻ\n- Làm sạch "
           "dữ liệu bằng pandas, trực quan hóa trên Power BI",
     "expected_skills": ["SQL", "Excel", "Power BI", "Pandas", "Statistics", "Data Analysis"],
     "relevance": {4: 2, 12: 2}},
    {"id": 3, "location": "Hà Nội", "work_types": ["full_time"], "years": 1,
     "target": "AI Engineer",
     "cv": "KINH NGHIỆM LÀM VIỆC\n1 năm kinh nghiệm nghiên cứu học máy tại phòng lab\nKỸ NĂNG\n"
           "Python, sklearn, PyTorch, deep learning, xử lý ngôn ngữ tự nhiên, Tiếng Anh (IELTS 7.0)"
           "\nDỰ ÁN\nPhân loại cảm xúc bình luận tiếng Việt\n- Fine-tune mô hình transformer bằng "
           "PyTorch",
     "expected_skills": ["Python", "Machine Learning", "Scikit-learn", "PyTorch", "Deep Learning",
                         "NLP", "Tiếng Anh"],
     "relevance": {13: 2, 5: 2, 1: 1}},
    {"id": 4, "location": "Hồ Chí Minh", "work_types": ["full_time", "remote"], "years": 1,
     "target": "Frontend Developer",
     "cv": "KỸ NĂNG\nJS (ES6), TypeScript, ReactJS, HTML5/CSS3, Tailwind\nDỰ ÁN\nTrang quản trị "
           "bán hàng\n- Xây dựng bằng React và TypeScript, gọi REST API\nKINH NGHIỆM\n1 năm kinh "
           "nghiệm frontend",
     "expected_skills": ["JavaScript", "TypeScript", "React", "HTML/CSS", "Tailwind CSS",
                         "REST API"],
     "relevance": {3: 2, 11: 2, 9: 1}},
    {"id": 5, "location": "Hà Nội", "work_types": ["full_time"], "years": 1,
     "target": "Java Developer",
     "cv": "KỸ NĂNG\nJava core, Spring Boot, MySQL, Git, kiến trúc microservices\nKINH NGHIỆM\n"
           "1 năm kinh nghiệm Java tại công ty outsourcing",
     "expected_skills": ["Java", "Spring Boot", "MySQL", "Git", "Microservices"],
     "relevance": {2: 2, 1: 1}},
    {"id": 6, "location": "Hồ Chí Minh", "work_types": ["full_time"], "years": 0,
     "target": "Tester",
     "cv": "KỸ NĂNG\nKiểm thử thủ công, viết test case, Selenium cơ bản, SQL, Agile\nDỰ ÁN\n"
           "Kiểm thử website thương mại điện tử\n- Viết 200 test case, báo lỗi trên Jira",
     "expected_skills": ["Manual Testing", "Selenium", "SQL", "Agile/Scrum"],
     "relevance": {8: 2}},
    {"id": 7, "location": "Hồ Chí Minh", "work_types": ["hybrid", "full_time"], "years": 0,
     "target": "UI/UX Designer",
     "cv": "KỸ NĂNG\nFigma, thiết kế giao diện, UX research, HTML/CSS cơ bản\nDỰ ÁN\nRedesign "
           "ứng dụng đặt đồ ăn\n- Wireframe và prototype trên Figma",
     "expected_skills": ["Figma", "UI/UX Design", "HTML/CSS"],
     "relevance": {9: 2, 3: 1}},
    {"id": 8, "location": "Hà Nội", "work_types": ["full_time"], "years": 0,
     "target": "Digital Marketing",
     "cv": "KỸ NĂNG\nGoogle Ads, Facebook Ads, SEO, viết content, Excel\nDỰ ÁN\nChiến dịch "
           "marketing cho cửa hàng mỹ phẩm online",
     "expected_skills": ["Digital Marketing", "SEO", "Content Writing", "Excel"],
     "relevance": {10: 2}},
    {"id": 9, "location": "Hà Nội", "work_types": ["full_time"], "years": 1,
     "target": "DevOps Engineer",
     "cv": "KỸ NĂNG\nLinux (Ubuntu), Docker, k8s, AWS EC2/S3, GitHub Actions, Python scripting\n"
           "KINH NGHIỆM\n1 năm kinh nghiệm vận hành hệ thống",
     "expected_skills": ["Linux", "Docker", "Kubernetes", "AWS", "CI/CD", "Python", "Git"],
     "relevance": {6: 2, 1: 1}},
    {"id": 10, "location": "Đà Nẵng", "work_types": ["full_time"], "years": 0,
     "target": "Mobile Developer",
     "cv": "KỸ NĂNG\nFlutter, Dart, Android, Firebase, REST API\nDỰ ÁN\nỨng dụng học từ vựng\n"
           "- Viết bằng Flutter, đã đưa lên Google Play",
     "expected_skills": ["Flutter", "Android", "REST API"],
     "relevance": {7: 2}},
]
