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
  Snackbar,
  Alert,
} from '@mui/material'
import { Close as CloseIcon, Save as SaveIcon } from '@mui/icons-material'
import { findingsApi } from '../../services/api'

interface FindingDetailDialogProps {
  open: boolean
  onClose: () => void
  findingId: string | null
  onUpdate?: () => void
}

export default function FindingDetailDialog({
  open,
  onClose,
  findingId,
  onUpdate,
}: FindingDetailDialogProps) {
  const [loading, setLoading] = useState(false)
  const [editing, setEditing] = useState(false)
  const [finding, setFinding] = useState<any>(null)
  const [editedFinding, setEditedFinding] = useState<any>(null)
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })

  useEffect(() => {
    if (open && findingId) {
      loadFinding()
    }
  }, [open, findingId])

  const loadFinding = async () => {
    if (!findingId) return
    
    setLoading(true)
    try {
      const response = await findingsApi.getById(findingId)
      setFinding(response.data)
      setEditedFinding(response.data)
    } catch (error) {
      console.error('Failed to load finding:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!findingId || !editedFinding) return
    
    setLoading(true)
    try {
      await findingsApi.update(findingId, editedFinding)
      setFinding(editedFinding)
      setEditing(false)
      setSnackbar({ open: true, message: 'Finding updated successfully', severity: 'success' })
      if (onUpdate) onUpdate()
    } catch (error) {
      console.error('Failed to update finding:', error)
      setSnackbar({ open: true, message: 'Failed to update finding', severity: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!findingId) return
    
    if (!confirm('Are you sure you want to delete this finding?')) return
    
    setLoading(true)
    try {
      await findingsApi.delete(findingId)
      setSnackbar({ open: true, message: 'Finding deleted successfully', severity: 'success' })
      if (onUpdate) onUpdate()
      setTimeout(() => onClose(), 1000) // Close after showing success message
    } catch (error) {
      console.error('Failed to delete finding:', error)
      setSnackbar({ open: true, message: 'Failed to delete finding', severity: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const getSeverityColor = (severity: string) => {
    const colors: any = {
      critical: 'error',
      high: 'error',
      medium: 'warning',
      low: 'success',
    }
    return colors[severity?.toLowerCase()] || 'default'
  }

  if (!finding && !loading) {
    return null
  }

  const displayFinding = editing ? editedFinding : finding

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Finding Details</Typography>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      
      <DialogContent dividers>
        {loading && !finding ? (
          <Typography>Loading...</Typography>
        ) : displayFinding ? (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="textSecondary">
                Finding ID
              </Typography>
              <Typography variant="body1">{displayFinding.finding_id}</Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Severity
              </Typography>
              {editing ? (
                <FormControl fullWidth size="small" sx={{ mt: 1 }}>
                  <Select
                    value={editedFinding.severity || ''}
                    onChange={(e) =>
                      setEditedFinding({ ...editedFinding, severity: e.target.value })
                    }
                  >
                    <MenuItem value="low">Low</MenuItem>
                    <MenuItem value="medium">Medium</MenuItem>
                    <MenuItem value="high">High</MenuItem>
                    <MenuItem value="critical">Critical</MenuItem>
                  </Select>
                </FormControl>
              ) : (
                <Box mt={1}>
                  <Chip
                    label={displayFinding.severity || 'Unknown'}
                    color={getSeverityColor(displayFinding.severity)}
                    size="small"
                  />
                </Box>
              )}
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Data Source
              </Typography>
              {editing ? (
                <TextField
                  fullWidth
                  size="small"
                  value={editedFinding.data_source || ''}
                  onChange={(e) =>
                    setEditedFinding({ ...editedFinding, data_source: e.target.value })
                  }
                  sx={{ mt: 1 }}
                />
              ) : (
                <Typography variant="body1">
                  {displayFinding.data_source || 'N/A'}
                </Typography>
              )}
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Timestamp
              </Typography>
              <Typography variant="body1">
                {displayFinding.timestamp
                  ? new Date(displayFinding.timestamp).toLocaleString()
                  : 'N/A'}
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="textSecondary">
                Anomaly Score
              </Typography>
              {editing ? (
                <TextField
                  fullWidth
                  size="small"
                  type="number"
                  value={editedFinding.anomaly_score || ''}
                  onChange={(e) =>
                    setEditedFinding({
                      ...editedFinding,
                      anomaly_score: parseFloat(e.target.value),
                    })
                  }
                  sx={{ mt: 1 }}
                />
              ) : (
                <Typography variant="body1">
                  {displayFinding.anomaly_score
                    ? displayFinding.anomaly_score.toFixed(2)
                    : 'N/A'}
                </Typography>
              )}
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" color="textSecondary">
                Description
              </Typography>
              {editing ? (
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  value={editedFinding.description || ''}
                  onChange={(e) =>
                    setEditedFinding({ ...editedFinding, description: e.target.value })
                  }
                  sx={{ mt: 1 }}
                />
              ) : (
                <Typography variant="body1">
                  {displayFinding.description || 'No description available'}
                </Typography>
              )}
            </Grid>

            {displayFinding.details && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="textSecondary">
                  Additional Details
                </Typography>
                <Box
                  sx={{
                    mt: 1,
                    p: 2,
                    bgcolor: 'background.default',
                    borderRadius: 1,
                    fontFamily: 'monospace',
                    fontSize: '0.875rem',
                    overflow: 'auto',
                    maxHeight: 200,
                  }}
                >
                  <pre>{JSON.stringify(displayFinding.details, null, 2)}</pre>
                </Box>
              </Grid>
            )}

            {displayFinding.related_entities && displayFinding.related_entities.length > 0 && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="textSecondary">
                  Related Entities
                </Typography>
                <Box mt={1}>
                  {displayFinding.related_entities.map((entity: string, index: number) => (
                    <Chip key={index} label={entity} size="small" sx={{ mr: 1, mb: 1 }} />
                  ))}
                </Box>
              </Grid>
            )}
          </Grid>
        ) : null}
      </DialogContent>

      <DialogActions>
        <Box display="flex" justifyContent="space-between" width="100%">
          <Box>
            {!editing && (
              <Button onClick={handleDelete} color="error" disabled={loading}>
                Delete
              </Button>
            )}
          </Box>
          <Box>
            {editing ? (
              <>
                <Button onClick={() => setEditing(false)} disabled={loading}>
                  Cancel
                </Button>
                <Button
                  onClick={handleSave}
                  variant="contained"
                  color="error"
                  startIcon={<SaveIcon />}
                  disabled={loading}
                >
                  Save
                </Button>
              </>
            ) : (
              <>
                <Button onClick={onClose}>Close</Button>
                <Button onClick={() => setEditing(true)} variant="contained" color="error">
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
    </Dialog>
  )
}

