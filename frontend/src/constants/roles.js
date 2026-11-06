export const VAI_TRO = {
  CANDIDATE: 'candidate',
  EMPLOYER: 'employer',
  SCHOOL: 'school',
  ADMIN: 'admin',
}

export const VAI_TRO_LABEL = {
  [VAI_TRO.CANDIDATE]: 'Sinh viên / Người mới đi làm',
  [VAI_TRO.EMPLOYER]: 'Nhà tuyển dụng',
  [VAI_TRO.SCHOOL]: 'Nhà trường',
  [VAI_TRO.ADMIN]: 'Quản trị viên',
}

export const HOME_BY_ROLE = {
  [VAI_TRO.CANDIDATE]: '/goi-y',
  [VAI_TRO.EMPLOYER]: '/nha-tuyen-dung/tin',
  [VAI_TRO.SCHOOL]: '/nha-truong/feed',
  [VAI_TRO.ADMIN]: '/quan-tri/tin-cach-ly',
}
