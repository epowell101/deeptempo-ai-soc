import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'
import MainLayout from './components/layout/MainLayout'
import Dashboard from './pages/Dashboard'
import Cases from './pages/Cases'
import Timesketch from './pages/Timesketch'
import Settings from './pages/Settings'

function App() {
  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="cases" element={<Cases />} />
          <Route path="timesketch" element={<Timesketch />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </Box>
  )
}

export default App

