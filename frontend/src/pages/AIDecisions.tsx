import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  LinearProgress,
  Stack,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material'
import {
  Feedback as FeedbackIcon,
  CheckCircle as CheckIcon,
  Refresh as RefreshIcon,
  Analytics as AnalyticsIcon,
  TrendingUp as TrendingUpIcon,
  Timer as TimerIcon,
} from '@mui/icons-material'
import { aiDecisionsApi } from '../services/api'
import AIDecisionFeedback from '../components/ai/AIDecisionFeedback'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index } = props
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

export default function AIDecisionsPage() {
  const [tabValue, setTabValue] = useState(0)
  const [loading, setLoading] = useState(false)
  const [pendingDecisions, setPendingDecisions] = useState<any[]>([])
  const [allDecisions, setAllDecisions] = useState<any[]>([])
  const [stats, setStats] = useState<any>(null)
  const [selectedDecision, setSelectedDecision] = useState<any>(null)
  const [feedbackDialogOpen, setFeedbackDialogOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Filters
  const [filterAgent, setFilterAgent] = useState<string>('all')
  const [filterFeedback, setFilterFeedback] = useState<string>('all')

  useEffect(() => {
    loadData()
  }, [filterAgent, filterFeedback])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Load pending feedback decisions
      const pendingResponse = await aiDecisionsApi.getPendingFeedback(50)
      setPendingDecisions(pendingResponse.data)

      // Load all decisions with filters
      const filters: any = { limit: 100 }
      if (filterAgent !== 'all') filters.agent_id = filterAgent
      if (filterFeedback === 'pending') filters.has_feedback = false
      if (filterFeedback === 'completed') filters.has_feedback = true
      
      const allResponse = await aiDecisionsApi.list(filters)
      setAllDecisions(allResponse.data)

      // Load stats
      const statsParams = filterAgent !== 'all' ? { agent_id: filterAgent } : {}
      const statsResponse = await aiDecisionsApi.getStats(statsParams)
      setStats(statsResponse.data)
      
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load AI decisions')
    } finally {
      setLoading(false)
    }
  }

  const handleProvideFeedback = (decision: any) => {
    setSelectedDecision(decision)
    setFeedbackDialogOpen(true)
  }

  const handleFeedbackSubmitted = () => {
    loadData() // Reload data after feedback
  }

  const getAgentDisplayName = (agentId: string) => {
    const agentNames: { [key: string]: string } = {
      triage: '🎯 Triage',
      investigation: '🔍 Investigation',
      threat_hunter: '🎣 Threat Hunter',
      correlation: '🔗 Correlation',
      auto_responder: '🤖 Auto-Response',
      reporting: '📊 Reporting',
      mitre_analyst: '🎭 MITRE',
      forensics: '🔬 Forensics',
      threat_intel: '🌐 Threat Intel',
      compliance: '📋 Compliance',
      malware_analyst: '🦠 Malware',
      network_analyst: '🌐 Network',
    }
    return agentNames[agentId] || agentId
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.85) return 'success'
    if (confidence >= 0.7) return 'warning'
    return 'error'
  }

  const formatDateTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const formatTimeSaved = (minutes: number) => {
    if (minutes < 60) return `${minutes}m`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" gutterBottom>
            AI Decision Feedback
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Review AI decisions and provide feedback for continuous improvement
          </Typography>
        </Box>
        <Button
          startIcon={<RefreshIcon />}
          onClick={loadData}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading && !stats && <CircularProgress />}

      {/* Stats Cards */}
      {stats && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" variant="caption">
                      Total Decisions
                    </Typography>
                    <Typography variant="h4">{stats.total_decisions}</Typography>
                  </Box>
                  <AnalyticsIcon color="primary" sx={{ fontSize: 40, opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" variant="caption">
                      Feedback Rate
                    </Typography>
                    <Typography variant="h4">
                      {(stats.feedback_rate * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <FeedbackIcon color="info" sx={{ fontSize: 40, opacity: 0.3 }} />
                </Box>
                <LinearProgress 
                  variant="determinate" 
                  value={stats.feedback_rate * 100} 
                  sx={{ mt: 1 }}
                />
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" variant="caption">
                      Agreement Rate
                    </Typography>
                    <Typography variant="h4">
                      {(stats.agreement_rate * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <TrendingUpIcon color="success" sx={{ fontSize: 40, opacity: 0.3 }} />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Avg Accuracy: {(stats.avg_accuracy_grade * 100).toFixed(0)}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="text.secondary" variant="caption">
                      Time Saved
                    </Typography>
                    <Typography variant="h4">
                      {stats.total_time_saved_hours.toFixed(1)}h
                    </Typography>
                  </Box>
                  <TimerIcon color="warning" sx={{ fontSize: 40, opacity: 0.3 }} />
                </Box>
                <Typography variant="caption" color="text.secondary">
                  Last {stats.period_days} days
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label={`Pending Feedback (${pendingDecisions.length})`} />
          <Tab label="All Decisions" />
          <Tab label="Analytics" />
        </Tabs>
      </Paper>

      {/* Pending Feedback Tab */}
      <TabPanel value={tabValue} index={0}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Decisions sorted by confidence (lowest first) - low confidence decisions benefit most from feedback
        </Typography>
        
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Agent</TableCell>
                <TableCell>Decision Type</TableCell>
                <TableCell>Confidence</TableCell>
                <TableCell>Recommended Action</TableCell>
                <TableCell>Timestamp</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {pendingDecisions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Box sx={{ py: 3 }}>
                      <CheckIcon color="success" sx={{ fontSize: 48, mb: 1 }} />
                      <Typography variant="body2" color="text.secondary">
                        No pending feedback - all decisions have been reviewed!
                      </Typography>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : (
                pendingDecisions.map((decision) => (
                  <TableRow key={decision.id} hover>
                    <TableCell>
                      <Chip 
                        label={getAgentDisplayName(decision.agent_id)} 
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip label={decision.decision_type} size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={`${(decision.confidence_score * 100).toFixed(0)}%`}
                        size="small"
                        color={getConfidenceColor(decision.confidence_score)}
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title={decision.recommended_action}>
                        <Typography variant="body2" noWrap sx={{ maxWidth: 300 }}>
                          {decision.recommended_action}
                        </Typography>
                      </Tooltip>
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {formatDateTime(decision.timestamp)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        variant="contained"
                        startIcon={<FeedbackIcon />}
                        onClick={() => handleProvideFeedback(decision)}
                      >
                        Provide Feedback
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* All Decisions Tab */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ mb: 2, display: 'flex', gap: 2 }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Agent</InputLabel>
            <Select
              value={filterAgent}
              onChange={(e) => setFilterAgent(e.target.value)}
              label="Agent"
            >
              <MenuItem value="all">All Agents</MenuItem>
              <MenuItem value="triage">Triage</MenuItem>
              <MenuItem value="investigation">Investigation</MenuItem>
              <MenuItem value="auto_responder">Auto-Response</MenuItem>
              <MenuItem value="threat_hunter">Threat Hunter</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Feedback Status</InputLabel>
            <Select
              value={filterFeedback}
              onChange={(e) => setFilterFeedback(e.target.value)}
              label="Feedback Status"
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="completed">Completed</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Agent</TableCell>
                <TableCell>Decision Type</TableCell>
                <TableCell>Confidence</TableCell>
                <TableCell>Human Decision</TableCell>
                <TableCell>Outcome</TableCell>
                <TableCell>Time Saved</TableCell>
                <TableCell>Timestamp</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {allDecisions.map((decision) => (
                <TableRow key={decision.id} hover>
                  <TableCell>
                    <Chip 
                      label={getAgentDisplayName(decision.agent_id)} 
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip label={decision.decision_type} size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={`${(decision.confidence_score * 100).toFixed(0)}%`}
                      size="small"
                      color={getConfidenceColor(decision.confidence_score)}
                    />
                  </TableCell>
                  <TableCell>
                    {decision.human_decision ? (
                      <Chip 
                        label={decision.human_decision}
                        size="small"
                        color={
                          decision.human_decision === 'agree' ? 'success' :
                          decision.human_decision === 'partial' ? 'warning' :
                          'error'
                        }
                      />
                    ) : (
                      <Chip label="Pending" size="small" variant="outlined" />
                    )}
                  </TableCell>
                  <TableCell>
                    {decision.actual_outcome ? (
                      <Chip 
                        label={decision.actual_outcome.replace('_', ' ')} 
                        size="small"
                        variant="outlined"
                      />
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell>
                    {decision.time_saved_minutes ? 
                      formatTimeSaved(decision.time_saved_minutes) : 
                      '-'
                    }
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {formatDateTime(decision.timestamp)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {!decision.human_decision && (
                      <IconButton
                        size="small"
                        onClick={() => handleProvideFeedback(decision)}
                      >
                        <FeedbackIcon fontSize="small" />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      {/* Analytics Tab */}
      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Outcome Distribution
              </Typography>
              {stats && Object.keys(stats.outcomes).length > 0 ? (
                <Stack spacing={2}>
                  {Object.entries(stats.outcomes).map(([outcome, count]: [string, any]) => (
                    <Box key={outcome}>
                      <Box display="flex" justifyContent="space-between" mb={0.5}>
                        <Typography variant="body2">
                          {outcome.replace('_', ' ').toUpperCase()}
                        </Typography>
                        <Typography variant="body2" fontWeight="bold">
                          {count}
                        </Typography>
                      </Box>
                      <LinearProgress 
                        variant="determinate"
                        value={(count / stats.total_with_feedback) * 100}
                      />
                    </Box>
                  ))}
                </Stack>
              ) : (
                <Alert severity="info">No outcome data available yet</Alert>
              )}
            </Paper>
          </Grid>

          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Performance Metrics
              </Typography>
              <Stack spacing={2}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Decisions per Day
                  </Typography>
                  <Typography variant="h4">
                    {stats ? Math.round(stats.total_decisions / stats.period_days) : 0}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Average Time Saved per Decision
                  </Typography>
                  <Typography variant="h4">
                    {stats && stats.total_decisions > 0 
                      ? Math.round(stats.total_time_saved_minutes / stats.total_decisions)
                      : 0}m
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Decisions Needing Review
                  </Typography>
                  <Typography variant="h4">
                    {stats ? stats.total_decisions - stats.total_with_feedback : 0}
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Feedback Dialog */}
      <AIDecisionFeedback
        open={feedbackDialogOpen}
        onClose={() => setFeedbackDialogOpen(false)}
        decision={selectedDecision}
        onFeedbackSubmitted={handleFeedbackSubmitted}
      />
    </Box>
  )
}

