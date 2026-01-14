import React, { createContext, useContext, useState, useEffect, useMemo } from 'react'
import { ThemeProvider as MuiThemeProvider, createTheme, Theme } from '@mui/material/styles'
import { configApi } from '../services/api'

interface ThemeContextType {
  mode: 'light' | 'dark'
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export const useTheme = () => {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

interface ThemeProviderProps {
  children: React.ReactNode
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [mode, setMode] = useState<'light' | 'dark'>('dark')

  // Load theme preference from API on mount
  useEffect(() => {
    configApi.getTheme()
      .then(response => {
        if (response.data.theme) {
          setMode(response.data.theme)
        }
      })
      .catch(err => console.error('Failed to load theme:', err))
  }, [])

  const toggleTheme = () => {
    const newMode = mode === 'light' ? 'dark' : 'light'
    setMode(newMode)
    
    // Save to API
    configApi.setTheme(newMode)
      .catch(err => console.error('Failed to save theme:', err))
  }

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          primary: {
            main: mode === 'dark' ? '#1976d2' : '#1565c0',
          },
          secondary: {
            main: mode === 'dark' ? '#dc004e' : '#c62828',
          },
          background: {
            default: mode === 'dark' ? '#121212' : '#f5f5f5',
            paper: mode === 'dark' ? '#1e1e1e' : '#ffffff',
          },
        },
        components: {
          MuiDrawer: {
            styleOverrides: {
              paper: {
                backgroundColor: mode === 'dark' ? '#1e1e1e' : '#ffffff',
              },
            },
          },
          MuiAppBar: {
            styleOverrides: {
              root: {
                backgroundColor: mode === 'dark' ? '#1e1e1e' : '#1976d2',
              },
            },
          },
        },
      }),
    [mode]
  )

  return (
    <ThemeContext.Provider value={{ mode, toggleTheme }}>
      <MuiThemeProvider theme={theme}>{children}</MuiThemeProvider>
    </ThemeContext.Provider>
  )
}

