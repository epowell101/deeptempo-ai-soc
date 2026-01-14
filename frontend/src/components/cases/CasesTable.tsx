import { useEffect, useState, useMemo } from 'react'
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
  TablePagination,
  TableSortLabel,
} from '@mui/material'
import { Visibility as ViewIcon } from '@mui/icons-material'
import { casesApi } from '../../services/api'
import CaseDetailDialog from './CaseDetailDialog'

interface CasesTableProps {
  filters?: any
  searchQuery?: string
  limit?: number
  refreshKey?: number
}

export default function CasesTable({ filters = {}, searchQuery = '', limit, refreshKey = 0 }: CasesTableProps) {
  const [cases, setCases] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(10)
  const [orderBy, setOrderBy] = useState<string>('created_at')
  const [order, setOrder] = useState<'asc' | 'desc'>('desc')

  // Memoize filters to prevent unnecessary re-renders
  const stableFilters = useMemo(() => filters, [JSON.stringify(filters)])

  useEffect(() => {
    loadCases()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stableFilters, searchQuery, limit, refreshKey])

  const loadCases = async () => {
    try {
      setLoading(true)
      const params: any = { ...stableFilters }
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key]
        }
      })
      
      const response = await casesApi.getAll(params)
      let casesList = response.data.cases || []
      
      // Apply search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        casesList = casesList.filter((caseItem: any) => {
          return (
            caseItem.case_id?.toLowerCase().includes(query) ||
            caseItem.title?.toLowerCase().includes(query) ||
            caseItem.description?.toLowerCase().includes(query)
          )
        })
      }
      
      // Apply limit if specified
      if (limit) {
        casesList = casesList.slice(0, limit)
      }
      
      setCases(casesList)
    } catch (error) {
      console.error('Failed to load cases:', error)
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

  const handleViewCase = (caseId: string) => {
    setSelectedCaseId(caseId)
    setDialogOpen(true)
  }

  const handleCloseDialog = () => {
    setDialogOpen(false)
    setSelectedCaseId(null)
  }

  const handleUpdate = () => {
    loadCases()
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

  const sortCases = (cases: any[]) => {
    return cases.sort((a, b) => {
      let aValue = a[orderBy]
      let bValue = b[orderBy]

      // Handle special cases
      if (orderBy === 'priority') {
        const priorityOrder: any = { critical: 4, high: 3, medium: 2, low: 1 }
        aValue = priorityOrder[a.priority?.toLowerCase()] || 0
        bValue = priorityOrder[b.priority?.toLowerCase()] || 0
      } else if (orderBy === 'created_at') {
        aValue = new Date(a.created_at || 0).getTime()
        bValue = new Date(b.created_at || 0).getTime()
      }

      if (order === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0
      }
    })
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={3}>
        <CircularProgress />
      </Box>
    )
  }

  if (cases.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography color="textSecondary" align="center">
          No cases found
        </Typography>
      </Paper>
    )
  }

  // Sort and paginate cases
  const sortedCases = sortCases([...cases])
  const paginatedCases = sortedCases.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)

  return (
    <>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'case_id'}
                  direction={orderBy === 'case_id' ? order : 'asc'}
                  onClick={() => handleRequestSort('case_id')}
                >
                  Case ID
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'title'}
                  direction={orderBy === 'title' ? order : 'asc'}
                  onClick={() => handleRequestSort('title')}
                >
                  Title
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'status'}
                  direction={orderBy === 'status' ? order : 'asc'}
                  onClick={() => handleRequestSort('status')}
                >
                  Status
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'priority'}
                  direction={orderBy === 'priority' ? order : 'asc'}
                  onClick={() => handleRequestSort('priority')}
                >
                  Priority
                </TableSortLabel>
              </TableCell>
              <TableCell>
                <TableSortLabel
                  active={orderBy === 'created_at'}
                  direction={orderBy === 'created_at' ? order : 'asc'}
                  onClick={() => handleRequestSort('created_at')}
                >
                  Created
                </TableSortLabel>
              </TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedCases.map((caseItem) => (
              <TableRow 
                key={caseItem.case_id}
                onClick={() => handleViewCase(caseItem.case_id)}
                sx={{ 
                  cursor: 'pointer',
                  '&:hover': {
                    backgroundColor: 'action.hover'
                  }
                }}
              >
                <TableCell>{caseItem.case_id}</TableCell>
                <TableCell>{caseItem.title || 'Untitled'}</TableCell>
                <TableCell>
                  <Chip
                    label={caseItem.status || 'unknown'}
                    color={getStatusColor(caseItem.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={caseItem.priority || 'unknown'}
                    color={getPriorityColor(caseItem.priority)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {caseItem.created_at
                    ? new Date(caseItem.created_at).toLocaleString()
                    : 'N/A'}
                </TableCell>
                <TableCell align="right">
                  <Button
                    size="small"
                    startIcon={<ViewIcon />}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleViewCase(caseItem.case_id)
                    }}
                  >
                    View
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={cases.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </TableContainer>

      <CaseDetailDialog
        open={dialogOpen}
        onClose={handleCloseDialog}
        caseId={selectedCaseId}
        onUpdate={handleUpdate}
      />
    </>
  )
}

