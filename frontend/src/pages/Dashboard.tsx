import { useEffect, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import {
  Box,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Tabs,
  Tab,
  CircularProgress,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Snackbar,
  Alert,
  Tooltip,
  Switch,
  FormControlLabel,
} from '@mui/material'
import {
  Warning as WarningIcon,
  Folder as FolderIcon,
  Refresh as RefreshIcon,
  FileDownload as ExportIcon,
  Timeline as TimelineIcon,
  Search as SearchIcon,
} from '@mui/icons-material'
import { findingsApi, casesApi, configApi } from '../services/api'
import FindingsTable from '../components/findings/FindingsTable'
import CasesTable from '../components/cases/CasesTable'
import AttackChart from '../components/attack/AttackChart'
import ExportToTimesketchDialog from '../components/timesketch/ExportToTimesketchDialog'

interface LayoutContext {
  handleInvestigate: (findingId: string, agentId: string, prompt: string, title: string) => void
}

interface Stats {
  findings: any
  cases: any
}

export default function Dashboard() {
  const { handleInvestigate } = useOutletContext<LayoutContext>()
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentTab, setCurrentTab] = useState(0)
  const [filters, setFilters] = useState({
    severity: '',
    data_source: '',
    min_anomaly_score: '',
  })
  const [findingsSearch, setFindingsSearch] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })
  const [timesketchDialogOpen, setTimesketchDialogOpen] = useState(false)
  const [selectedFindingIds, setSelectedFindingIds] = useState<string[]>([])
  const [autoRefresh, setAutoRefresh] = useState(false)
  const [refreshInterval, setRefreshInterval] = useState(30)
  const [timesketchEnabled, setTimesketchEnabled] = useState(false)

  useEffect(() => {
    loadStats()
    checkTimesketchStatus()
  }, [])

  const checkTimesketchStatus = async () => {
    try {
      const response = await configApi.getIntegrations()
      const enabledIntegrations = response.data?.enabled_integrations || []
      setTimesketchEnabled(enabledIntegrations.includes('timesketch'))
    } catch (error) {
      console.error('Error checking Timesketch status:', error)
      setTimesketchEnabled(false)
    }
  }

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null
    
    if (autoRefresh) {
      intervalId = setInterval(() => {
        handleRefresh()
      }, refreshInterval * 1000)
    }
    
    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [autoRefresh, refreshInterval])

  const loadStats = async () => {
    try {
      const [findingsRes, casesRes] = await Promise.all([
        findingsApi.getSummary(),
        casesApi.getSummary(),
      ])

      setStats({
        findings: findingsRes.data,
        cases: casesRes.data,
      })
    } catch (error) {
      console.error('Failed to load stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
    loadStats()
  }

  const handleExport = async () => {
    try {
      const response = await findingsApi.export('json')
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `findings_export_${new Date().toISOString().split('T')[0]}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      setSnackbar({ open: true, message: 'Findings exported successfully', severity: 'success' })
    } catch (error) {
      console.error('Export failed:', error)
      setSnackbar({ open: true, message: 'Export failed. Check console for details.', severity: 'error' })
    }
  }

  const handleExportToTimesketch = async () => {
    try {
      const params: any = { ...filters }
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key]
        }
      })
      
      const response = await findingsApi.getAll(params)
      const findingIds = response.data.findings?.map((f: any) => f.finding_id) || []
      setSelectedFindingIds(findingIds)
      setTimesketchDialogOpen(true)
    } catch (error) {
      console.error('Failed to get findings:', error)
      setSnackbar({ open: true, message: 'Failed to prepare export', severity: 'error' })
    }
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
        <Typography variant="h4">Dashboard</Typography>
        <Box display="flex" alignItems="center" gap={2}>
          <Tooltip title={`Auto-refresh every ${refreshInterval} seconds`}>
            <FormControlLabel
              control={
                <Switch
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  color="error"
                />
              }
              label="Auto-refresh"
            />
          </Tooltip>
          {autoRefresh && (
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <Select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
              >
                <MenuItem value={10}>10s</MenuItem>
                <MenuItem value={30}>30s</MenuItem>
                <MenuItem value={60}>1m</MenuItem>
                <MenuItem value={300}>5m</MenuItem>
              </Select>
            </FormControl>
          )}
          <Tooltip title="Refresh all data from the backend">
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
            >
              Refresh
            </Button>
          </Tooltip>
          {timesketchEnabled && (
            <Tooltip title="Export filtered findings to Timesketch for timeline analysis">
              <Button
                variant="outlined"
                startIcon={<TimelineIcon />}
                onClick={handleExportToTimesketch}
              >
                Export to Timesketch
              </Button>
            </Tooltip>
          )}
          <Tooltip title="Download all findings as a JSON file">
            <Button
              variant="contained"
              color="error"
              startIcon={<ExportIcon />}
              onClick={handleExport}
            >
              Export JSON
            </Button>
          </Tooltip>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Total Findings
                  </Typography>
                  <Typography variant="h4">
                    {stats?.findings?.total || 0}
                  </Typography>
                </Box>
                <WarningIcon color="error" sx={{ fontSize: 48 }} />
              </Box>
              {stats?.findings?.by_severity && (
                <Box mt={2}>
                  <Typography variant="caption" color="error">
                    Critical: {stats.findings.by_severity.critical || 0}
                  </Typography>
                  <Typography variant="caption" color="warning" sx={{ ml: 2 }}>
                    High: {stats.findings.by_severity.high || 0}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Tooltip title="Click to view active cases">
            <Card 
              sx={{ cursor: 'pointer', '&:hover': { boxShadow: 4 } }}
              onClick={() => setCurrentTab(1)}
            >
              <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Box>
                    <Typography color="textSecondary" gutterBottom>
                      Active Cases
                    </Typography>
                    <Typography variant="h4">
                      {stats?.cases?.total || 0}
                    </Typography>
                  </Box>
                  <FolderIcon color="error" sx={{ fontSize: 48 }} />
                </Box>
                {stats?.cases?.by_status && (
                  <Box mt={2}>
                    <Typography variant="caption">
                      Open: {stats.cases.by_status.open || 0}
                    </Typography>
                    <Typography variant="caption" sx={{ ml: 2 }}>
                      In Progress: {stats.cases.by_status['in-progress'] || 0}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Tooltip>
        </Grid>
      </Grid>

      {/* Tabbed Content */}
      <Paper sx={{ width: '100%' }}>
        <Tabs value={currentTab} onChange={(_, v) => setCurrentTab(v)}>
          <Tab label="Findings" />
          <Tab label="Active Cases" />
          <Tab label="ATT&CK Overview" />
        </Tabs>

        <Box sx={{ p: 3 }}>
          {currentTab === 0 && (
            <>
              {/* Search and Filters */}
              <Paper sx={{ p: 2, mb: 3 }} elevation={0} variant="outlined">
                <Typography variant="h6" gutterBottom>
                  Search & Filters
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12}>
                    <TextField
                      fullWidth
                      placeholder="Search findings by ID, data source, or description..."
                      value={findingsSearch}
                      onChange={(e) => setFindingsSearch(e.target.value)}
                      InputProps={{
                        startAdornment: (
                          <Box sx={{ mr: 1, display: 'flex', alignItems: 'center', color: 'text.secondary' }}>
                            <SearchIcon />
                          </Box>
                        ),
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <FormControl fullWidth>
                      <InputLabel>Severity</InputLabel>
                      <Select
                        value={filters.severity}
                        label="Severity"
                        onChange={(e) =>
                          setFilters({ ...filters, severity: e.target.value })
                        }
                      >
                        <MenuItem value="">All</MenuItem>
                        <MenuItem value="critical">Critical</MenuItem>
                        <MenuItem value="high">High</MenuItem>
                        <MenuItem value="medium">Medium</MenuItem>
                        <MenuItem value="low">Low</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="Data Source"
                      value={filters.data_source}
                      onChange={(e) =>
                        setFilters({ ...filters, data_source: e.target.value })
                      }
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="Min Anomaly Score"
                      type="number"
                      value={filters.min_anomaly_score}
                      onChange={(e) =>
                        setFilters({ ...filters, min_anomaly_score: e.target.value })
                      }
                    />
                  </Grid>
                </Grid>
              </Paper>
              
              {/* Findings Table */}
              <FindingsTable filters={filters} searchQuery={findingsSearch} refreshKey={refreshKey} onInvestigate={handleInvestigate} />
            </>
          )}
          {currentTab === 1 && <CasesTable limit={10} />}
          {currentTab === 2 && <AttackChart />}
        </Box>
      </Paper>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Export to Timesketch Dialog */}
      <ExportToTimesketchDialog
        open={timesketchDialogOpen}
        onClose={() => setTimesketchDialogOpen(false)}
        findingIds={selectedFindingIds}
        defaultTimelineName={`Findings Export - ${new Date().toLocaleDateString()}`}
      />
    </Box>
  )
}

