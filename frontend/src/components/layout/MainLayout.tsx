import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Search as SearchIcon,
  Folder as FolderIcon,
  Timeline as TimelineIcon,
  Settings as SettingsIcon,
  Brightness4 as Brightness4Icon,
  Brightness7 as Brightness7Icon,
  Chat as ChatIcon,
} from '@mui/icons-material'
import { useTheme } from '../../contexts/ThemeContext'
import ClaudeDrawer from '../claude/ClaudeDrawer'
import { configApi } from '../../services/api'

const drawerWidth = 240

export default function MainLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [claudeOpen, setClaudeOpen] = useState(false)
  const [investigationData, setInvestigationData] = useState<{
    messages: Array<{ role: string; content: string }>
    agentId: string
    title: string
  } | null>(null)
  const [timesketchEnabled, setTimesketchEnabled] = useState(false)
  const [splunkEnabled, setSplunkEnabled] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const { mode, toggleTheme } = useTheme()

  // Check if integrations with UI are enabled
  useEffect(() => {
    const checkIntegrationStatus = async () => {
      try {
        const response = await configApi.getIntegrations()
        const enabledIntegrations = response.data?.enabled_integrations || []
        setTimesketchEnabled(enabledIntegrations.includes('timesketch'))
        setSplunkEnabled(enabledIntegrations.includes('splunk'))
      } catch (error) {
        console.error('Error checking integration status:', error)
        setTimesketchEnabled(false)
        setSplunkEnabled(false)
      }
    }
    checkIntegrationStatus()
  }, [])

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleInvestigate = (findingId: string, agentId: string, prompt: string, title: string) => {
    setInvestigationData({
      messages: [{ role: 'user', content: prompt }],
      agentId: agentId,
      title: title
    })
    setClaudeOpen(true)
  }

  // Build menu items dynamically based on integration status
  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Cases', icon: <FolderIcon />, path: '/cases' },
    ...(splunkEnabled ? [{ text: 'Splunk', icon: <SearchIcon />, path: '/splunk' }] : []),
    ...(timesketchEnabled ? [{ text: 'Timesketch', icon: <TimelineIcon />, path: '/timesketch' }] : []),
    { text: 'Settings', icon: <SettingsIcon />, path: '/settings' },
  ]

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          DeepTempo AI SOC
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => navigate(item.path)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </div>
  )

  return (
    <Box sx={{ display: 'flex', width: '100%' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {menuItems.find(item => item.path === location.pathname)?.text || 'DeepTempo AI SOC'}
          </Typography>
          <Tooltip title="Toggle DeepTempo Chat">
            <IconButton color="inherit" onClick={() => setClaudeOpen(!claudeOpen)}>
              <ChatIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Toggle theme">
            <IconButton color="inherit" onClick={toggleTheme}>
              {mode === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
        }}
      >
        <Outlet context={{ handleInvestigate }} />
      </Box>
      <ClaudeDrawer 
        open={claudeOpen} 
        onClose={() => {
          setClaudeOpen(false)
          setInvestigationData(null)
        }}
        initialMessages={investigationData?.messages}
        initialAgentId={investigationData?.agentId}
        initialTitle={investigationData?.title}
      />
    </Box>
  )
}

