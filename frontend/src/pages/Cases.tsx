import { useState } from 'react'
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Paper,
  Snackbar,
  Alert,
  Tooltip,
} from '@mui/material'
import { Add as AddIcon, Refresh as RefreshIcon, Search as SearchIcon } from '@mui/icons-material'
import CasesTable from '../components/cases/CasesTable'
import { casesApi } from '../services/api'

export default function Cases() {
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
  })
  const [searchQuery, setSearchQuery] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [newCase, setNewCase] = useState({
    title: '',
    description: '',
    priority: 'medium',
  })
  const [snackbar, setSnackbar] = useState<{ open: boolean; message: string; severity: 'success' | 'error' }>({
    open: false,
    message: '',
    severity: 'success',
  })

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1)
  }

  const handleCreateCase = async () => {
    if (!newCase.title.trim()) {
      setSnackbar({ open: true, message: 'Please enter a case title', severity: 'error' })
      return
    }

    try {
      await casesApi.create({
        ...newCase,
        finding_ids: [],
      })
      setCreateDialogOpen(false)
      setNewCase({ title: '', description: '', priority: 'medium' })
      setSnackbar({ open: true, message: 'Case created successfully', severity: 'success' })
      handleRefresh()
    } catch (error) {
      console.error('Failed to create case:', error)
      setSnackbar({ open: true, message: 'Failed to create case', severity: 'error' })
    }
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Cases</Typography>
        <Box>
          <Tooltip title="Refresh cases from the backend">
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              sx={{ mr: 1 }}
            >
              Refresh
            </Button>
          </Tooltip>
          <Tooltip title="Create a new case to track an investigation">
            <Button
              variant="contained"
              color="error"
              startIcon={<AddIcon />}
              onClick={() => setCreateDialogOpen(true)}
            >
              New Case
            </Button>
          </Tooltip>
        </Box>
      </Box>

      {/* Search and Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Search & Filters
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12}>
            <TextField
              fullWidth
              placeholder="Search cases by title, description, or ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <Box sx={{ mr: 1, display: 'flex', alignItems: 'center', color: 'text.secondary' }}>
                    <SearchIcon />
                  </Box>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status}
                label="Status"
                onChange={(e) =>
                  setFilters({ ...filters, status: e.target.value })
                }
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value="open">Open</MenuItem>
                <MenuItem value="in-progress">In Progress</MenuItem>
                <MenuItem value="resolved">Resolved</MenuItem>
                <MenuItem value="closed">Closed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={filters.priority}
                label="Priority"
                onChange={(e) =>
                  setFilters({ ...filters, priority: e.target.value })
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
        </Grid>
      </Paper>

      {/* Cases Table */}
      <CasesTable filters={filters} searchQuery={searchQuery} refreshKey={refreshKey} />

      {/* Create Case Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Create New Case</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Title"
            fullWidth
            value={newCase.title}
            onChange={(e) => setNewCase({ ...newCase, title: e.target.value })}
          />
          <TextField
            margin="dense"
            label="Description"
            fullWidth
            multiline
            rows={4}
            value={newCase.description}
            onChange={(e) => setNewCase({ ...newCase, description: e.target.value })}
          />
          <FormControl fullWidth margin="dense">
            <InputLabel>Priority</InputLabel>
            <Select
              value={newCase.priority}
              label="Priority"
              onChange={(e) => setNewCase({ ...newCase, priority: e.target.value })}
            >
              <MenuItem value="low">Low</MenuItem>
              <MenuItem value="medium">Medium</MenuItem>
              <MenuItem value="high">High</MenuItem>
              <MenuItem value="critical">Critical</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCreateCase} variant="contained" color="error">
            Create
          </Button>
        </DialogActions>
      </Dialog>

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
    </Box>
  )
}

