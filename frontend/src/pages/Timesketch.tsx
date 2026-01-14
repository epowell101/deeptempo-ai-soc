import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  Tabs,
  Tab,
} from '@mui/material'
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Timeline as TimelineIcon,
  Launch as LaunchIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Search as SearchIcon,
} from '@mui/icons-material'
import { timesketchApi } from '../services/api'

interface Sketch {
  id: number
  name: string
  description: string
  created_at: string
  updated_at: string
  status: string
  user?: {
    username: string
  }
}

interface TimesketchStatus {
  configured: boolean
  connected: boolean
  message?: string
  error?: string
}

interface DockerStatus {
  docker_available: boolean
  daemon_running: boolean
  container_running: boolean
  error?: string
}

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

export default function Timesketch() {
  const [loading, setLoading] = useState(true)
  const [status, setStatus] = useState<TimesketchStatus | null>(null)
  const [dockerStatus, setDockerStatus] = useState<DockerStatus | null>(null)
  const [sketches, setSketches] = useState<Sketch[]>([])
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newSketch, setNewSketch] = useState({ name: '', description: '' })
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const [currentTab, setCurrentTab] = useState(0)
  const [dockerLoading, setDockerLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [statusRes, dockerRes] = await Promise.all([
        timesketchApi.getStatus(),
        timesketchApi.getDockerStatus(),
      ])

      setStatus(statusRes.data)
      setDockerStatus(dockerRes.data)

      if (statusRes.data.connected) {
        await loadSketches()
      }
    } catch (error) {
      console.error('Failed to load Timesketch data:', error)
      setMessage({
        type: 'error',
        text: 'Failed to load Timesketch data. Please check your configuration.',
      })
    } finally {
      setLoading(false)
    }
  }

  const loadSketches = async () => {
    try {
      const res = await timesketchApi.listSketches()
      setSketches(res.data.sketches || [])
    } catch (error) {
      console.error('Failed to load sketches:', error)
      setMessage({ type: 'error', text: 'Failed to load sketches' })
    }
  }

  const handleCreateSketch = async () => {
    if (!newSketch.name.trim()) {
      setMessage({ type: 'error', text: 'Sketch name is required' })
      return
    }

    try {
      await timesketchApi.createSketch(newSketch)
      setMessage({ type: 'success', text: 'Sketch created successfully' })
      setCreateDialogOpen(false)
      setNewSketch({ name: '', description: '' })
      await loadSketches()
    } catch (error) {
      console.error('Failed to create sketch:', error)
      setMessage({ type: 'error', text: 'Failed to create sketch' })
    }
  }

  const handleStartDocker = async () => {
    setDockerLoading(true)
    try {
      await timesketchApi.startDocker(5000)
      setMessage({ type: 'success', text: 'Timesketch Docker container starting...' })
      // Wait a bit then check status
      setTimeout(async () => {
        const res = await timesketchApi.getDockerStatus()
        setDockerStatus(res.data)
        setDockerLoading(false)
      }, 5000)
    } catch (error) {
      console.error('Failed to start Docker:', error)
      setMessage({ type: 'error', text: 'Failed to start Docker container' })
      setDockerLoading(false)
    }
  }

  const handleStopDocker = async () => {
    setDockerLoading(true)
    try {
      await timesketchApi.stopDocker()
      setMessage({ type: 'success', text: 'Timesketch Docker container stopped' })
      const res = await timesketchApi.getDockerStatus()
      setDockerStatus(res.data)
    } catch (error) {
      console.error('Failed to stop Docker:', error)
      setMessage({ type: 'error', text: 'Failed to stop Docker container' })
    } finally {
      setDockerLoading(false)
    }
  }

  const handleOpenSketch = (sketchId: number) => {
    if (status?.configured) {
      // Extract server URL from status or construct it
      const serverUrl = 'http://localhost:5000' // Default Docker URL
      window.open(`${serverUrl}/sketch/${sketchId}/`, '_blank')
    }
  }

  const getStatusColor = (connected: boolean) => {
    return connected ? 'success' : 'error'
  }

  const getStatusIcon = (connected: boolean) => {
    return connected ? <CheckCircleIcon /> : <ErrorIcon />
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Timesketch Timeline Analysis</Typography>
        <Box>
          <Button
            startIcon={<RefreshIcon />}
            onClick={loadData}
            sx={{ mr: 2 }}
          >
            Refresh
          </Button>
          {status?.connected && (
            <Button
              variant="contained"
              color="error"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              Create Sketch
            </Button>
          )}
        </Box>
      </Box>

      {message && (
        <Alert severity={message.type} onClose={() => setMessage(null)} sx={{ mb: 2 }}>
          {message.text}
        </Alert>
      )}

      {/* Status Overview */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Timesketch Server Status
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <Chip
                      icon={getStatusIcon(status?.connected || false)}
                      label={status?.connected ? 'Connected' : 'Disconnected'}
                      color={getStatusColor(status?.connected || false)}
                      size="small"
                    />
                    {!status?.configured && (
                      <Chip
                        icon={<WarningIcon />}
                        label="Not Configured"
                        color="warning"
                        size="small"
                        sx={{ ml: 1 }}
                      />
                    )}
                  </Box>
                  {status?.message && (
                    <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                      {status.message}
                    </Typography>
                  )}
                </Box>
                <TimelineIcon color="error" sx={{ fontSize: 48 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Docker Container Status
              </Typography>
              <Box display="flex" alignItems="center" mt={1} mb={2}>
                {dockerStatus?.docker_available ? (
                  <>
                    <Chip
                      icon={dockerStatus.daemon_running ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={dockerStatus.daemon_running ? 'Docker Running' : 'Docker Stopped'}
                      color={dockerStatus.daemon_running ? 'success' : 'error'}
                      size="small"
                    />
                    <Chip
                      icon={dockerStatus.container_running ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={dockerStatus.container_running ? 'Container Running' : 'Container Stopped'}
                      color={dockerStatus.container_running ? 'success' : 'default'}
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  </>
                ) : (
                  <Chip
                    icon={<ErrorIcon />}
                    label="Docker Not Available"
                    color="error"
                    size="small"
                  />
                )}
              </Box>
            </CardContent>
            <CardActions>
              {dockerStatus?.docker_available && dockerStatus.daemon_running && (
                <>
                  <Button
                    size="small"
                    startIcon={<PlayIcon />}
                    onClick={handleStartDocker}
                    disabled={dockerStatus.container_running || dockerLoading}
                  >
                    Start Container
                  </Button>
                  <Button
                    size="small"
                    startIcon={<StopIcon />}
                    onClick={handleStopDocker}
                    disabled={!dockerStatus.container_running || dockerLoading}
                  >
                    Stop Container
                  </Button>
                </>
              )}
            </CardActions>
          </Card>
        </Grid>
      </Grid>

      {!status?.configured && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Timesketch is not configured. Please go to Settings to configure your Timesketch server connection.
        </Alert>
      )}

      {/* Tabs */}
      {status?.connected && (
        <Paper sx={{ width: '100%' }}>
          <Tabs value={currentTab} onChange={(_, v) => setCurrentTab(v)}>
            <Tab label={`Sketches (${sketches.length})`} />
            <Tab label="About" />
          </Tabs>

          <TabPanel value={currentTab} index={0}>
            {/* Search Box */}
            <TextField
              fullWidth
              placeholder="Search sketches by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              sx={{ mb: 3 }}
              InputProps={{
                startAdornment: (
                  <Box sx={{ mr: 1, display: 'flex', alignItems: 'center', color: 'text.secondary' }}>
                    <SearchIcon />
                  </Box>
                ),
              }}
            />

            {/* Sketches List */}
            {(() => {
              const filteredSketches = searchQuery.trim()
                ? sketches.filter((sketch) => {
                    const query = searchQuery.toLowerCase()
                    return (
                      sketch.name.toLowerCase().includes(query) ||
                      sketch.description?.toLowerCase().includes(query)
                    )
                  })
                : sketches

              if (sketches.length === 0) {
                return (
                  <Box textAlign="center" py={4}>
                    <TimelineIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="textSecondary" gutterBottom>
                      No sketches found
                    </Typography>
                    <Typography variant="body2" color="textSecondary" mb={3}>
                      Create your first sketch to start analyzing timelines
                    </Typography>
                    <Button
                      variant="contained"
                      color="error"
                      startIcon={<AddIcon />}
                      onClick={() => setCreateDialogOpen(true)}
                    >
                      Create Sketch
                    </Button>
                  </Box>
                )
              }

              if (filteredSketches.length === 0) {
                return (
                  <Box textAlign="center" py={4}>
                    <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="textSecondary" gutterBottom>
                      No sketches match your search
                    </Typography>
                    <Typography variant="body2" color="textSecondary">
                      Try a different search term
                    </Typography>
                  </Box>
                )
              }

              return (
                <Grid container spacing={2}>
                  {filteredSketches.map((sketch) => (
                  <Grid item xs={12} sm={6} md={4} key={sketch.id}>
                    <Card>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {sketch.name}
                        </Typography>
                        <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                          {sketch.description || 'No description'}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          Created: {new Date(sketch.created_at).toLocaleDateString()}
                        </Typography>
                        {sketch.user && (
                          <Typography variant="caption" color="textSecondary" sx={{ display: 'block' }}>
                            By: {sketch.user.username}
                          </Typography>
                        )}
                      </CardContent>
                      <CardActions>
                        <Button
                          size="small"
                          startIcon={<LaunchIcon />}
                          onClick={() => handleOpenSketch(sketch.id)}
                        >
                          Open
                        </Button>
                      </CardActions>
                    </Card>
                    </Grid>
                  ))}
                </Grid>
              )
            })()}
          </TabPanel>

          <TabPanel value={currentTab} index={1}>
            <Typography variant="h6" gutterBottom>
              About Timesketch
            </Typography>
            <Typography variant="body1" paragraph>
              Timesketch is an open-source tool for collaborative forensic timeline analysis. It allows
              security analysts to visualize, search, and investigate event timelines from multiple sources.
            </Typography>
            <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
              Features
            </Typography>
            <ul>
              <li>
                <Typography variant="body1">Collaborative timeline analysis</Typography>
              </li>
              <li>
                <Typography variant="body1">Advanced search and filtering</Typography>
              </li>
              <li>
                <Typography variant="body1">Event tagging and commenting</Typography>
              </li>
              <li>
                <Typography variant="body1">Integration with DeepTempo findings and cases</Typography>
              </li>
              <li>
                <Typography variant="body1">Export capabilities for reporting</Typography>
              </li>
            </ul>
          </TabPanel>
        </Paper>
      )}

      {/* Create Sketch Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Sketch</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Sketch Name"
            fullWidth
            value={newSketch.name}
            onChange={(e) => setNewSketch({ ...newSketch, name: e.target.value })}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={3}
            value={newSketch.description}
            onChange={(e) => setNewSketch({ ...newSketch, description: e.target.value })}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateSketch} variant="contained" color="error">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

