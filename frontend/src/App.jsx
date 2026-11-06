import { Navigate, Route, Routes } from 'react-router-dom'
import { Spin } from 'antd'
import { HOME_BY_ROLE, VAI_TRO } from '@/constants/roles'
import AppLayout from '@/components/AppLayout'
import ProtectedRoute from '@/components/ProtectedRoute'
import { useAuth } from '@/contexts/AuthContext'
import Login from '@/pages/auth/Login'
import Register from '@/pages/auth/Register'
import LinkedInCallback from '@/pages/auth/LinkedInCallback'
import JobList from '@/pages/jobs/JobList'
import JobDetail from '@/pages/jobs/JobDetail'
import CandidateProfile from '@/pages/candidate/CandidateProfile'
import Recommendations from '@/pages/candidate/Recommendations'
import SkillGap from '@/pages/candidate/SkillGap'
import MyApplications from '@/pages/candidate/MyApplications'
import SavedJobs from '@/pages/candidate/SavedJobs'
import Privacy from '@/pages/candidate/Privacy'
import SchoolFeed from '@/pages/candidate/SchoolFeed'
import EmployerJobs from '@/pages/employer/EmployerJobs'
import JobForm from '@/pages/employer/JobForm'
import CandidateRanking from '@/pages/employer/CandidateRanking'
import CandidateProfileView from '@/pages/employer/CandidateProfileView'
import BiDashboard from '@/pages/bi/BiDashboard'
import SchoolFeedManage from '@/pages/school/SchoolFeedManage'
import SchoolSkillReport from '@/pages/school/SchoolSkillReport'
import Quarantine from '@/pages/admin/Quarantine'
import SkillDictionary from '@/pages/admin/SkillDictionary'
import DataQuality from '@/pages/admin/DataQuality'

const { CANDIDATE, EMPLOYER, SCHOOL, ADMIN } = VAI_TRO

const Home = () => {
  const { user, isLoading } = useAuth()
  if (isLoading) return <Spin style={{ display: 'block', margin: 48 }} />
  return <Navigate to={user ? HOME_BY_ROLE[user.role] : '/viec-lam'} replace />
}

const App = () => (
  <Routes>
    <Route path="/dang-nhap" element={<Login />} />
    <Route path="/dang-ky" element={<Register />} />
    <Route path="/dang-nhap/linkedin" element={<LinkedInCallback />} />
    <Route element={<AppLayout />}>
      <Route index element={<Home />} />
      <Route path="/viec-lam" element={<JobList />} />
      <Route path="/viec-lam/:jobId" element={<JobDetail />} />

      <Route element={<ProtectedRoute roles={[CANDIDATE]} />}>
        <Route path="/ho-so" element={<CandidateProfile />} />
        <Route path="/goi-y" element={<Recommendations />} />
        <Route path="/thieu-hut-ky-nang" element={<SkillGap />} />
        <Route path="/ung-tuyen" element={<MyApplications />} />
        <Route path="/tin-da-luu" element={<SavedJobs />} />
        <Route path="/quyen-rieng-tu" element={<Privacy />} />
        <Route path="/feed-truong" element={<SchoolFeed />} />
      </Route>

      <Route element={<ProtectedRoute roles={[EMPLOYER]} />}>
        <Route path="/nha-tuyen-dung/tin" element={<EmployerJobs />} />
        <Route path="/nha-tuyen-dung/tin/moi" element={<JobForm />} />
        <Route path="/nha-tuyen-dung/tin/:jobId/sua" element={<JobForm />} />
        <Route path="/nha-tuyen-dung/tin/:jobId/ung-vien" element={<CandidateRanking />} />
        <Route path="/nha-tuyen-dung/ung-vien/:candidateId" element={<CandidateProfileView />} />
      </Route>

      <Route element={<ProtectedRoute roles={[EMPLOYER, SCHOOL, ADMIN]} />}>
        <Route path="/bi" element={<BiDashboard />} />
      </Route>

      <Route element={<ProtectedRoute roles={[SCHOOL]} />}>
        <Route path="/nha-truong/feed" element={<SchoolFeedManage />} />
        <Route path="/nha-truong/bao-cao" element={<SchoolSkillReport />} />
      </Route>

      <Route element={<ProtectedRoute roles={[ADMIN]} />}>
        <Route path="/quan-tri/tin-cach-ly" element={<Quarantine />} />
        <Route path="/quan-tri/tu-dien" element={<SkillDictionary />} />
        <Route path="/quan-tri/chat-luong" element={<DataQuality />} />
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes>
)

export default App
