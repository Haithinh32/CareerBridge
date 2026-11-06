export const HINH_THUC = {
  FULL_TIME: 'full_time',
  PART_TIME: 'part_time',
  INTERNSHIP: 'internship',
  REMOTE: 'remote',
  HYBRID: 'hybrid',
}

export const HINH_THUC_LABEL = {
  [HINH_THUC.FULL_TIME]: 'Toàn thời gian',
  [HINH_THUC.PART_TIME]: 'Bán thời gian',
  [HINH_THUC.INTERNSHIP]: 'Thực tập',
  [HINH_THUC.REMOTE]: 'Từ xa',
  [HINH_THUC.HYBRID]: 'Kết hợp',
}

export const CAP_BAC = {
  INTERN: 'intern',
  FRESHER: 'fresher',
  JUNIOR: 'junior',
  MIDDLE: 'middle',
  SENIOR: 'senior',
}

export const CAP_BAC_LABEL = {
  [CAP_BAC.INTERN]: 'Thực tập sinh',
  [CAP_BAC.FRESHER]: 'Fresher',
  [CAP_BAC.JUNIOR]: 'Junior',
  [CAP_BAC.MIDDLE]: 'Middle',
  [CAP_BAC.SENIOR]: 'Senior',
}

export const TRANG_THAI_TIN = {
  OPEN: 'open',
  QUARANTINED: 'quarantined',
  CLOSED: 'closed',
  EXPIRED: 'expired',
  REJECTED: 'rejected',
}

export const TRANG_THAI_TIN_UI = {
  [TRANG_THAI_TIN.OPEN]: { color: 'green', text: 'Đang mở' },
  [TRANG_THAI_TIN.QUARANTINED]: { color: 'orange', text: 'Chờ duyệt (cách ly)' },
  [TRANG_THAI_TIN.CLOSED]: { color: 'default', text: 'Đã đóng' },
  [TRANG_THAI_TIN.EXPIRED]: { color: 'default', text: 'Hết hạn' },
  [TRANG_THAI_TIN.REJECTED]: { color: 'red', text: 'Bị loại' },
}

export const LOAI_CO = {
  DUPLICATE: 'duplicate',
  EXPIRED: 'expired',
  FRESHER_REQUIRES_EXPERIENCE: 'fresher_requires_experience',
  SCAM: 'scam',
  INCOMPLETE: 'incomplete',
}

export const LOAI_CO_UI = {
  [LOAI_CO.DUPLICATE]: { color: 'purple', text: 'Tin trùng' },
  [LOAI_CO.EXPIRED]: { color: 'default', text: 'Hết hạn' },
  [LOAI_CO.FRESHER_REQUIRES_EXPERIENCE]: { color: 'gold', text: 'Fresher đòi kinh nghiệm' },
  [LOAI_CO.SCAM]: { color: 'red', text: 'Nghi lừa đảo' },
  [LOAI_CO.INCOMPLETE]: { color: 'blue', text: 'Thiếu thông tin' },
}

export const HANH_DONG_DUYET = {
  APPROVE: 'approve',
  REJECT: 'reject',
}

export const DIA_DIEM = ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Cần Thơ', 'Hải Phòng', 'Từ xa']
