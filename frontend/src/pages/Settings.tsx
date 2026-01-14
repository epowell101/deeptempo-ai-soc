import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  TextField,
  Button,
  Alert,
  Switch,
  FormControlLabel,
  FormGroup,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  Grid,
  Card,
  CardContent,
  CardActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip,
} from '@mui/material'
import { useNotifications } from '../contexts/NotificationContext'
import { notificationService } from '../services/notifications'
import { 
  Save as SaveIcon, 
  Refresh as RefreshIcon,
  Add as AddIcon,
  CheckCircle as CheckIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Description as LogsIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  HelpOutline as HelpIcon,
  Search as SearchIcon,
} from '@mui/icons-material'
import { configApi, mcpApi, storageApi } from '../services/api'
import IntegrationWizard from '../components/settings/IntegrationWizard'
import CustomIntegrationBuilder from '../components/settings/CustomIntegrationBuilder'
import { INTEGRATIONS, INTEGRATION_CATEGORIES, getIntegrationsByCategory, getAllIntegrations, loadCustomIntegrations } from '../config/integrations'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

export default function Settings() {
  const [currentTab, setCurrentTab] = useState(0)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const { notificationsEnabled, setNotificationsEnabled, permissionGranted } = useNotifications()

  // Claude settings
  const [claudeConfig, setClaudeConfig] = useState({
    api_key: '',
    configured: false,
  })


  // S3 settings
  const [s3Config, setS3Config] = useState({
    bucket_name: '',
    region: 'us-east-1',
    access_key_id: '',
    secret_access_key: '',
    findings_path: 'findings.json',
    cases_path: 'cases.json',
    configured: false,
  })


  // MCP settings
  const [mcpServers, setMcpServers] = useState<string[]>([])
  const [mcpStatuses, setMcpStatuses] = useState<Record<string, string>>({})
  const [logsDialog, setLogsDialog] = useState<{ open: boolean; server: string; logs: string }>({
    open: false,
    server: '',
    logs: '',
  })
  const [s3SetupDialogOpen, setS3SetupDialogOpen] = useState(false)
  const [claudeSetupDialogOpen, setClaudeSetupDialogOpen] = useState(false)
  const [githubSetupDialogOpen, setGithubSetupDialogOpen] = useState(false)
  const [postgresqlSetupDialogOpen, setPostgresqlSetupDialogOpen] = useState(false)

  // GitHub settings
  const [githubConfig, setGithubConfig] = useState({
    token: '',
    configured: false,
  })

  // PostgreSQL settings
  const [postgresqlConfig, setPostgresqlConfig] = useState({
    connection_string: '',
    configured: false,
  })
  
  // Storage backend status
  const [storageStatus, setStorageStatus] = useState<{
    backend: string
    database_available: boolean
    json_available: boolean
    description: string
    recommendations: any[]
  } | null>(null)
  
  const [storageHealth, setStorageHealth] = useState<{
    healthy: boolean
    backend: string
    findings_count: number
    cases_count: number
    message: string
  } | null>(null)
  
  const [reconnecting, setReconnecting] = useState(false)

  // Integrations settings
  const [integrationsConfig, setIntegrationsConfig] = useState({
    enabled_integrations: [] as string[],
    integrations: {} as Record<string, any>,
    configured: false,
  })
  
  // Integration wizard
  const [wizardOpen, setWizardOpen] = useState(false)
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(null)
  
  // Custom integration builder
  const [customIntegrationBuilderOpen, setCustomIntegrationBuilderOpen] = useState(false)
  
  // Integration search
  const [integrationSearch, setIntegrationSearch] = useState('')

  // General settings
  const [generalConfig, setGeneralConfig] = useState({
    auto_start_sync: false,
    show_notifications: true,
    theme: 'dark',
    enable_keyring: false,
  })

  useEffect(() => {
    loadConfigs()
  }, [])

  // Sync notifications enabled state with general config
  useEffect(() => {
    setGeneralConfig(prev => ({ ...prev, show_notifications: notificationsEnabled }))
  }, [notificationsEnabled])

  useEffect(() => {
    if (currentTab === 3) { // MCP Servers tab
      loadMcpServers()
    } else if (currentTab === 4) { // PostgreSQL tab
      loadStorageStatus()
    }
  }, [currentTab])

  const loadConfigs = async () => {
    // Load custom integrations first
    try {
      await loadCustomIntegrations()
    } catch (error) {
      console.error('Error loading custom integrations:', error)
    }

    try {
      // Load GitHub config
      const githubData = await configApi.getGitHub()
      setGithubConfig({ ...githubConfig, configured: githubData.data?.configured || false })
      
      // Load PostgreSQL config
      const postgresqlData = await configApi.getPostgreSQL()
      setPostgresqlConfig({ ...postgresqlConfig, configured: postgresqlData.data?.configured || false })
    } catch (error) {
      console.error('Error loading GitHub/PostgreSQL configs:', error)
    }

    try {
      const [claude, s3, integrations, general] = await Promise.all([
        configApi.getClaude().catch(() => ({ data: { configured: false } })),
        configApi.getS3().catch(() => ({ data: { configured: false } })),
        configApi.getIntegrations().catch(() => ({ data: { configured: false, enabled_integrations: [], integrations: {} } })),
        configApi.getGeneral().catch(() => ({ data: { auto_start_sync: false, show_notifications: true, theme: 'dark', enable_keyring: false } })),
      ])
      setClaudeConfig(prev => ({ ...prev, configured: claude.data.configured }))
      setS3Config(prev => ({ ...prev, ...s3.data }))
      setIntegrationsConfig(prev => ({ ...prev, ...integrations.data }))
      setGeneralConfig(prev => ({ ...prev, ...general.data }))
    } catch (error) {
      console.error('Failed to load configs:', error)
    }
  }

  const loadMcpServers = async () => {
    try {
      const [servers, statuses] = await Promise.all([
        mcpApi.listServers(),
        mcpApi.getStatuses(),
      ])
      setMcpServers(servers.data.servers || [])
      
      // Convert list format to dictionary format
      const statusList = statuses.data.statuses || []
      const statusDict: Record<string, string> = {}
      if (Array.isArray(statusList)) {
        statusList.forEach((item: any) => {
          if (item.name && item.status) {
            statusDict[item.name] = item.status
          }
        })
      } else {
        // Fallback for old format (if it's already a dict)
        Object.assign(statusDict, statusList)
      }
      setMcpStatuses(statusDict)
    } catch (error) {
      console.error('Failed to load MCP servers:', error)
    }
  }
  
  const loadStorageStatus = async () => {
    try {
      const [status, health] = await Promise.all([
        storageApi.getStatus(),
        storageApi.getHealth(),
      ])
      setStorageStatus(status.data)
      setStorageHealth(health.data)
    } catch (error) {
      console.error('Failed to load storage status:', error)
    }
  }
  
  const handleReconnectDatabase = async () => {
    setReconnecting(true)
    try {
      const response = await storageApi.reconnect()
      const data = response.data
      
      if (data.success) {
        setMessage({ 
          type: 'success', 
          text: 'Successfully reconnected to PostgreSQL database!' 
        })
        // Reload storage status to show updated connection
        await loadStorageStatus()
      } else {
        setMessage({ 
          type: 'error', 
          text: data.message || 'Failed to reconnect to database' 
        })
      }
      setTimeout(() => setMessage(null), 5000)
    } catch (error: any) {
      console.error('Failed to reconnect to database:', error)
      setMessage({ 
        type: 'error', 
        text: error.response?.data?.message || 'Failed to reconnect to database' 
      })
      setTimeout(() => setMessage(null), 5000)
    } finally {
      setReconnecting(false)
    }
  }

  const handleSaveClaude = async () => {
    try {
      await configApi.setClaude(claudeConfig.api_key)
      setMessage({ type: 'success', text: 'Claude API key saved successfully' })
      setTimeout(() => setMessage(null), 3000)
      await loadConfigs()
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save Claude API key' })
    }
  }


  const handleSaveS3 = async () => {
    try {
      await configApi.setS3(s3Config)
      setMessage({ type: 'success', text: 'S3 configuration saved' })
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save S3 configuration' })
    }
  }


  const handleSaveGeneral = async () => {
    try {
      await configApi.setGeneral(generalConfig)
      setMessage({ type: 'success', text: 'General settings saved' })
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save general settings' })
    }
  }

  const handleNotificationToggle = async (checked: boolean) => {
    try {
      if (checked && !notificationService.isSupported()) {
        setMessage({ type: 'error', text: 'Your browser does not support desktop notifications' })
        return
      }

      await setNotificationsEnabled(checked)
      setGeneralConfig({ ...generalConfig, show_notifications: checked })
      
      if (checked && permissionGranted) {
        // Show a test notification
        notificationService.notifyGeneric(
          'Notifications Enabled',
          'You will now receive desktop notifications for important events',
          { severity: 'success' }
        )
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to enable notifications. Please check browser permissions.' })
    }
  }

  const handleTestNotification = () => {
    if (!notificationService.isSupported()) {
      setMessage({ type: 'error', text: 'Your browser does not support desktop notifications' })
      return
    }

    if (!permissionGranted) {
      setMessage({ type: 'error', text: 'Notification permission not granted. Please enable notifications first.' })
      return
    }

    notificationService.notifyGeneric(
      'Test Notification',
      'This is a test desktop notification from DeepTempo AI SOC',
      { severity: 'info' }
    )
    setMessage({ type: 'success', text: 'Test notification sent' })
    setTimeout(() => setMessage(null), 3000)
  }

  const handleSaveGitHub = async () => {
    try {
      await configApi.setGitHub(githubConfig.token)
      setMessage({ type: 'success', text: 'GitHub token saved successfully' })
      setTimeout(() => setMessage(null), 3000)
      await loadConfigs()
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save GitHub token' })
    }
  }

  const handleSavePostgreSQL = async () => {
    try {
      await configApi.setPostgreSQL(postgresqlConfig.connection_string)
      setMessage({ type: 'success', text: 'PostgreSQL connection string saved successfully' })
      setTimeout(() => setMessage(null), 3000)
      await loadConfigs()
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save PostgreSQL configuration' })
    }
  }

  const handleMcpServerAction = async (serverName: string, action: 'start' | 'stop') => {
    try {
      if (action === 'start') {
        await mcpApi.startServer(serverName)
      } else {
        await mcpApi.stopServer(serverName)
      }
      setMessage({ type: 'success', text: `Server ${serverName} ${action}ed successfully` })
      setTimeout(() => setMessage(null), 3000)
      loadMcpServers()
    } catch (error: any) {
      const errorMsg = `Failed to ${action} server ${serverName}`
      setMessage({ type: 'error', text: errorMsg })
      
      // Send desktop notification for MCP server error
      notificationService.notifyMcpServerStatus({
        name: serverName,
        status: 'error',
        error: error?.response?.data?.detail || errorMsg,
      })
    }
  }

  const handleStartAll = async () => {
    try {
      await mcpApi.startAll()
      setMessage({ type: 'success', text: 'All servers started successfully' })
      setTimeout(() => setMessage(null), 3000)
      
      // Send desktop notification for successful bulk start
      notificationService.notifyGeneric(
        'MCP Servers Started',
        'All MCP servers have been started successfully',
        { severity: 'success', requireInteraction: false }
      )
      
      loadMcpServers()
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to start all servers' })
      
      // Send desktop notification for bulk start failure
      notificationService.notifyGeneric(
        'MCP Servers Start Failed',
        error?.response?.data?.detail || 'Failed to start all MCP servers',
        { severity: 'error', requireInteraction: true }
      )
    }
  }

  const handleStopAll = async () => {
    try {
      await mcpApi.stopAll()
      setMessage({ type: 'success', text: 'All servers stopped successfully' })
      setTimeout(() => setMessage(null), 3000)
      loadMcpServers()
    } catch (error: any) {
      setMessage({ type: 'error', text: 'Failed to stop all servers' })
      
      // Send desktop notification only on error
      notificationService.notifyGeneric(
        'MCP Servers Stop Failed',
        error?.response?.data?.detail || 'Failed to stop all MCP servers',
        { severity: 'error', requireInteraction: true }
      )
    }
  }

  const handleViewLogs = async (serverName: string) => {
    try {
      const response = await mcpApi.getLogs(serverName)
      setLogsDialog({
        open: true,
        server: serverName,
        logs: response.data.logs || 'No logs available',
      })
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load logs' })
    }
  }

  const handleOpenIntegrationWizard = (integrationId: string) => {
    setSelectedIntegration(integrationId)
    setWizardOpen(true)
  }

  const handleSaveIntegration = async (integrationId: string, config: Record<string, any>) => {
    try {
      const updatedIntegrations = { ...integrationsConfig.integrations }
      updatedIntegrations[integrationId] = config

      const updatedEnabled = [...integrationsConfig.enabled_integrations]
      if (!updatedEnabled.includes(integrationId)) {
        updatedEnabled.push(integrationId)
      }

      await configApi.setIntegrations({
        enabled_integrations: updatedEnabled,
        integrations: updatedIntegrations,
      })

      setIntegrationsConfig({
        ...integrationsConfig,
        enabled_integrations: updatedEnabled,
        integrations: updatedIntegrations,
        configured: true,
      })

      setMessage({ type: 'success', text: `${integrationId} configured successfully` })
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      throw new Error('Failed to save integration configuration')
    }
  }

  const handleDisableIntegration = async (integrationId: string) => {
    try {
      const updatedEnabled = integrationsConfig.enabled_integrations.filter(
        (id) => id !== integrationId
      )

      await configApi.setIntegrations({
        enabled_integrations: updatedEnabled,
        integrations: integrationsConfig.integrations,
      })

      setIntegrationsConfig({
        ...integrationsConfig,
        enabled_integrations: updatedEnabled,
      })

      setMessage({ type: 'success', text: `${integrationId} disabled` })
      setTimeout(() => setMessage(null), 3000)
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to disable ${integrationId}` })
    }
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>

      {message && (
        <Alert severity={message.type} sx={{ mb: 2 }} onClose={() => setMessage(null)}>
          {message.text}
        </Alert>
      )}

      <Paper>
        <Tabs value={currentTab} onChange={(_, v) => setCurrentTab(v)} variant="scrollable" scrollButtons="auto">
          <Tab label="Claude API" />
          <Tab label="S3 Storage" />
          <Tab label="MCP Servers" />
          <Tab label="GitHub" />
          <Tab label="PostgreSQL" />
          <Tab label="Integrations" />
          <Tab label="General" />
        </Tabs>
        {/* Claude API Tab */}
        <TabPanel value={currentTab} index={0}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Claude API Configuration
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                {claudeConfig.configured ? '✓ API key is configured' : '⚠ API key not configured'}
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<HelpIcon />}
              onClick={() => setClaudeSetupDialogOpen(true)}
              sx={{ height: 'fit-content' }}
            >
              Setup Guide
            </Button>
          </Box>
          <TextField
            fullWidth
            label="API Key"
            type="password"
            value={claudeConfig.api_key}
            onChange={(e) => setClaudeConfig({ ...claudeConfig, api_key: e.target.value })}
            margin="normal"
            helperText="Your Anthropic API key for Claude"
          />
          <Button
            variant="contained"
            color="error"
            startIcon={<SaveIcon />}
            onClick={handleSaveClaude}
            sx={{ mt: 2 }}
          >
            Save
          </Button>
        </TabPanel>

        {/* S3 Storage Tab */}
        <TabPanel value={currentTab} index={1}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                S3 Storage Configuration
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Configure AWS S3 bucket access for storing and analyzing findings and cases
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<HelpIcon />}
              onClick={() => setS3SetupDialogOpen(true)}
              sx={{ height: 'fit-content' }}
            >
              Setup Guide
            </Button>
          </Box>
          <TextField
            fullWidth
            label="Bucket Name"
            value={s3Config.bucket_name}
            onChange={(e) => setS3Config({ ...s3Config, bucket_name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Region"
            value={s3Config.region}
            onChange={(e) => setS3Config({ ...s3Config, region: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Access Key ID"
            value={s3Config.access_key_id}
            onChange={(e) => setS3Config({ ...s3Config, access_key_id: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Secret Access Key"
            type="password"
            value={s3Config.secret_access_key}
            onChange={(e) => setS3Config({ ...s3Config, secret_access_key: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Findings Path"
            value={s3Config.findings_path}
            onChange={(e) => setS3Config({ ...s3Config, findings_path: e.target.value })}
            margin="normal"
            helperText="Path to findings file in S3 bucket"
          />
          <TextField
            fullWidth
            label="Cases Path"
            value={s3Config.cases_path}
            onChange={(e) => setS3Config({ ...s3Config, cases_path: e.target.value })}
            margin="normal"
            helperText="Path to cases file in S3 bucket"
          />
          <Button
            variant="contained"
            color="error"
            startIcon={<SaveIcon />}
            onClick={handleSaveS3}
            sx={{ mt: 2 }}
          >
            Save
          </Button>
        </TabPanel>

        {/* MCP Servers Tab */}
        <TabPanel value={currentTab} index={2}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6">
                MCP Server Management
              </Typography>
              <Typography variant="body2" color="textSecondary">
                Manage Model Context Protocol servers for DeepTempo integration
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadMcpServers}
              >
                Refresh
              </Button>
              <Button
                variant="outlined"
                color="success"
                startIcon={<StartIcon />}
                onClick={handleStartAll}
              >
                Start All
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<StopIcon />}
                onClick={handleStopAll}
              >
                Stop All
              </Button>
            </Box>
          </Box>

          {mcpServers.length === 0 ? (
            <Alert severity="info">
              No MCP servers configured. Configure integrations in the Integrations tab to enable MCP servers.
            </Alert>
          ) : (
            <Paper variant="outlined">
              <List>
                {mcpServers.map((serverName) => {
                  const status = mcpStatuses[serverName] || 'unknown'
                  const isRunning = status === 'running'
                  const isStdio = status.includes('stdio')
                  
                  return (
                    <ListItem
                      key={serverName}
                      divider
                      secondaryAction={
                        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                          <Tooltip title="View logs">
                            <IconButton
                              size="small"
                              onClick={() => handleViewLogs(serverName)}
                            >
                              <LogsIcon />
                            </IconButton>
                          </Tooltip>
                          <Button
                            size="small"
                            variant="outlined"
                            color="success"
                            startIcon={<StartIcon />}
                            onClick={() => handleMcpServerAction(serverName, 'start')}
                            disabled={isRunning || isStdio}
                          >
                            Start
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            color="error"
                            startIcon={<StopIcon />}
                            onClick={() => handleMcpServerAction(serverName, 'stop')}
                            disabled={!isRunning || isStdio}
                          >
                            Stop
                          </Button>
                        </Box>
                      }
                    >
                      <ListItemText
                        primary={
                          <Typography variant="subtitle1" component="div">
                            {serverName}
                          </Typography>
                        }
                        secondary={
                          <Box sx={{ mt: 0.5 }}>
                            <Chip
                              label={status}
                              color={isRunning ? 'success' : isStdio ? 'info' : 'default'}
                              size="small"
                            />
                            {isStdio && (
                              <Typography variant="caption" sx={{ ml: 1, color: 'text.secondary' }}>
                                (Managed by Claude Desktop)
                              </Typography>
                            )}
                          </Box>
                        }
                      />
                    </ListItem>
                  )
                })}
              </List>
            </Paper>
          )}

          {/* PostgreSQL MCP Server Configuration */}
          <Divider sx={{ my: 4 }} />
          <Box sx={{ mb: 2 }}>
            <Typography variant="h6" gutterBottom>
              PostgreSQL MCP Server (Claude Desktop Integration)
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Configure PostgreSQL MCP server (@modelcontextprotocol/server-postgres) for Claude Desktop to query databases
            </Typography>
          </Box>
          
          <Alert severity="info" sx={{ mb: 2 }}>
            <Typography variant="body2" gutterBottom>
              <strong>Note:</strong> This is for Claude Desktop integration only. 
              For the application's internal PostgreSQL database, see the <strong>PostgreSQL</strong> tab.
            </Typography>
          </Alert>

          <Card variant="outlined" sx={{ mb: 2 }}>
            <CardContent>
              <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 'bold' }}>
                PostgreSQL MCP Server Configuration
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                Connection string format: postgresql://user:password@host:port/database
              </Typography>
              <TextField
                fullWidth
                label="PostgreSQL Connection String"
                type="password"
                value={postgresqlConfig.connection_string}
                onChange={(e) => setPostgresqlConfig({ ...postgresqlConfig, connection_string: e.target.value })}
                margin="normal"
                placeholder="postgresql://deeptempo:password@localhost:5432/deeptempo_soc"
                helperText="Full connection string including credentials"
                size="small"
              />
              <Box sx={{ mt: 2, display: 'flex', gap: 1 }}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<SaveIcon />}
                  onClick={handleSavePostgreSQL}
                  size="small"
                >
                  Save Configuration
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<HelpIcon />}
                  onClick={() => setPostgresqlSetupDialogOpen(true)}
                  size="small"
                >
                  Setup Guide
                </Button>
              </Box>
            </CardContent>
          </Card>

          <Typography variant="caption" color="textSecondary" component="div" sx={{ mt: 1 }}>
            <strong>Connection String Examples:</strong>
            <ul style={{ marginTop: 4, marginBottom: 0 }}>
              <li>Local: <code>postgresql://deeptempo:password@localhost:5432/deeptempo_soc</code></li>
              <li>Remote: <code>postgresql://user:pass@db.example.com:5432/production</code></li>
              <li>With SSL: <code>postgresql://user:pass@host:5432/db?sslmode=require</code></li>
            </ul>
          </Typography>

          {/* Logs Dialog */}
          <Dialog
            open={logsDialog.open}
            onClose={() => setLogsDialog({ ...logsDialog, open: false })}
            maxWidth="md"
            fullWidth
          >
            <DialogTitle>
              Server Logs: {logsDialog.server}
            </DialogTitle>
            <DialogContent>
              <Box
                component="pre"
                sx={{
                  bgcolor: 'background.default',
                  p: 2,
                  borderRadius: 1,
                  overflow: 'auto',
                  maxHeight: 400,
                  fontSize: '0.875rem',
                  fontFamily: 'monospace',
                }}
              >
                {logsDialog.logs}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setLogsDialog({ ...logsDialog, open: false })}>
                Close
              </Button>
            </DialogActions>
          </Dialog>
        </TabPanel>

        {/* S3 Setup Guide Dialog */}
        <Dialog
          open={s3SetupDialogOpen}
          onClose={() => setS3SetupDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HelpIcon color="error" />
              <Typography variant="h6">Setup Your S3 Bucket Correctly</Typography>
            </Box>
          </DialogTitle>
          <DialogContent dividers>
            <Typography variant="h6" gutterBottom sx={{ mt: 1 }}>
              Prerequisites
            </Typography>
            <Typography variant="body2" paragraph>
              • An active AWS account<br />
              • AWS CLI installed (optional but recommended)<br />
              • Basic understanding of AWS IAM and S3
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 1: Create S3 Bucket
            </Typography>
            <Typography variant="body2" paragraph>
              1. Sign in to the AWS Management Console<br />
              2. Navigate to S3 service<br />
              3. Click "Create bucket"<br />
              4. Enter a unique bucket name (e.g., "deeptempo-soc-findings")<br />
              5. Select your preferred AWS region<br />
              6. Keep "Block all public access" enabled for security<br />
              7. Enable versioning (recommended for data protection)<br />
              8. Click "Create bucket"
            </Typography>

            <Alert severity="info" sx={{ mb: 2 }}>
              <strong>Bucket Naming Rules:</strong> Must be globally unique, 3-63 characters, lowercase, 
              can contain hyphens but not underscores, and must not be formatted as an IP address.
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 2: Create IAM User for DeepTempo
            </Typography>
            <Typography variant="body2" paragraph>
              1. Navigate to IAM service in AWS Console<br />
              2. Click "Users" → "Add users"<br />
              3. Enter username (e.g., "deeptempo-s3-access")<br />
              4. Select "Programmatic access" for access type<br />
              5. Click "Next: Permissions"
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 3: Set IAM Permissions
            </Typography>
            <Typography variant="body2" paragraph>
              1. Select "Attach existing policies directly"<br />
              2. Click "Create policy" (opens in new tab)<br />
              3. Switch to JSON editor and paste the policy below:<br />
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
{`{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR-BUCKET-NAME/*",
        "arn:aws:s3:::YOUR-BUCKET-NAME"
      ]
    }
  ]
}`}
            </Box>
            <Typography variant="body2" paragraph>
              4. Replace "YOUR-BUCKET-NAME" with your actual bucket name<br />
              5. Click "Review policy"<br />
              6. Name it "DeepTempoS3Access"<br />
              7. Click "Create policy"<br />
              8. Go back to the user creation tab, refresh policies, and attach "DeepTempoS3Access"<br />
              9. Click "Next" through the remaining steps<br />
              10. Click "Create user"
            </Typography>

            <Alert severity="warning" sx={{ mb: 2 }}>
              <strong>Important:</strong> Save the Access Key ID and Secret Access Key immediately! 
              AWS will only show the secret key once. Store them securely.
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 4: Configure CORS (if using browser-based uploads)
            </Typography>
            <Typography variant="body2" paragraph>
              1. Go to your S3 bucket<br />
              2. Click "Permissions" tab<br />
              3. Scroll to "Cross-origin resource sharing (CORS)"<br />
              4. Click "Edit" and add:
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
{`[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": ["*"],
    "ExposeHeaders": ["ETag"]
  }
]`}
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 5: Initialize Bucket Structure
            </Typography>
            <Typography variant="body2" paragraph>
              Create initial files in your bucket (you can upload empty JSON files):<br />
              • findings.json - Initialize with: {`{}`}<br />
              • cases.json - Initialize with: {`{}`}<br />
              <br />
              Or use AWS CLI:
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
{`echo '{}' > findings.json
echo '{}' > cases.json
aws s3 cp findings.json s3://YOUR-BUCKET-NAME/findings.json
aws s3 cp cases.json s3://YOUR-BUCKET-NAME/cases.json`}
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 6: Configure DeepTempo
            </Typography>
            <Typography variant="body2" paragraph>
              Now enter the following information in the fields above:<br />
              • <strong>Bucket Name:</strong> Your S3 bucket name<br />
              • <strong>Region:</strong> AWS region where bucket was created (e.g., us-east-1)<br />
              • <strong>Access Key ID:</strong> From Step 3<br />
              • <strong>Secret Access Key:</strong> From Step 3<br />
              • <strong>Findings Path:</strong> findings.json (or your custom path)<br />
              • <strong>Cases Path:</strong> cases.json (or your custom path)<br />
            </Typography>

            <Alert severity="success" sx={{ mb: 2 }}>
              <strong>Best Practices:</strong><br />
              • Enable S3 bucket versioning for data protection<br />
              • Enable S3 server-side encryption (AES-256 or KMS)<br />
              • Set up lifecycle policies for old versions<br />
              • Monitor bucket access with AWS CloudTrail<br />
              • Use least-privilege IAM policies<br />
              • Regularly rotate access keys
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Troubleshooting
            </Typography>
            <Typography variant="body2" component="div">
              <strong>Access Denied Errors:</strong><br />
              • Verify IAM policy includes correct bucket name<br />
              • Check bucket policy doesn't block access<br />
              • Ensure credentials are correct<br />
              <br />
              <strong>Connection Issues:</strong><br />
              • Verify region matches bucket location<br />
              • Check network/firewall settings<br />
              • Ensure AWS service is not experiencing outages<br />
              <br />
              <strong>File Not Found:</strong><br />
              • Verify file paths match exactly (case-sensitive)<br />
              • Check files exist in bucket<br />
              • Ensure proper file permissions
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setS3SetupDialogOpen(false)} variant="contained" color="error">
              Got It!
            </Button>
          </DialogActions>
        </Dialog>

        {/* Claude Setup Guide Dialog */}
        <Dialog
          open={claudeSetupDialogOpen}
          onClose={() => setClaudeSetupDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HelpIcon color="primary" />
              <Typography variant="h6">Setup Claude API Access</Typography>
            </Box>
          </DialogTitle>
          <DialogContent dividers>
            <Typography variant="h6" gutterBottom sx={{ mt: 1 }}>
              What is Claude?
            </Typography>
            <Typography variant="body2" paragraph>
              Claude is an AI assistant created by Anthropic. DeepTempo uses Claude's advanced language understanding 
              capabilities to analyze security findings, provide intelligent recommendations, and assist with SOC operations.
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 1: Create an Anthropic Account
            </Typography>
            <Typography variant="body2" paragraph>
              1. Visit <strong>https://console.anthropic.com</strong><br />
              2. Click "Sign Up" in the top right corner<br />
              3. Enter your email address and create a password<br />
              4. Verify your email address by clicking the link in the confirmation email<br />
              5. Complete your profile setup
            </Typography>

            <Alert severity="info" sx={{ mb: 2 }}>
              <strong>Note:</strong> You may need to add billing information to access the API. 
              Anthropic offers various pricing tiers including pay-as-you-go options.
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 2: Generate API Key
            </Typography>
            <Typography variant="body2" paragraph>
              1. Log in to the Anthropic Console<br />
              2. Navigate to "API Keys" from the left sidebar or settings<br />
              3. Click "Create Key" or "New API Key"<br />
              4. Give your key a descriptive name (e.g., "DeepTempo SOC")<br />
              5. Copy the generated API key immediately (it won't be shown again)
            </Typography>

            <Alert severity="warning" sx={{ mb: 2 }}>
              <strong>Important:</strong> Store your API key securely! It provides access to your Anthropic account. 
              Never share it publicly or commit it to version control.
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 3: Configure DeepTempo
            </Typography>
            <Typography variant="body2" paragraph>
              1. Paste your API key in the "API Key" field above<br />
              2. Click "Save"<br />
              3. DeepTempo will validate your key and confirm successful configuration<br />
              4. You can now use Claude's AI capabilities throughout the application
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              API Key Format
            </Typography>
            <Typography variant="body2" paragraph>
              Claude API keys typically start with "sk-ant-" followed by a long string of characters.
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
              sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            </Box>

            <Alert severity="success" sx={{ mb: 2 }}>
              <strong>Best Practices:</strong><br />
              • Use separate API keys for different environments (dev/prod)<br />
              • Rotate API keys regularly for security<br />
              • Monitor your API usage in the Anthropic Console<br />
              • Set up usage limits to control costs<br />
              • Keep your API keys in secure secret management systems
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Troubleshooting
            </Typography>
            <Typography variant="body2" component="div">
              <strong>Invalid API Key Error:</strong><br />
              • Verify you copied the complete key without spaces<br />
              • Ensure the key hasn't been revoked or expired<br />
              • Check you're using a production API key, not a test key<br />
              <br />
              <strong>Rate Limit Errors:</strong><br />
              • Check your usage tier in Anthropic Console<br />
              • Consider upgrading your plan for higher limits<br />
              • Implement rate limiting in your application<br />
              <br />
              <strong>Billing Issues:</strong><br />
              • Verify your payment method is valid<br />
              • Check your account balance<br />
              • Review usage in the Anthropic Console
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button 
              href="https://console.anthropic.com" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Open Anthropic Console
            </Button>
            <Button onClick={() => setClaudeSetupDialogOpen(false)} variant="contained">
              Got It!
            </Button>
          </DialogActions>
        </Dialog>

        {/* GitHub Setup Guide Dialog */}
        <Dialog
          open={githubSetupDialogOpen}
          onClose={() => setGithubSetupDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HelpIcon color="primary" />
              <Typography variant="h6">Setup GitHub Personal Access Token</Typography>
            </Box>
          </DialogTitle>
          <DialogContent dividers>
            <Typography variant="h6" gutterBottom sx={{ mt: 1 }}>
              What is the GitHub MCP Server?
            </Typography>
            <Typography variant="body2" paragraph>
              The GitHub MCP (Model Context Protocol) server is a community integration 
              (@modelcontextprotocol/server-github) that provides Claude with access to GitHub APIs. 
              This allows DeepTempo to interact with repositories, issues, pull requests, and more.
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 1: Navigate to GitHub Settings
            </Typography>
            <Typography variant="body2" paragraph>
              1. Log in to GitHub at <strong>https://github.com</strong><br />
              2. Click your profile picture in the top right<br />
              3. Select "Settings" from the dropdown menu<br />
              4. Scroll down and click "Developer settings" in the left sidebar<br />
              5. Click "Personal access tokens" → "Tokens (classic)"
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 2: Generate New Token
            </Typography>
            <Typography variant="body2" paragraph>
              1. Click "Generate new token" → "Generate new token (classic)"<br />
              2. Enter a descriptive note (e.g., "DeepTempo SOC Integration")<br />
              3. Set expiration (recommended: 90 days, then rotate)<br />
              4. Select the required scopes (see below)
            </Typography>

            <Alert severity="info" sx={{ mb: 2 }}>
              <strong>Token Types:</strong> Use "classic" tokens for broader compatibility. 
              Fine-grained tokens offer more granular control but require additional configuration.
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 3: Select Required Scopes
            </Typography>
            <Typography variant="body2" paragraph>
              Select the following scopes for DeepTempo functionality:
            </Typography>
            <Typography variant="body2" component="div">
              <ul>
                <li><strong>repo</strong> - Full control of private repositories
                  <ul>
                    <li>Allows reading repository contents, commits, and branches</li>
                    <li>Required for accessing organization repositories</li>
                  </ul>
                </li>
                <li><strong>read:org</strong> - Read organization and team membership
                  <ul>
                    <li>Enables reading organization data</li>
                    <li>Required for accessing organization repositories</li>
                  </ul>
                </li>
                <li><strong>read:user</strong> - Read user profile data
                  <ul>
                    <li>Allows reading user profile information</li>
                    <li>Useful for attribution and user-specific data</li>
                  </ul>
                </li>
              </ul>
            </Typography>

            <Alert severity="warning" sx={{ mb: 2 }}>
              <strong>Security Note:</strong> Only grant the minimum permissions needed. 
              The repo scope provides full access to private repositories, so protect this token carefully.
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 4: Generate and Copy Token
            </Typography>
            <Typography variant="body2" paragraph>
              1. Scroll to the bottom and click "Generate token"<br />
              2. Copy the token immediately (it starts with "ghp_")<br />
              3. Store it securely - you won't be able to see it again!
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 5: Configure DeepTempo
            </Typography>
            <Typography variant="body2" paragraph>
              1. Paste your token in the "GitHub Personal Access Token" field above<br />
              2. Click "Save"<br />
              3. DeepTempo will configure the GitHub MCP server<br />
              4. The server will start automatically when needed
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              What Can You Do With GitHub Integration?
            </Typography>
            <Typography variant="body2" component="div">
              Once configured, Claude (via DeepTempo) can:
              <ul>
                <li>Search repositories for security-related code</li>
                <li>Read file contents and analyze code</li>
                <li>Review commit history and changes</li>
                <li>Access issues and pull requests</li>
                <li>List repository branches and tags</li>
                <li>Read repository metadata and settings</li>
              </ul>
            </Typography>

            <Alert severity="success" sx={{ mb: 2 }}>
              <strong>Best Practices:</strong><br />
              • Use separate tokens for different applications<br />
              • Set expiration dates and rotate tokens regularly<br />
              • Revoke tokens immediately if compromised<br />
              • Never commit tokens to version control<br />
              • Use secrets management for production deployments<br />
              • Audit token usage in GitHub Settings
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Troubleshooting
            </Typography>
            <Typography variant="body2" component="div">
              <strong>Invalid Token Error:</strong><br />
              • Verify you copied the complete token<br />
              • Check token hasn't expired<br />
              • Ensure token wasn't revoked<br />
              <br />
              <strong>Permission Denied:</strong><br />
              • Verify required scopes are enabled<br />
              • Check organization permissions if accessing org repos<br />
              • Confirm repository access permissions<br />
              <br />
              <strong>MCP Server Won't Start:</strong><br />
              • Check token is properly saved<br />
              • Review MCP server logs in the MCP Servers tab<br />
              • Verify GitHub API is accessible (not blocked by firewall)
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button 
              href="https://github.com/settings/tokens" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              Create Token
            </Button>
            <Button onClick={() => setGithubSetupDialogOpen(false)} variant="contained">
              Got It!
            </Button>
          </DialogActions>
        </Dialog>

        {/* PostgreSQL Setup Guide Dialog */}
        <Dialog
          open={postgresqlSetupDialogOpen}
          onClose={() => setPostgresqlSetupDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HelpIcon color="primary" />
              <Typography variant="h6">Setup PostgreSQL Database Connection</Typography>
            </Box>
          </DialogTitle>
          <DialogContent dividers>
            <Typography variant="h6" gutterBottom sx={{ mt: 1 }}>
              What is the PostgreSQL MCP Server?
            </Typography>
            <Typography variant="body2" paragraph>
              The PostgreSQL MCP server (@modelcontextprotocol/server-postgres) is a community integration 
              that allows Claude to query and analyze data in PostgreSQL databases. This is useful for 
              security data stored in databases, log analysis, and threat intelligence repositories.
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Prerequisites
            </Typography>
            <Typography variant="body2" paragraph>
              • A PostgreSQL server (local or remote)<br />
              • Database credentials with appropriate permissions<br />
              • Network connectivity to the database server<br />
              • PostgreSQL version 10 or higher recommended
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Option 1: Use Existing PostgreSQL Server
            </Typography>
            <Typography variant="body2" paragraph>
              If you already have a PostgreSQL server, you just need the connection string. 
              Skip to Step 3 below.
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Option 2: Install PostgreSQL with Docker
            </Typography>
            <Typography variant="body2" paragraph>
              Quick setup using Docker for testing:
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
{`docker run -d \\
  --name deeptempo-postgres \\
  -e POSTGRES_PASSWORD=mysecretpassword \\
  -e POSTGRES_DB=security_data \\
  -p 5432:5432 \\
  postgres:15`}
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Option 3: Install PostgreSQL Locally
            </Typography>
            <Typography variant="body2" paragraph>
              <strong>macOS (using Homebrew):</strong>
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
{`brew install postgresql@15
brew services start postgresql@15`}
            </Box>
            <Typography variant="body2" paragraph>
              <strong>Ubuntu/Debian:</strong>
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
{`sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql`}
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 3: Create Database User (Optional but Recommended)
            </Typography>
            <Typography variant="body2" paragraph>
              Create a dedicated user for DeepTempo:
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
{`# Connect to PostgreSQL as superuser
psql -U postgres

# Create user and database
CREATE USER deeptempo_user WITH PASSWORD 'secure_password';
CREATE DATABASE security_data OWNER deeptempo_user;
GRANT ALL PRIVILEGES ON DATABASE security_data TO deeptempo_user;

# Exit
\\q`}
            </Box>

            <Alert severity="warning" sx={{ mb: 2 }}>
              <strong>Security:</strong> Use strong passwords and avoid using the postgres superuser account 
              for applications. Create dedicated users with only the permissions they need.
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 4: Build Connection String
            </Typography>
            <Typography variant="body2" paragraph>
              PostgreSQL connection strings follow this format:
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
postgresql://username:password@hostname:port/database
            </Box>
            <Typography variant="body2" paragraph>
              <strong>Examples:</strong>
            </Typography>
            <Typography variant="body2" component="div">
              <ul>
                <li><strong>Local:</strong> postgresql://deeptempo_user:password@localhost:5432/security_data</li>
                <li><strong>Remote:</strong> postgresql://user:pass@db.example.com:5432/production</li>
                <li><strong>With SSL:</strong> postgresql://user:pass@host:5432/db?sslmode=require</li>
                <li><strong>AWS RDS:</strong> postgresql://user:pass@instance.region.rds.amazonaws.com:5432/db</li>
              </ul>
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 5: Test Connection
            </Typography>
            <Typography variant="body2" paragraph>
              Test your connection string using psql:
            </Typography>
            <Box
              component="pre"
              sx={{
                bgcolor: 'background.default',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                fontSize: '0.75rem',
                fontFamily: 'monospace',
                mb: 2,
              }}
            >
psql "postgresql://user:password@localhost:5432/database"
            </Box>
            <Typography variant="body2" paragraph>
              If you can connect and see the database prompt, your connection string is correct.
            </Typography>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Step 6: Configure DeepTempo
            </Typography>
            <Typography variant="body2" paragraph>
              1. Enter your complete connection string in the field above<br />
              2. Click "Save"<br />
              3. DeepTempo will configure the PostgreSQL MCP server<br />
              4. Claude can now query your database when needed
            </Typography>

            <Alert severity="info" sx={{ mb: 2 }}>
              <strong>SSL/TLS:</strong> For production databases, append ?sslmode=require to enable SSL. 
              Options include: disable, allow, prefer, require, verify-ca, verify-full
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              What Can Claude Do With Database Access?
            </Typography>
            <Typography variant="body2" component="div">
              Once configured, Claude can:
              <ul>
                <li>Query security logs and events</li>
                <li>Analyze patterns in threat intelligence data</li>
                <li>Join data across multiple tables</li>
                <li>Generate statistics and aggregations</li>
                <li>Search for indicators of compromise</li>
                <li>Export data for further analysis</li>
              </ul>
            </Typography>

            <Alert severity="success" sx={{ mb: 2 }}>
              <strong>Best Practices:</strong><br />
              • Use read-only users if Claude only needs to query data<br />
              • Enable SSL/TLS for connections to remote databases<br />
              • Use strong, unique passwords<br />
              • Limit database user permissions (principle of least privilege)<br />
              • Monitor database access logs<br />
              • Keep PostgreSQL updated for security patches<br />
              • Use connection pooling for production deployments
            </Alert>

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Troubleshooting
            </Typography>
            <Typography variant="body2" component="div">
              <strong>Connection Refused:</strong><br />
              • Verify PostgreSQL is running: sudo systemctl status postgresql<br />
              • Check hostname and port are correct<br />
              • Ensure pg_hba.conf allows connections from your IP<br />
              • Check firewall allows port 5432<br />
              <br />
              <strong>Authentication Failed:</strong><br />
              • Verify username and password are correct<br />
              • Check pg_hba.conf authentication method<br />
              • Ensure user has database access permissions<br />
              <br />
              <strong>SSL Errors:</strong><br />
              • Try sslmode=disable for testing locally<br />
              • Use sslmode=require for remote connections<br />
              • Check server SSL certificate is valid<br />
              <br />
              <strong>Database Not Found:</strong><br />
              • Verify database name is correct (case-sensitive)<br />
              • Check database exists: psql -U postgres -l<br />
              • Ensure user has access to the database
            </Typography>
          </DialogContent>
          <DialogActions>
            <Button 
              href="https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              PostgreSQL Docs
            </Button>
            <Button onClick={() => setPostgresqlSetupDialogOpen(false)} variant="contained">
              Got It!
            </Button>
          </DialogActions>
        </Dialog>

        {/* GitHub Tab */}
        <TabPanel value={currentTab} index={3}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                GitHub Configuration (Community Server)
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                {githubConfig.configured ? '✓ GitHub token is configured' : '⚠ GitHub token not configured'}
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<HelpIcon />}
              onClick={() => setGithubSetupDialogOpen(true)}
              sx={{ height: 'fit-content' }}
            >
              Setup Guide
            </Button>
          </Box>
          <Alert severity="info" sx={{ mb: 2 }}>
            The GitHub MCP server is a community server (@modelcontextprotocol/server-github) that provides access to GitHub APIs.
            You need to create a Personal Access Token with repo, read:org, and read:user scopes.
          </Alert>
          <TextField
            fullWidth
            label="GitHub Personal Access Token"
            type="password"
            value={githubConfig.token}
            onChange={(e) => setGithubConfig({ ...githubConfig, token: e.target.value })}
            margin="normal"
            placeholder="ghp_your_token_here"
            helperText="Create at: https://github.com/settings/tokens"
          />
          <Button
            variant="contained"
            color="error"
            startIcon={<SaveIcon />}
            onClick={handleSaveGitHub}
            sx={{ mt: 2 }}
          >
            Save
          </Button>
          <Divider sx={{ my: 3 }} />
          <Typography variant="subtitle2" gutterBottom>
            Required Token Scopes:
          </Typography>
          <Typography variant="body2" component="div">
            <ul>
              <li><strong>repo</strong> - Full control of private repositories</li>
              <li><strong>read:org</strong> - Read org and team membership</li>
              <li><strong>read:user</strong> - Read user profile data</li>
            </ul>
          </Typography>
        </TabPanel>

        {/* PostgreSQL Tab */}
        <TabPanel value={currentTab} index={4}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                PostgreSQL Database Configuration
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                {storageStatus && (
                  <>
                    <Chip
                      label={storageStatus.backend === 'postgresql' ? 'PostgreSQL Active' : 'JSON Files Active'}
                      color={storageStatus.backend === 'postgresql' ? 'success' : 'warning'}
                      size="small"
                      icon={storageStatus.backend === 'postgresql' ? <CheckIcon /> : undefined}
                    />
                    {storageHealth && (
                      <Chip
                        label={`${storageHealth.findings_count} Findings, ${storageHealth.cases_count} Cases`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </>
                )}
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadStorageStatus}
                size="small"
              >
                Refresh
              </Button>
              <Button
                variant="contained"
                startIcon={<RefreshIcon />}
                onClick={handleReconnectDatabase}
                disabled={reconnecting}
                size="small"
                color="primary"
              >
                {reconnecting ? 'Reconnecting...' : 'Reconnect to PostgreSQL'}
              </Button>
              <Button
                variant="outlined"
                startIcon={<HelpIcon />}
                onClick={() => setPostgresqlSetupDialogOpen(true)}
                size="small"
              >
                Setup Guide
              </Button>
            </Box>
          </Box>

          {/* Current Status Card */}
          {storageStatus && (
            <Card sx={{ mb: 2 }}>
              <CardContent>
                <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                  Current Storage Backend
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          Backend Type
                        </Typography>
                        <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>
                          {storageStatus.backend}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          Status
                        </Typography>
                        <Typography variant="body1">
                          {storageStatus.database_available ? 
                            '✓ PostgreSQL Available' : 
                            '⚠ PostgreSQL Not Available'}
                        </Typography>
                      </Box>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="textSecondary">
                        {storageStatus.description}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
              </CardContent>
            </Card>
          )}

          {/* Recommendations */}
          {storageStatus && storageStatus.recommendations && storageStatus.recommendations.length > 0 && (
            <Alert severity={storageStatus.backend === 'postgresql' ? 'info' : 'warning'} sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                {storageStatus.recommendations[0].title}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                {storageStatus.recommendations[0].description}
              </Typography>
              <Typography variant="body2" sx={{ fontFamily: 'monospace', bgcolor: 'rgba(0,0,0,0.1)', p: 1, borderRadius: 1 }}>
                {storageStatus.recommendations[0].action}
              </Typography>
            </Alert>
          )}

          {/* PostgreSQL Setup Instructions */}
          {storageStatus && storageStatus.backend !== 'postgresql' && (
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Enable PostgreSQL for Production
              </Typography>
              <Typography variant="body2" component="div">
                <ol style={{ margin: 0, paddingLeft: '20px' }}>
                  <li>Start PostgreSQL: <code>./start_database.sh</code> (macOS/Linux) or <code>start_database.bat</code> (Windows)</li>
                  <li>The application will automatically detect and use PostgreSQL</li>
                  <li>No restart required - just refresh this page</li>
                </ol>
              </Typography>
            </Alert>
          )}

          {/* Documentation Links */}
          <Divider sx={{ my: 3 }} />
          <Typography variant="subtitle2" gutterBottom>
            Documentation:
          </Typography>
          <Typography variant="body2" component="div">
            <ul>
              <li><strong>Quick Start:</strong> See <code>GETTING_STARTED_WITH_POSTGRES.md</code></li>
              <li><strong>Full Setup:</strong> See <code>DATABASE_SETUP.md</code></li>
              <li><strong>Data Ingestion:</strong> See <code>DATA_INGESTION_GUIDE.md</code></li>
            </ul>
          </Typography>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
            <Typography variant="caption" color="textSecondary">
              <strong>Note:</strong> For Claude Desktop integration with PostgreSQL MCP server, 
              configure it in the <strong>MCP Servers</strong> tab instead.
            </Typography>
          </Box>
        </TabPanel>

        {/* Integrations Tab */}
        <TabPanel value={currentTab} index={5}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
            <Box>
              <Typography variant="h6" gutterBottom>
                Security Integrations
              </Typography>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Configure external security tools and services for enhanced threat intelligence
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setCustomIntegrationBuilderOpen(true)}
              sx={{ minWidth: '200px' }}
            >
              Build Custom Integration
            </Button>
          </Box>

          {/* Search Box */}
          <TextField
            fullWidth
            placeholder="Search integrations by name, description, or category..."
            value={integrationSearch}
            onChange={(e) => setIntegrationSearch(e.target.value)}
            margin="normal"
            sx={{ mt: 3, mb: 2 }}
            InputProps={{
              startAdornment: (
                <Box sx={{ mr: 1, display: 'flex', alignItems: 'center', color: 'text.secondary' }}>
                  <SearchIcon />
                </Box>
              ),
            }}
          />

          {/* Summary of enabled integrations */}
          <Box sx={{ mt: 3, mb: 3 }}>
            <Alert severity={integrationsConfig.enabled_integrations.length > 0 ? 'success' : 'info'}>
              <Typography variant="subtitle2" gutterBottom>
                Active Integrations: {integrationsConfig.enabled_integrations.length}
              </Typography>
              {integrationsConfig.enabled_integrations.length === 0 ? (
                <Typography variant="body2">
                  No integrations enabled yet. Configure your first integration below.
                </Typography>
              ) : (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {integrationsConfig.enabled_integrations.map((integrationId) => {
                    const integration = getAllIntegrations().find((i) => i.id === integrationId)
                    return (
                      <Chip
                        key={integrationId}
                        label={integration?.name || integrationId}
                        color="error"
                        size="small"
                        onDelete={() => handleDisableIntegration(integrationId)}
                      />
                    )
                  })}
                </Box>
              )}
            </Alert>
          </Box>

          <Divider sx={{ my: 3 }} />

          {/* No results message */}
          {integrationSearch.trim() && 
           INTEGRATION_CATEGORIES.every((category) => {
             const categoryIntegrations = getIntegrationsByCategory(category)
             const filteredIntegrations = categoryIntegrations.filter((integration) => {
               const searchLower = integrationSearch.toLowerCase()
               return (
                 integration.name.toLowerCase().includes(searchLower) ||
                 integration.description.toLowerCase().includes(searchLower) ||
                 integration.category.toLowerCase().includes(searchLower)
               )
             })
             return filteredIntegrations.length === 0
           }) && (
            <Alert severity="info">
              No integrations found matching "{integrationSearch}". Try a different search term.
            </Alert>
          )}

          {/* Integrations grouped by category */}
          {INTEGRATION_CATEGORIES.map((category) => {
            const categoryIntegrations = getIntegrationsByCategory(category)
            
            // Filter integrations based on search term
            const filteredIntegrations = integrationSearch.trim()
              ? categoryIntegrations.filter((integration) => {
                  const searchLower = integrationSearch.toLowerCase()
                  return (
                    integration.name.toLowerCase().includes(searchLower) ||
                    integration.description.toLowerCase().includes(searchLower) ||
                    integration.category.toLowerCase().includes(searchLower)
                  )
                })
              : categoryIntegrations
            
            // Skip category if no integrations match
            if (filteredIntegrations.length === 0) return null

            return (
              <Accordion key={category} defaultExpanded={integrationSearch.trim() !== '' || category === 'Threat Intelligence'}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">
                    {category}
                    <Chip
                      label={filteredIntegrations.length}
                      size="small"
                      sx={{ ml: 2 }}
                    />
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    {filteredIntegrations.map((integration) => {
                      const isEnabled = integrationsConfig.enabled_integrations.includes(
                        integration.id
                      )
                      const isConfigured = !!integrationsConfig.integrations[integration.id]

                      return (
                        <Grid item xs={12} sm={6} md={4} key={integration.id}>
                          <Card
                            variant="outlined"
                            sx={{
                              height: '100%',
                              display: 'flex',
                              flexDirection: 'column',
                              borderColor: isEnabled ? 'error.main' : undefined,
                              borderWidth: isEnabled ? 2 : 1,
                            }}
                          >
                            <CardContent sx={{ flexGrow: 1 }}>
                              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
                                <Typography variant="h6" component="div">
                                  {integration.name}
                                </Typography>
                                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                  {integration.has_ui && (
                                    <Tooltip title="Has dedicated UI page">
                                      <Chip 
                                        label="UI" 
                                        size="small" 
                                        color="primary" 
                                        sx={{ height: 20, fontSize: '0.65rem' }}
                                      />
                                    </Tooltip>
                                  )}
                                  {isEnabled && (
                                    <CheckIcon
                                      color="success"
                                      fontSize="small"
                                    />
                                  )}
                                </Box>
                              </Box>
                              {integration.functionality_type && (
                                <Chip 
                                  label={integration.functionality_type} 
                                  size="small" 
                                  variant="outlined"
                                  sx={{ mb: 1, height: 22, fontSize: '0.7rem' }}
                                />
                              )}
                              <Typography
                                variant="body2"
                                color="textSecondary"
                                sx={{ minHeight: 60 }}
                              >
                                {integration.description}
                              </Typography>
                            </CardContent>
                            <CardActions>
                              <Button
                                size="small"
                                variant={isConfigured ? 'outlined' : 'contained'}
                                startIcon={isConfigured ? <SettingsIcon /> : <AddIcon />}
                                onClick={() => handleOpenIntegrationWizard(integration.id)}
                              >
                                {isConfigured ? 'Reconfigure' : 'Setup'}
                              </Button>
                              {integration.docs_url && (
                                <Button
                                  size="small"
                                  href={integration.docs_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  Docs
                                </Button>
                              )}
                            </CardActions>
                          </Card>
                        </Grid>
                      )
                    })}
                  </Grid>
                </AccordionDetails>
              </Accordion>
            )
          })}

          {/* Integration Wizard Dialog */}
          {selectedIntegration && (
            <IntegrationWizard
              open={wizardOpen}
              onClose={() => setWizardOpen(false)}
              integration={getAllIntegrations().find((i) => i.id === selectedIntegration)!}
              onSave={handleSaveIntegration}
              existingConfig={integrationsConfig.integrations[selectedIntegration]}
            />
          )}

          {/* Custom Integration Builder */}
          {customIntegrationBuilderOpen && (
            <CustomIntegrationBuilder
              onClose={() => setCustomIntegrationBuilderOpen(false)}
              onSave={(integrationId) => {
                setCustomIntegrationBuilderOpen(false)
                setMessage({ type: 'success', text: `Custom integration '${integrationId}' created successfully! Configure it below.` })
                loadConfigs()
              }}
            />
          )}
        </TabPanel>

        {/* General Tab */}
        <TabPanel value={currentTab} index={6}>
          <Typography variant="h6" gutterBottom>
            General Settings
          </Typography>
          <Typography variant="body2" color="textSecondary" gutterBottom>
            Configure general application preferences
          </Typography>
          <FormGroup sx={{ mt: 3 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={generalConfig.auto_start_sync}
                  onChange={(e) => setGeneralConfig({ ...generalConfig, auto_start_sync: e.target.checked })}
                />
              }
              label="Start auto-sync on application start"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={generalConfig.show_notifications}
                  onChange={(e) => handleNotificationToggle(e.target.checked)}
                />
              }
              label="Show desktop notifications"
            />
            {notificationService.isSupported() && (
              <Box sx={{ ml: 4, mt: 1 }}>
                <Typography variant="caption" color="textSecondary">
                  {permissionGranted 
                    ? '✓ Browser permission granted' 
                    : '⚠ Browser permission not granted - will be requested when enabled'}
                </Typography>
                {generalConfig.show_notifications && permissionGranted && (
                  <Box sx={{ mt: 1 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={handleTestNotification}
                    >
                      Send Test Notification
                    </Button>
                  </Box>
                )}
              </Box>
            )}
            <FormControlLabel
              control={
                <Switch
                  checked={generalConfig.enable_keyring}
                  onChange={(e) => setGeneralConfig({ ...generalConfig, enable_keyring: e.target.checked })}
                />
              }
              label={
                <Box>
                  <Typography>Use OS Keyring for Secrets</Typography>
                  <Typography variant="caption" color="textSecondary">
                    Enable macOS Keychain / Windows Credential Manager (desktop only)
                  </Typography>
                </Box>
              }
            />
            <Box sx={{ ml: 4, mt: 1, mb: 2 }}>
              <Alert severity="info" sx={{ fontSize: '0.75rem' }}>
                <Typography variant="caption">
                  <strong>Note:</strong> By default, secrets are stored in <code>~/.deeptempo/.env</code> file.
                  Enable this only if you want to use your operating system's keyring (macOS Keychain, Windows Credential Manager).
                  For server deployments, leave this disabled to avoid permission prompts.
                </Typography>
              </Alert>
            </Box>
            {!notificationService.isSupported() && (
              <Box sx={{ ml: 4, mt: 1 }}>
                <Typography variant="caption" color="error">
                  ⚠ Your browser does not support desktop notifications
                </Typography>
              </Box>
            )}
          </FormGroup>
          <Divider sx={{ my: 3 }} />
          <Typography variant="subtitle1" gutterBottom>
            Theme
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={generalConfig.theme === 'dark'}
                onChange={(e) => setGeneralConfig({ ...generalConfig, theme: e.target.checked ? 'dark' : 'light' })}
              />
            }
            label="Dark Mode"
          />
          <Box sx={{ mt: 3 }}>
            <Button
              variant="contained"
              color="error"
              startIcon={<SaveIcon />}
              onClick={handleSaveGeneral}
            >
              Save
            </Button>
          </Box>
          <Divider sx={{ my: 3 }} />
          <Box>
            <Typography variant="subtitle1" gutterBottom>
              About
            </Typography>
            <Typography variant="body2" color="textSecondary">
              <strong>DeepTempo AI SOC</strong><br />
              Security Operations Center with AI-powered analysis<br />
              Version: 1.0.0
            </Typography>
          </Box>
        </TabPanel>
      </Paper>
    </Box>
  )
}
