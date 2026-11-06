export const TRANG_THAI_UNG_TUYEN = {
  SUBMITTED: 'submitted',
  VIEWED: 'viewed',
  INTERVIEW: 'interview',
  HIRED: 'hired',
  REJECTED: 'rejected',
}

export const TRANG_THAI_UNG_TUYEN_UI = {
  [TRANG_THAI_UNG_TUYEN.SUBMITTED]: { color: 'blue', text: 'Đã nộp' },
  [TRANG_THAI_UNG_TUYEN.VIEWED]: { color: 'cyan', text: 'Đã xem' },
  [TRANG_THAI_UNG_TUYEN.INTERVIEW]: { color: 'gold', text: 'Mời phỏng vấn' },
  [TRANG_THAI_UNG_TUYEN.HIRED]: { color: 'green', text: 'Trúng tuyển' },
  [TRANG_THAI_UNG_TUYEN.REJECTED]: { color: 'red', text: 'Từ chối' },
}

// Bước tiếp theo nhà tuyển dụng được chọn, khớp ALLOWED_TRANSITIONS ở backend
export const BUOC_TIEP_THEO = {
  [TRANG_THAI_UNG_TUYEN.SUBMITTED]: [
    TRANG_THAI_UNG_TUYEN.INTERVIEW,
    TRANG_THAI_UNG_TUYEN.REJECTED,
  ],
  [TRANG_THAI_UNG_TUYEN.VIEWED]: [TRANG_THAI_UNG_TUYEN.INTERVIEW, TRANG_THAI_UNG_TUYEN.REJECTED],
  [TRANG_THAI_UNG_TUYEN.INTERVIEW]: [TRANG_THAI_UNG_TUYEN.HIRED, TRANG_THAI_UNG_TUYEN.REJECTED],
  [TRANG_THAI_UNG_TUYEN.HIRED]: [],
  [TRANG_THAI_UNG_TUYEN.REJECTED]: [],
}

export const LOAI_TAI_LIEU = {
  CV: 'cv',
  PROJECT: 'project',
  LINKEDIN_PDF: 'linkedin_pdf',
}

export const LOAI_TAI_LIEU_LABEL = {
  [LOAI_TAI_LIEU.CV]: 'CV',
  [LOAI_TAI_LIEU.PROJECT]: 'Đồ án / dự án',
  [LOAI_TAI_LIEU.LINKEDIN_PDF]: 'Hồ sơ LinkedIn (PDF)',
}

export const NGUON_KY_NANG_LABEL = {
  ai_extracted: 'AI trích xuất',
  manual: 'Tự thêm',
}

export const MUC_DICH_DONG_Y = {
  CV_ANALYSIS: 'cv_analysis',
  JOB_RECOMMENDATION: 'job_recommendation',
  EMPLOYER_DISCOVERY: 'employer_discovery',
  SCHOOL_SHARING: 'school_sharing',
  MODEL_IMPROVEMENT: 'model_improvement',
}

export const MUC_DICH_DONG_Y_UI = {
  [MUC_DICH_DONG_Y.CV_ANALYSIS]: {
    title: 'Phân tích CV tự động',
    description: 'AI đọc CV/đồ án bạn tải lên để trích kỹ năng, học vấn và dự án.',
  },
  [MUC_DICH_DONG_Y.JOB_RECOMMENDATION]: {
    title: 'Gợi ý việc làm',
    description: 'Dùng hồ sơ và kỹ năng của bạn để tính điểm phù hợp với các tin tuyển dụng.',
  },
  [MUC_DICH_DONG_Y.EMPLOYER_DISCOVERY]: {
    title: 'Cho phép nhà tuyển dụng tìm thấy bạn',
    description:
      'Hồ sơ xuất hiện trong danh sách xếp hạng ứng viên của nhà tuyển dụng dù bạn chưa ứng tuyển.',
  },
  [MUC_DICH_DONG_Y.SCHOOL_SHARING]: {
    title: 'Chia sẻ số liệu tổng hợp với nhà trường',
    description: 'Kỹ năng của bạn được tính (ẩn danh, tổng hợp) vào báo cáo kỹ năng của trường.',
  },
  [MUC_DICH_DONG_Y.MODEL_IMPROVEMENT]: {
    title: 'Cải thiện mô hình gợi ý',
    description: 'Đánh giá "có phù hợp không" của bạn được dùng để huấn luyện lại thuật toán khớp.',
  },
}

export const LY_DO_THU_HOI_LABEL = {
  candidate_rejected: 'Doanh nghiệp đã từ chối hồ sơ',
  job_closed: 'Vị trí đã đóng',
  consent_withdrawn: 'Bạn đã rút đồng ý',
}

export const NGUON_TRUY_CAP_LABEL = {
  application: 'Bạn ứng tuyển',
  discovery: 'Doanh nghiệp tìm thấy bạn',
}

export const DAC_TRUNG_KHOP_LABEL = {
  skill: 'Kỹ năng',
  text: 'Nội dung CV',
  experience: 'Kinh nghiệm',
  location: 'Địa điểm',
  work_type: 'Hình thức',
  title: 'Vị trí mục tiêu',
}
