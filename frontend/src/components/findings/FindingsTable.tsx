import { useEffect, useState, useMemo, useRef } from 'react'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Typography,
  Button,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  TablePagination,
  TableSortLabel,
} from '@mui/material'
import { 
  Visibility as ViewIcon,
  Psychology as InvestigateIcon,
  MoreVert as MoreIcon
} from '@mui/icons-material'
import { findingsApi, agentsApi } from '../../services/api'
import FindingDetailDialog from './FindingDetailDialog'
import { notificationService } from '../../services/notifications'

interface FindingsTableProps {
  filters?: any
  searchQuery?: string
  limit?: number
  refreshKey?: number
  onInvestigate?: (findingId: string, agentId: string, prompt: string, title: string) => void
}

interface Agent {
  id: string
  name: string
  icon: string
}

export default function FindingsTable({ filters = {}, searchQuery = '', limit, refreshKey = 0, onInvestigate }: FindingsTableProps) {
  const [findings, setFindings] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [agents, setAgents] = useState<Agent[]>([])
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [selectedFinding, setSelectedFinding] = useState<any>(null)
  const prevFindingsRef = useRef<Set<string>>(new Set())
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)
  const [orderBy, setOrderBy] = useState<string>('timestamp')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')

  // Memoize filters to prevent unnecessary re-renders
  const stableFilters = useMemo(() => filters, [JSON.stringify(filters)])

  useEffect(() => {
    loadFindings()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stableFilters, searchQuery, limit, refreshKey])

  useEffect(() => {
    // Load agents list
    const loadAgents = async () => {
      try {
        const response = await agentsApi.listAgents()
        setAgents(response.data.agents || [])
      } catch (error) {
        console.error('Failed to load agents:', error)
      }
    }
    loadAgents()
  }, [])

  const loadFindings = async () => {
    try {
      setLoading(true)
      const params: any = { ...stableFilters, limit }
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key]
        }
      })
      
      const response = await findingsApi.getAll(params)
      let newFindings = response.data.findings || []
      
      // Apply search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        newFindings = newFindings.filter((finding: any) => {
          return (
            finding.finding_id?.toLowerCase().includes(query) ||
            finding.data_source?.toLowerCase().includes(query) ||
            finding.description?.toLowerCase().includes(query) ||
            finding.title?.toLowerCase().includes(query)
          )
        })
      }
      
      // Check for new high/critical severity findings and send notifications
      if (prevFindingsRef.current.size > 0) {
        newFindings.forEach((finding: any) => {
          const isNew = !prevFindingsRef.current.has(finding.finding_id)
          const isHighSeverity = finding.severity?.toLowerCase() === 'critical' || finding.severity?.toLowerCase() === 'high'
          
          if (isNew && isHighSeverity) {
            notificationService.notifyNewFinding({
              finding_id: finding.finding_id,
              title: finding.title,
              severity: finding.severity,
              description: finding.description,
            })
          }
        })
      }
      
      // Update previous findings set
      prevFindingsRef.current = new Set(newFindings.map((f: any) => f.finding_id))
      
      setFindings(newFindings)
    } catch (error) {
      console.error('Failed to load findings:', error)
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

  const handleViewFinding = (findingId: string) => {
    setSelectedFindingId(findingId)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setSelectedFindingId(null)
  }

  const handleUpdate = () => {
    loadFindings()
  }

  const handleInvestigateClick = (event: React.MouseEvent<HTMLElement>, finding: any) => {
    setAnchorEl(event.currentTarget)
    setSelectedFinding(finding)
  }

  const handleCloseMenu = () => {
    setAnchorEl(null)
    setSelectedFinding(null)
  }

  const handleAgentSelect = async (agentId: string) => {
    if (!selectedFinding || !onInvestigate) {
      handleCloseMenu()
      return
    }

    try {
      // Get the investigation prompt from the API
      const response = await agentsApi.startInvestigation({
        finding_id: selectedFinding.finding_id,
        agent_id: agentId,
      })

      const agent = agents.find(a => a.id === agentId)
      const title = `Investigation: ${selectedFinding.finding_id.substring(0, 8)}...`
      
      onInvestigate(
        selectedFinding.finding_id,
        agentId,
        response.data.prompt,
        title
      )
    } catch (error) {
      console.error('Failed to start investigation:', error)
    } finally {
      handleCloseMenu()
    }
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    )
  }

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage)
  }

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10))
    setPage(0)
  }

  const handleRequestSort = (property: string) => {
    const isAsc = orderBy === property && order === 'asc'
    setOrder(isAsc ? 'desc' : 'asc')
    setOrderBy(property)
  }

  const sortFindings = (findings: any[]) => {
    return findings.sort((a, b) => {
      let aValue = a[orderBy]
      let bValue = b[orderBy]

      // Handle special cases
      if (orderBy === 'severity') {
        const severityOrder: any = { critical: 4, high: 3, medium: 2, low: 1 }
        aValue = severityOrder[a.severity?.toLowerCase()] || 0
        bValue = severityOrder[b.severity?.toLowerCase()] || 0
      } else if (orderBy === 'timestamp') {
        aValue = new Date(a.timestamp || 0).getTime()
        bValue = new Date(b.timestamp || 0).getTime()
      } else if (orderBy === 'anomaly_score') {
        aValue = a.anomaly_score || 0
        bValue = b.anomaly_score || 0
      }

      if (order === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
      }
    })
  }

  if (findings.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography color="textSecondary" align="center">
          No findings found
        </Typography>
      </Paper>
    )
  }

  // Sort and paginate findings
  const sortedFindings = sortFindings([...findings])
  const paginatedFindings = sortedFindings.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)

  return (
    <>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'finding_id'}
                  direction={orderBy === 'finding_id' ? order : 'asc'}
                  onClick={() => handleRequestSort('finding_id')}
                >
                  Finding ID
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'severity'}
                  direction={orderBy === 'severity' ? order : 'asc'}
                  onClick={() => handleRequestSort('severity')}
                >
                  Severity
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'data_source'}
                  direction={orderBy === 'data_source' ? order : 'asc'}
                  onClick={() => handleRequestSort('data_source')}
                >
                  Data Source
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'timestamp'}
                  direction={orderBy === 'timestamp' ? order : 'asc'}
                  onClick={() => handleRequestSort('timestamp')}
                >
                  Timestamp
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'anomaly_score'}
                  direction={orderBy === 'anomaly_score' ? order : 'asc'}
                  onClick={() => handleRequestSort('anomaly_score')}
                >
                  Anomaly Score
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedFindings.map((finding) => (
              <TableRow 
                key={finding.finding_id}
                onClick={() => handleViewFinding(finding.finding_id)}
                sx={{ 
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'action.hover'
                  }
                }}
              >
                <TableCell>{finding.finding_id}</TableCell>
                <TableCell>
                  <Chip
                    label={finding.severity || 'unknown'}
                    color={getSeverityColor(finding.severity)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{finding.data_source || 'N/A'}</TableCell>
                <TableCell>
                  {finding.timestamp
                    ? new Date(finding.timestamp).toLocaleString()
                    : 'N/A'}
                </TableCell>
                <TableCell>
                  {finding.anomaly_score
                    ? finding.anomaly_score.toFixed(2)
                    : 'N/A'}
                </TableCell>
                <TableCell align="right">
                  <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                    <Button
                      size="small"
                      startIcon={<ViewIcon />}
                      onClick={(e) => {
                        e.stopPropagation()
                        handleViewFinding(finding.finding_id)
                      }}
                    >
                      View
                    </Button>
                    {onInvestigate && (
                      <Button
                        size="small"
                        variant="contained"
                        color="error"
                        startIcon={<InvestigateIcon />}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleInvestigateClick(e, finding)
                        }}
                      >
                        Investigate
                      </Button>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={findings.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>

      <FindingDetailDialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        findingId={selectedFindingId}
        onUpdate={handleUpdate}
      />

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleCloseMenu}
      >
        <MenuItem disabled>
          <Typography variant="caption" color="textSecondary">
            Select an agent to investigate:
          </Typography>
        </MenuItem>
        {agents.map((agent) => (
          <MenuItem key={agent.id} onClick={() => handleAgentSelect(agent.id)}>
            <ListItemIcon>
              <span style={{ fontSize: '1.5rem' }}>{agent.icon}</span>
            </ListItemIcon>
            <ListItemText primary={agent.name} />
          </MenuItem>
        ))}
      </Menu>
    </>
  )
}

