import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Typography,
  Chip,
  Box,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Snackbar,
  Alert,
  Tabs,
  Tab,
  Paper,
  Card,
  CardContent,
  CardActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material'
import {
  Close as CloseIcon,
  Save as SaveIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  PictureAsPdf as PdfIcon,
  CheckCircle as ResolveIcon,
  Timeline as TimelineIcon,
} from '@mui/icons-material'
import { casesApi, findingsApi, configApi } from '../../services/api'
import ExportToTimesketchDialog from '../timesketch/ExportToTimesketchDialog'
import { notificationService } from '../../services/notifications'

interface CaseDetailDialogProps {
  open: boolean
  onClose: () => void
  caseId: string | null
  onUpdate?: () => void
}

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`case-tabpanel-${index}`}
      aria-labelledby={`case-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  )
}

export default function CaseDetailDialog({
  open,
  onClose,
  caseId,
  onUpdate,
}: CaseDetailDialogProps) {
  const [loading, setLoading] = useState(false)
  const [tabValue, setTabValue] = useState(0)
  const [caseData, setCaseData] = useState<any>(null)
  const [findings, setFindings] = useState<any[]>([])
  const [allFindings, setAllFindings] = useState<any[]>([])
  
  // Editing state
  const [editMode, setEditMode] = useState(false)
  const [editedCase, setEditedCase] = useState<any>(null)
  
  // Activity state
  const [newActivity, setNewActivity] = useState({
    activity_type: 'note',
    description: '',
  })
  
  // Resolution state
  const [newResolutionStep, setNewResolutionStep] = useState({
    description: '',
    action_taken: '',
    result: '',
  })
  
  // Findings management
  const [selectedFindingId, setSelectedFindingId] = useState('')
  
  const [snackbar, setSnackbar] = useState<{
    open: boolean
    message: string
    severity: 'success' | 'error'
  }>({
    open: false,
    message: '',
    severity: 'success',
  })
  
  const [timesketchDialogOpen, setTimesketchDialogOpen] = useState(false)
  const [timesketchEnabled, setTimesketchEnabled] = useState(false)

  useEffect(() => {
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
    checkTimesketchStatus()
  }, [])

  useEffect(() => {
    if (open && caseId) {
      loadCase()
      loadAllFindings()
    }
  }, [open, caseId])

  const loadCase = async () => {
    if (!caseId) return

    setLoading(true)
    try {
      const response = await casesApi.getById(caseId)
      setCaseData(response.data)
      setEditedCase(response.data)
      
      // Load associated findings
      const findingIds = response.data.finding_ids || []
      const findingsData = await Promise.all(
        findingIds.map(async (id: string) => {
          try {
            const resp = await findingsApi.getById(id)
            return resp.data
          } catch (error) {
            console.error(`Failed to load finding ${id}:`, error)
            return null
          }
        })
      )
      setFindings(findingsData.filter((f) => f !== null))
    } catch (error) {
      console.error('Failed to load case:', error)
      setSnackbar({
        open: true,
        message: 'Failed to load case',
        severity: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  const loadAllFindings = async () => {
    try {
      const response = await findingsApi.getAll({ limit: 100 })
      setAllFindings(response.data.findings || [])
    } catch (error) {
      console.error('Failed to load findings:', error)
    }
  }

  const handleSave = async () => {
    if (!caseId || !editedCase) return

    setLoading(true)
    try {
      await casesApi.update(caseId, {
        title: editedCase.title,
        description: editedCase.description,
        status: editedCase.status,
        priority: editedCase.priority,
        assignee: editedCase.assignee,
      })
      setCaseData(editedCase)
      setEditMode(false)
      setSnackbar({
        open: true,
        message: 'Case updated successfully',
        severity: 'success',
      })
      
      // Send desktop notification for case update
      notificationService.notifyCaseUpdate({
        case_id: caseId,
        title: editedCase.title,
        status: editedCase.status,
        priority: editedCase.priority,
        message: 'Case details updated successfully',
      })
      
      if (onUpdate) onUpdate()
    } catch (error) {
      console.error('Failed to update case:', error)
      setSnackbar({
        open: true,
        message: 'Failed to update case',
        severity: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleAddActivity = async () => {
    if (!caseId || !newActivity.description.trim()) return

    setLoading(true)
    try {
      await casesApi.addActivity(caseId, newActivity)
      setNewActivity({ activity_type: 'note', description: '' })
      await loadCase()
      setSnackbar({
        open: true,
        message: 'Activity added',
        severity: 'success',
      })
    } catch (error) {
      console.error('Failed to add activity:', error)
      setSnackbar({
        open: true,
        message: 'Failed to add activity',
        severity: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleAddResolutionStep = async () => {
    if (!caseId || !newResolutionStep.description.trim()) return

    setLoading(true)
    try {
      await casesApi.addResolutionStep(caseId, newResolutionStep)
      setNewResolutionStep({ description: '', action_taken: '', result: '' })
      await loadCase()
      setSnackbar({
        open: true,
        message: 'Resolution step added',
        severity: 'success',
      })
    } catch (error) {
      console.error('Failed to add resolution step:', error)
      setSnackbar({
        open: true,
        message: 'Failed to add resolution step',
        severity: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleAddFinding = async () => {
    if (!caseId || !selectedFindingId) return

    setLoading(true)
    try {
      await casesApi.addFinding(caseId, selectedFindingId)
      setSelectedFindingId('')
      await loadCase()
      setSnackbar({
        open: true,
        message: 'Finding added to case',
        severity: 'success',
      })
    } catch (error) {
      console.error('Failed to add finding:', error)
      setSnackbar({
        open: true,
        message: 'Failed to add finding',
        severity: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveFinding = async (findingId: string) => {
    if (!caseId) return

    setLoading(true)
    try {
      await casesApi.removeFinding(caseId, findingId)
      await loadCase()
      setSnackbar({
        open: true,
        message: 'Finding removed from case',
        severity: 'success',
      })
    } catch (error) {
      console.error('Failed to remove finding:', error)
      setSnackbar({
        open: true,
        message: 'Failed to remove finding',
        severity: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateReport = async () => {
    if (!caseId) return

    setLoading(true)
    try {
      const response = await casesApi.generateReport(caseId)
      setSnackbar({
        open: true,
        message: `Report generated: ${response.data.filename}`,
        severity: 'success',
      })
      
      // Send desktop notification for report generation
      if (caseData) {
        notificationService.notifyGeneric(
          'Report Generated',
          `PDF report for case "${caseData.title}" is ready: ${response.data.filename}`,
          { severity: 'success', requireInteraction: false }
        )
      }
    } catch (error: any) {
      console.error('Failed to generate report:', error)
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || 'Failed to generate report',
        severity: 'error',
      })
      
      // Send error notification
      if (caseData) {
        notificationService.notifyGeneric(
          'Report Generation Failed',
          `Failed to generate report for case "${caseData.title}"`,
          { severity: 'error', requireInteraction: false }
        )
      }
    } finally {
      setLoading(false)
    }
  }

  const handleResolveCase = async () => {
    if (!caseId) return

    setLoading(true)
    try {
      await casesApi.update(caseId, { status: 'resolved' })
      await loadCase()
      setSnackbar({
        open: true,
        message: 'Case marked as resolved',
        severity: 'success',
      })
      
      // Send desktop notification for case resolution
      if (caseData) {
        notificationService.notifyCaseUpdate({
          case_id: caseId,
          title: caseData.title,
          status: 'resolved',
          priority: caseData.priority,
          message: 'Case has been resolved',
        })
      }
      
      if (onUpdate) onUpdate()
    } catch (error) {
      console.error('Failed to resolve case:', error)
      setSnackbar({
        open: true,
        message: 'Failed to resolve case',
        severity: 'error',
      })
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: any = {
      open: 'info',
      'in-progress': 'warning',
      resolved: 'success',
      closed: 'default',
    }
    return colors[status?.toLowerCase()] || 'default'
  }

  const getPriorityColor = (priority: string) => {
    const colors: any = {
      critical: 'error',
      high: 'error',
      medium: 'warning',
      low: 'success',
    }
    return colors[priority?.toLowerCase()] || 'default'
  }

  if (!caseData && !loading) {
    return null
  }

  const displayCase = editMode ? editedCase : caseData
  const activities = displayCase?.activities || []
  const resolutionSteps = displayCase?.resolution_steps || []
  const timeline = displayCase?.timeline || []

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Box>
            <Typography variant="h6">
              {displayCase?.title || 'Case Details'}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              {displayCase?.case_id}
            </Typography>
          </Box>
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              startIcon={<PdfIcon />}
              onClick={handleGenerateReport}
              disabled={loading}
              size="small"
            >
              Generate Report
            </Button>
            {displayCase?.status !== 'resolved' && (
              <Button
                variant="outlined"
                color="success"
                startIcon={<ResolveIcon />}
                onClick={handleResolveCase}
                disabled={loading}
                size="small"
              >
                Resolve
              </Button>
            )}
            <IconButton onClick={onClose} size="small">
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 3 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Overview" />
          <Tab label={`Findings (${findings.length})`} />
          <Tab label={`Activities (${activities.length})`} />
          <Tab label={`Resolution (${resolutionSteps.length})`} />
        </Tabs>
      </Box>

      <DialogContent dividers sx={{ minHeight: '400px' }}>
        {loading && !caseData ? (
          <Typography>Loading...</Typography>
        ) : (
          <>
            {/* Overview Tab */}
            <TabPanel value={tabValue} index={0}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Case Information
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="textSecondary">
                          Title
                        </Typography>
                        {editMode ? (
                          <TextField
                            fullWidth
                            size="small"
                            value={editedCase.title || ''}
                            onChange={(e) =>
                              setEditedCase({ ...editedCase, title: e.target.value })
                            }
                          />
                        ) : (
                          <Typography variant="body1">
                            {displayCase.title || 'Untitled'}
                          </Typography>
                        )}
                      </Grid>

                      <Grid item xs={6}>
                        <Typography variant="subtitle2" color="textSecondary">
                          Status
                        </Typography>
                        {editMode ? (
                          <FormControl fullWidth size="small">
                            <Select
                              value={editedCase.status || 'open'}
                              onChange={(e) =>
                                setEditedCase({ ...editedCase, status: e.target.value })
                              }
                            >
                              <MenuItem value="open">Open</MenuItem>
                              <MenuItem value="in-progress">In Progress</MenuItem>
                              <MenuItem value="resolved">Resolved</MenuItem>
                              <MenuItem value="closed">Closed</MenuItem>
                            </Select>
                          </FormControl>
                        ) : (
                          <Chip
                            label={displayCase.status || 'Open'}
                            color={getStatusColor(displayCase.status)}
                            size="small"
                          />
                        )}
                      </Grid>

                      <Grid item xs={6}>
                        <Typography variant="subtitle2" color="textSecondary">
                          Priority
                        </Typography>
                        {editMode ? (
                          <FormControl fullWidth size="small">
                            <Select
                              value={editedCase.priority || 'medium'}
                              onChange={(e) =>
                                setEditedCase({
                                  ...editedCase,
                                  priority: e.target.value,
                                })
                              }
                            >
                              <MenuItem value="low">Low</MenuItem>
                              <MenuItem value="medium">Medium</MenuItem>
                              <MenuItem value="high">High</MenuItem>
                              <MenuItem value="critical">Critical</MenuItem>
                            </Select>
                          </FormControl>
                        ) : (
                          <Chip
                            label={displayCase.priority || 'Medium'}
                            color={getPriorityColor(displayCase.priority)}
                            size="small"
                          />
                        )}
                      </Grid>

                      <Grid item xs={6}>
                        <Typography variant="subtitle2" color="textSecondary">
                          Assignee
                        </Typography>
                        {editMode ? (
                          <TextField
                            fullWidth
                            size="small"
                            value={editedCase.assignee || ''}
                            onChange={(e) =>
                              setEditedCase({
                                ...editedCase,
                                assignee: e.target.value,
                              })
                            }
                            placeholder="Unassigned"
                          />
                        ) : (
                          <Typography variant="body1">
                            {displayCase.assignee || 'Unassigned'}
                          </Typography>
                        )}
                      </Grid>

                      <Grid item xs={6}>
                        <Typography variant="subtitle2" color="textSecondary">
                          Created
                        </Typography>
                        <Typography variant="body2">
                          {displayCase.created_at
                            ? new Date(displayCase.created_at).toLocaleString()
                            : 'N/A'}
                        </Typography>
                      </Grid>

                      <Grid item xs={12}>
                        <Typography variant="subtitle2" color="textSecondary">
                          Description
                        </Typography>
                        {editMode ? (
                          <TextField
                            fullWidth
                            multiline
                            rows={4}
                            value={editedCase.description || ''}
                            onChange={(e) =>
                              setEditedCase({
                                ...editedCase,
                                description: e.target.value,
                              })
                            }
                          />
                        ) : (
                          <Typography variant="body2">
                            {displayCase.description || 'No description'}
                          </Typography>
                        )}
                      </Grid>
                    </Grid>
                  </Paper>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Timeline
                    </Typography>
                    <List dense>
                      {timeline.map((event: any, index: number) => (
                        <ListItem key={index}>
                          <ListItemText
                            primary={event.event}
                            secondary={new Date(event.timestamp).toLocaleString()}
                          />
                        </ListItem>
                      ))}
                      {timeline.length === 0 && (
                        <Typography variant="body2" color="textSecondary">
                          No timeline events
                        </Typography>
                      )}
                    </List>
                  </Paper>
                </Grid>
              </Grid>
            </TabPanel>

            {/* Findings Tab */}
            <TabPanel value={tabValue} index={1}>
              <Box mb={3}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Add Finding to Case
                  </Typography>
                  <Box display="flex" gap={2}>
                    <FormControl fullWidth>
                      <InputLabel>Select Finding</InputLabel>
                      <Select
                        value={selectedFindingId}
                        label="Select Finding"
                        onChange={(e) => setSelectedFindingId(e.target.value)}
                      >
                        {allFindings
                          .filter(
                            (f) =>
                              !displayCase?.finding_ids?.includes(f.finding_id)
                          )
                          .map((finding) => (
                            <MenuItem
                              key={finding.finding_id}
                              value={finding.finding_id}
                            >
                              {finding.finding_id} - {finding.severity}
                            </MenuItem>
                          ))}
                      </Select>
                    </FormControl>
                    <Button
                      variant="contained"
                      color="error"
                      startIcon={<AddIcon />}
                      onClick={handleAddFinding}
                      disabled={!selectedFindingId || loading}
                    >
                      Add
                    </Button>
                  </Box>
                </Paper>
              </Box>

              <TableContainer component={Paper}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Finding ID</TableCell>
                      <TableCell>Severity</TableCell>
                      <TableCell>Data Source</TableCell>
                      <TableCell>Anomaly Score</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {findings.map((finding) => (
                      <TableRow key={finding.finding_id}>
                        <TableCell>{finding.finding_id}</TableCell>
                        <TableCell>
                          <Chip
                            label={finding.severity}
                            color={getPriorityColor(finding.severity)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>{finding.data_source}</TableCell>
                        <TableCell>
                          {finding.anomaly_score?.toFixed(3) || 'N/A'}
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => handleRemoveFinding(finding.finding_id)}
                            disabled={loading}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
              {findings.length === 0 && (
                <Typography variant="body2" color="textSecondary" sx={{ mt: 2 }}>
                  No findings associated with this case
                </Typography>
              )}
            </TabPanel>

            {/* Activities Tab */}
            <TabPanel value={tabValue} index={2}>
              <Box mb={3}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Add Activity
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={3}>
                      <FormControl fullWidth>
                        <InputLabel>Type</InputLabel>
                        <Select
                          value={newActivity.activity_type}
                          label="Type"
                          onChange={(e) =>
                            setNewActivity({
                              ...newActivity,
                              activity_type: e.target.value,
                            })
                          }
                        >
                          <MenuItem value="note">Note</MenuItem>
                          <MenuItem value="status_change">Status Change</MenuItem>
                          <MenuItem value="finding_added">Finding Added</MenuItem>
                          <MenuItem value="action_taken">Action Taken</MenuItem>
                          <MenuItem value="investigation">Investigation</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} md={7}>
                      <TextField
                        fullWidth
                        label="Description"
                        value={newActivity.description}
                        onChange={(e) =>
                          setNewActivity({
                            ...newActivity,
                            description: e.target.value,
                          })
                        }
                        multiline
                        rows={2}
                      />
                    </Grid>
                    <Grid item xs={12} md={2}>
                      <Button
                        fullWidth
                        variant="contained"
                        color="error"
                        startIcon={<AddIcon />}
                        onClick={handleAddActivity}
                        disabled={!newActivity.description.trim() || loading}
                        sx={{ height: '100%' }}
                      >
                        Add
                      </Button>
                    </Grid>
                  </Grid>
                </Paper>
              </Box>

              <List>
                {activities
                  .slice()
                  .reverse()
                  .map((activity: any, index: number) => (
                    <Card key={index} sx={{ mb: 2 }}>
                      <CardContent>
                        <Box display="flex" justifyContent="space-between">
                          <Box>
                            <Chip
                              label={activity.activity_type.replace('_', ' ')}
                              size="small"
                              color="error"
                              sx={{ mb: 1 }}
                            />
                            <Typography variant="body1">
                              {activity.description}
                            </Typography>
                          </Box>
                          <Typography variant="caption" color="textSecondary">
                            {new Date(activity.timestamp).toLocaleString()}
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                {activities.length === 0 && (
                  <Typography variant="body2" color="textSecondary">
                    No activities recorded
                  </Typography>
                )}
              </List>
            </TabPanel>

            {/* Resolution Tab */}
            <TabPanel value={tabValue} index={3}>
              <Box mb={3}>
                <Paper sx={{ p: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    Add Resolution Step
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Step Description"
                        value={newResolutionStep.description}
                        onChange={(e) =>
                          setNewResolutionStep({
                            ...newResolutionStep,
                            description: e.target.value,
                          })
                        }
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Action Taken"
                        value={newResolutionStep.action_taken}
                        onChange={(e) =>
                          setNewResolutionStep({
                            ...newResolutionStep,
                            action_taken: e.target.value,
                          })
                        }
                        multiline
                        rows={3}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        label="Result (Optional)"
                        value={newResolutionStep.result}
                        onChange={(e) =>
                          setNewResolutionStep({
                            ...newResolutionStep,
                            result: e.target.value,
                          })
                        }
                        multiline
                        rows={2}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <Button
                        variant="contained"
                        color="error"
                        startIcon={<AddIcon />}
                        onClick={handleAddResolutionStep}
                        disabled={
                          !newResolutionStep.description.trim() ||
                          !newResolutionStep.action_taken.trim() ||
                          loading
                        }
                      >
                        Add Resolution Step
                      </Button>
                    </Grid>
                  </Grid>
                </Paper>
              </Box>

              <Box>
                <Typography variant="h6" gutterBottom>
                  Resolution Steps
                </Typography>
                {resolutionSteps.map((step: any, index: number) => (
                  <Card key={index} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" mb={1}>
                        <Chip
                          label={`Step ${index + 1}`}
                          color="success"
                          size="small"
                        />
                        <Typography variant="caption" color="textSecondary">
                          {new Date(step.timestamp).toLocaleString()}
                        </Typography>
                      </Box>
                      <Typography variant="subtitle2" gutterBottom>
                        {step.description}
                      </Typography>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        <strong>Action Taken:</strong>
                      </Typography>
                      <Typography variant="body2" paragraph>
                        {step.action_taken}
                      </Typography>
                      {step.result && (
                        <>
                          <Typography
                            variant="body2"
                            color="textSecondary"
                            gutterBottom
                          >
                            <strong>Result:</strong>
                          </Typography>
                          <Typography variant="body2">{step.result}</Typography>
                        </>
                      )}
                    </CardContent>
                  </Card>
                ))}
                {resolutionSteps.length === 0 && (
                  <Typography variant="body2" color="textSecondary">
                    No resolution steps recorded. Add steps to document how you
                    resolved this case.
                  </Typography>
                )}
              </Box>
            </TabPanel>
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Box display="flex" justifyContent="space-between" width="100%">
          <Box>
            {!editMode && timesketchEnabled && (
              <Button
                startIcon={<TimelineIcon />}
                onClick={() => setTimesketchDialogOpen(true)}
                disabled={!caseData}
              >
                Export to Timesketch
              </Button>
            )}
          </Box>
          <Box>
            {editMode ? (
              <>
                <Button onClick={() => setEditMode(false)} disabled={loading}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  variant="contained"
                  color="error"
                  startIcon={<SaveIcon />}
                  disabled={loading}
                >
                  Save Changes
                </Button>
              </>
            ) : (
              <>
                <Button onClick={onClose}>Close</Button>
                <Button onClick={() => setEditMode(true)} variant="contained" color="error">
                  Edit
                </Button>
              </>
            )}
          </Box>
        </Box>
      </DialogActions>

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
        caseId={caseId || undefined}
        defaultTimelineName={caseData ? `Case: ${caseData.title}` : ''}
      />
    </Dialog>
  )
}
