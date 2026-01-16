import { useState, useRef, useEffect } from 'react'
import {
  Drawer,
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  IconButton,
  CircularProgress,
  Tabs,
  Tab,
  Collapse,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Chip,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
} from '@mui/material'
import {
  Send as SendIcon,
  Add as AddIcon,
  Close as CloseIcon,
  Settings as SettingsIcon,
  AttachFile as AttachFileIcon,
  Image as ImageIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  PictureAsPdf as PdfIcon,
  Info as InfoIcon,
} from '@mui/icons-material'
import { claudeApi, agentsApi, mcpApi } from '../../services/api'
import { notificationService } from '../../services/notifications'

interface ContentBlock {
  type: 'text' | 'image'
  text?: string
  source?: {
    type: 'base64'
    media_type: string
    data: string
  }
}

interface Message {
  role: 'user' | 'assistant'
  content: string | ContentBlock[]
}

interface ChatTab {
  id: string
  title: string
  messages: Message[]
  investigationKey?: string  // Unique key for finding+agent investigations to prevent duplicates
}

interface ClaudeDrawerProps {
  open: boolean
  onClose: () => void
  initialMessages?: Message[]
  initialAgentId?: string
  initialTitle?: string
}

interface Agent {
  id: string
  name: string
  description: string
  icon?: string
  color?: string
  specialization?: string
}

interface Model {
  id: string
  name: string
  description: string
}

interface AttachedFile {
  name: string
  type: 'image' | 'text' | 'file'
  data: string
  media_type?: string
}

export default function ClaudeDrawer({ open, onClose, initialMessages, initialAgentId, initialTitle }: ClaudeDrawerProps) {
  // Helper function to strip thinking blocks from messages
  const stripThinkingBlocks = (messages: Message[]): Message[] => {
    return messages.map(msg => {
      if (msg.role === 'assistant' && Array.isArray(msg.content)) {
        // Filter out thinking blocks from content array
        const filteredContent = msg.content.filter((block: ContentBlock) => block.type !== 'thinking')
        // If only thinking blocks existed, convert to empty text
        if (filteredContent.length === 0) {
          return { ...msg, content: '' }
        }
        return { ...msg, content: filteredContent }
      }
      return msg
    }).filter(msg => {
      // Remove messages that have no content after filtering
      if (msg.role === 'assistant' && msg.content === '') {
        return false
      }
      return true
    })
  }

  // Load persisted chat data from localStorage
  const loadPersistedChatData = () => {
    try {
      const savedTabs = localStorage.getItem('claudeDrawerTabs')
      const savedCurrentTab = localStorage.getItem('claudeDrawerCurrentTab')
      
      if (savedTabs) {
        const parsedTabs = JSON.parse(savedTabs)
        
        // Clean up any thinking blocks from persisted messages
        // This ensures compatibility when loading old sessions
        const cleanedTabs = parsedTabs.map((tab: ChatTab) => ({
          ...tab,
          messages: tab.messages.map(msg => {
            if (msg.role === 'assistant' && Array.isArray(msg.content)) {
              // Filter out thinking blocks
              const filteredContent = msg.content.filter((block: any) => block.type !== 'thinking')
              return { ...msg, content: filteredContent.length > 0 ? filteredContent : msg.content }
            }
            return msg
          })
        }))
        
        return {
          tabs: cleanedTabs,
          currentTab: savedCurrentTab ? parseInt(savedCurrentTab, 10) : 0
        }
      }
    } catch (error) {
      console.error('Error loading persisted chat data:', error)
    }
    
    return {
      tabs: [{ id: '1', title: 'Chat 1', messages: [] }],
      currentTab: 0
    }
  }

  // Load persisted chat settings from localStorage
  const loadPersistedSettings = () => {
    try {
      const savedSettings = localStorage.getItem('claudeDrawerSettings')
      if (savedSettings) {
        return JSON.parse(savedSettings)
      }
    } catch (error) {
      console.error('Error loading persisted settings:', error)
    }
    
    return {
      model: 'claude-sonnet-4-20250514',
      maxTokens: 4096,
      enableThinking: false,
      thinkingBudget: 3,  // Default 3k tokens (safe for 4096 max_tokens)
      streaming: false,
      systemPrompt: '',
      selectedAgent: ''
    }
  }

  const persistedData = loadPersistedChatData()
  const persistedSettings = loadPersistedSettings()
  
  // Tab management
  const [tabs, setTabs] = useState<ChatTab[]>(persistedData.tabs)
  const [currentTab, setCurrentTab] = useState(persistedData.currentTab)
  const [lastInvestigationId, setLastInvestigationId] = useState<string | null>(null)
  
  // Message input
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  
  // Chat settings
  const [showSettings, setShowSettings] = useState(false)
  const [model, setModel] = useState(persistedSettings.model)
  const [maxTokens, setMaxTokens] = useState(persistedSettings.maxTokens)
  const [enableThinking, setEnableThinking] = useState(persistedSettings.enableThinking)
  const [thinkingBudget, setThinkingBudget] = useState(persistedSettings.thinkingBudget)
  const [streaming, setStreaming] = useState(persistedSettings.streaming)
  const [systemPrompt, setSystemPrompt] = useState(persistedSettings.systemPrompt)
  const [validationError, setValidationError] = useState<string | null>(null)
  
  // Individual field validation errors
  const [maxTokensError, setMaxTokensError] = useState<string | null>(null)
  const [thinkingBudgetError, setThinkingBudgetError] = useState<string | null>(null)
  const [systemPromptError, setSystemPromptError] = useState<string | null>(null)
  
  // Agent selection
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>(persistedSettings.selectedAgent)
  const [agentInfoDialogOpen, setAgentInfoDialogOpen] = useState(false)
  
  // Models list
  const [models, setModels] = useState<Model[]>([])
  
  // File attachments
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // MCP status
  const [mcpStatus, setMcpStatus] = useState<{ available: number; total: number } | null>(null)
  const [mcpError, setMcpError] = useState<string | null>(null)
  
  // Token estimation
  const [estimatedTokens, setEstimatedTokens] = useState(0)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [tabs, currentTab])

  // Persist tabs to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('claudeDrawerTabs', JSON.stringify(tabs))
    } catch (error) {
      console.error('Error persisting tabs:', error)
    }
  }, [tabs])

  // Persist current tab to localStorage whenever it changes
  useEffect(() => {
    try {
      localStorage.setItem('claudeDrawerCurrentTab', currentTab.toString())
    } catch (error) {
      console.error('Error persisting current tab:', error)
    }
  }, [currentTab])

  // Persist chat settings to localStorage whenever they change
  useEffect(() => {
    try {
      const settings = {
        model,
        maxTokens,
        enableThinking,
        thinkingBudget,
        streaming,
        systemPrompt,
        selectedAgent
      }
      localStorage.setItem('claudeDrawerSettings', JSON.stringify(settings))
    } catch (error) {
      console.error('Error persisting settings:', error)
    }
  }, [model, maxTokens, enableThinking, thinkingBudget, streaming, systemPrompt, selectedAgent])

  useEffect(() => {
    if (open) {
      loadAgents()
      loadModels()
      loadMcpStatus()
    }
  }, [open])

  // Handle initial investigation data
  useEffect(() => {
    // Create a unique ID for this investigation request
    const investigationId = initialMessages && initialAgentId 
      ? `${initialAgentId}-${JSON.stringify(initialMessages)}`
      : null
    
    console.log('Investigation useEffect triggered', { 
      open, 
      hasMessages: !!initialMessages && initialMessages.length > 0, 
      hasAgentId: !!initialAgentId,
      investigationId,
      lastInvestigationId
    })
    
    // Only proceed if:
    // 1. Drawer is open
    // 2. We have investigation data
    // 3. This is a NEW investigation (different from the last one)
    if (open && initialMessages && initialMessages.length > 0 && initialAgentId && investigationId !== lastInvestigationId) {
      console.log('Starting automatic investigation with agent:', initialAgentId)
      setLastInvestigationId(investigationId)
      
      // Extract finding ID from the first message (format: "analyze f-20260109-40d9379b...")
      let findingId = ''
      const firstMessageContent = typeof initialMessages[0]?.content === 'string' 
        ? initialMessages[0].content 
        : ''
      const findingMatch = firstMessageContent.match(/f-\d{8}-[a-f0-9]{8}/i)
      if (findingMatch) {
        findingId = findingMatch[0]
      }
      
      // Create investigation key to check for duplicates
      const investigationKey = findingId ? `${findingId}-${initialAgentId}` : null
      
      // Check if we already have a tab for this investigation
      const existingTabIndex = investigationKey 
        ? tabs.findIndex(tab => tab.investigationKey === investigationKey)
        : -1
      
      if (existingTabIndex !== -1) {
        // Tab already exists - just switch to it
        console.log('Found existing investigation tab, switching to it')
        setCurrentTab(existingTabIndex)
        setSelectedAgent(initialAgentId)
        return // Don't create a new tab or start a new investigation
      }
      
      // Create a new tab with the investigation
      const newTab: ChatTab = {
        id: `investigation-${Date.now()}`,
        title: initialTitle || 'Investigation',
        messages: initialMessages,
        investigationKey: investigationKey || undefined
      }
      
      // Add new tab to existing tabs instead of replacing them
      setTabs(prevTabs => [...prevTabs, newTab])
      const newTabIndex = tabs.length // Index of the newly added tab
      setCurrentTab(newTabIndex)
      setSelectedAgent(initialAgentId)
      setLoading(true)
      
      // Trigger the investigation by sending the message to the API
      const startInvestigation = async () => {
        try {
          console.log('Sending investigation request to API with agent:', initialAgentId)
          console.log('Initial messages:', initialMessages)
          
          // Explicitly enable thinking for investigations
          // Investigation agents (investigator, threat_hunter, etc.) need extended thinking
          // Note: Agents may override max_tokens, so use a safe thinking budget
          const response = await claudeApi.chat({
            messages: initialMessages,
            model: model || 'claude-sonnet-4-20250514',
            max_tokens: 32768,  // Large token limit for investigations (may be overridden by agent)
            enable_thinking: true,  // Always enable thinking for investigations
            thinking_budget: 10000,  // 10k token budget (safe for agents with 16k+ max_tokens)
            agent_id: initialAgentId,
            streaming: streaming || false,
          })
          
          console.log('Investigation response received:', response.data)
          
          const assistantMessage: Message = {
            role: 'assistant',
            content: response.data.response || 'No response',
          }
          
          // Update the specific tab that was created for this investigation
          setTabs(prevTabs => 
            prevTabs.map(tab => 
              tab.id === newTab.id 
                ? { ...tab, messages: [...initialMessages, assistantMessage] }
                : tab
            )
          )
          
          // Send desktop notification for investigation completion
          notificationService.notifyInvestigationComplete({
            title: initialTitle || 'Investigation',
            summary: 'Analysis complete - click to view results',
            finding_id: initialMessages?.[0]?.content?.toString()?.match(/finding[_-]?\w+/i)?.[0],
          })
        } catch (error: any) {
          console.error('Investigation error:', error)
          const errorMessage: Message = {
            role: 'assistant',
            content: `Error: ${error?.response?.data?.detail || 'Failed to get response'}`,
          }
          // Update the specific tab with the error message
          setTabs(prevTabs => 
            prevTabs.map(tab => 
              tab.id === newTab.id 
                ? { ...tab, messages: [...initialMessages, errorMessage] }
                : tab
            )
          )
        } finally {
          setLoading(false)
        }
      }
      
      // Start the investigation after a brief delay to ensure UI is ready
      setTimeout(startInvestigation, 300)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, initialMessages, initialAgentId, initialTitle, lastInvestigationId])

  // Reset investigation tracking when drawer closes
  useEffect(() => {
    if (!open) {
      setLastInvestigationId(null)
    }
  }, [open])

  useEffect(() => {
    // Estimate tokens based on conversation history
    const messages = tabs[currentTab]?.messages || []
    let total = 0
    messages.forEach(msg => {
      if (typeof msg.content === 'string') {
        // Rough estimation: ~4 chars per token
        total += msg.content.length / 4
      } else {
        msg.content.forEach(block => {
          if (block.type === 'text' && block.text) {
            total += block.text.length / 4
          } else if (block.type === 'image') {
            // Images use ~85 tokens per image
            total += 85
          }
        })
      }
    })
    // Add current input
    total += input.length / 4
    // Add system prompt if present
    if (systemPrompt) {
      total += systemPrompt.length / 4
    }
    setEstimatedTokens(Math.round(total))
  }, [tabs, currentTab, input, systemPrompt])

  // Validation effect - check for invalid configurations with individual field errors
  useEffect(() => {
    let hasError = false
    let maxTokensErr: string | null = null
    let thinkingBudgetErr: string | null = null
    let systemPromptErr: string | null = null
    
    // Validate Max Tokens
    if (maxTokens < 256 || maxTokens > 32768) {
      maxTokensErr = 'Must be between 256 and 32,768'
      hasError = true
    }
    
    // Validate Thinking Budget
    if (enableThinking) {
      if (thinkingBudget < 1 || thinkingBudget > 100) {
        thinkingBudgetErr = 'Must be between 1 and 100k tokens'
        hasError = true
      } else if ((thinkingBudget * 1000) >= maxTokens) {
        thinkingBudgetErr = `Must be less than max tokens (${maxTokens}). Current: ${thinkingBudget * 1000} tokens`
        // Also mark max tokens as related to the error
        if (!maxTokensErr) {
          maxTokensErr = `Must be greater than thinking budget (${thinkingBudget * 1000} tokens)`
        }
        hasError = true
      }
    }
    
    // Validate System Prompt
    if (systemPrompt.length > 10000) {
      systemPromptErr = `Exceeds maximum length (${systemPrompt.length}/10,000 characters)`
      hasError = true
    }
    
    setMaxTokensError(maxTokensErr)
    setThinkingBudgetError(thinkingBudgetErr)
    setSystemPromptError(systemPromptErr)
    setValidationError(hasError ? 'Please fix the configuration errors below' : null)
  }, [maxTokens, enableThinking, thinkingBudget, systemPrompt])

  const loadAgents = async () => {
    try {
      const response = await agentsApi.listAgents()
      setAgents(response.data.agents || [])
    } catch (error) {
      console.error('Failed to load agents:', error)
    }
  }

  const loadModels = async () => {
    try {
      const response = await claudeApi.getModels()
      setModels(response.data.models || [])
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }

  const loadMcpStatus = async () => {
    try {
      const response = await mcpApi.getStatuses()
      const statuses = response.data.statuses || []
      // Count servers that are available (not in error state)
      // This includes 'running', 'stopped', and 'stdio (Claude Desktop)' servers
      const available = statuses.filter((s: any) => 
        s.status && s.status !== 'error' && s.status !== 'not found'
      ).length
      setMcpStatus({ available, total: statuses.length })
      setMcpError(null)
    } catch (error) {
      console.error('Failed to load MCP status:', error)
      setMcpError('Failed to connect to MCP servers')
    }
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (!files || files.length === 0) return

    for (let i = 0; i < files.length; i++) {
      const file = files[i]
      try {
        const response = await claudeApi.uploadFile(file)
        const uploadData = response.data

        if (uploadData.type === 'image') {
          setAttachedFiles(prev => [
            ...prev,
            {
              name: uploadData.filename,
              type: 'image',
              data: uploadData.data,
              media_type: uploadData.media_type,
            },
          ])
        } else if (uploadData.type === 'text') {
          // For text files, add as text content
          setInput(prev => prev + '\n\n' + uploadData.content)
        }
      } catch (error: any) {
        console.error('File upload error:', error)
        alert(`Failed to upload ${file.name}: ${error.response?.data?.detail || error.message}`)
      }
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleSend = async () => {
    if ((!input.trim() && attachedFiles.length === 0) || loading || validationError) return

    // Build message content
    let messageContent: string | ContentBlock[]
    
    if (attachedFiles.length > 0) {
      // Use content blocks format
      const contentBlocks: ContentBlock[] = []
      
      // Add text if present
      if (input.trim()) {
        contentBlocks.push({
          type: 'text',
          text: input.trim(),
        })
      }
      
      // Add images
      attachedFiles.forEach(file => {
        if (file.type === 'image' && file.media_type) {
          contentBlocks.push({
            type: 'image',
            source: {
              type: 'base64',
              media_type: file.media_type,
              data: file.data,
            },
          })
        }
      })
      
      messageContent = contentBlocks
    } else {
      messageContent = input.trim()
    }

    const userMessage: Message = {
      role: 'user',
      content: messageContent,
    }

    // Add user message
    const newTabs = [...tabs]
    newTabs[currentTab].messages.push(userMessage)
    setTabs(newTabs)
    setInput('')
    setAttachedFiles([])
    setLoading(true)

    try {
      // Strip thinking blocks from messages if thinking is disabled
      const messagesToSend = enableThinking 
        ? newTabs[currentTab].messages 
        : stripThinkingBlocks(newTabs[currentTab].messages)
      
      if (streaming) {
        // Handle streaming mode
        try {
          const response = await fetch('/api/claude/chat/stream', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              messages: messagesToSend,
              model,
              max_tokens: maxTokens,
              enable_thinking: enableThinking,
              thinking_budget: thinkingBudget * 1000,
              agent_id: selectedAgent || undefined,
              system_prompt: systemPrompt || undefined,
            }),
          })

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`)
          }

          const reader = response.body?.getReader()
          const decoder = new TextDecoder()
          let assistantContent = ''

          // Add placeholder message
          const assistantMessage: Message = {
            role: 'assistant',
            content: '',
          }
          const updatedTabs = [...newTabs]
          updatedTabs[currentTab].messages.push(assistantMessage)
          setTabs(updatedTabs)

          if (reader) {
            while (true) {
              const { done, value } = await reader.read()
              if (done) break

              const chunk = decoder.decode(value)
              const lines = chunk.split('\n')

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  try {
                    const data = JSON.parse(line.slice(6))
                    if (data.error) {
                      throw new Error(data.error)
                    }
                    if (data.content) {
                      assistantContent += data.content
                      // Update message content
                      const streamingTabs = [...updatedTabs]
                      const lastMessage = streamingTabs[currentTab].messages[streamingTabs[currentTab].messages.length - 1]
                      lastMessage.content = assistantContent
                      setTabs(streamingTabs)
                    }
                    if (data.done) {
                      break
                    }
                  } catch (e) {
                    console.error('Error parsing streaming data:', e)
                  }
                }
              }
            }
          }
        } catch (streamError: any) {
          console.error('Streaming error:', streamError)
          throw streamError
        }
      } else {
        // Handle non-streaming mode
        console.log('Sending non-streaming request with max_tokens:', maxTokens)
        const response = await claudeApi.chat({
          messages: messagesToSend,
          model,
          max_tokens: maxTokens,
          enable_thinking: enableThinking,
          thinking_budget: thinkingBudget * 1000,
          agent_id: selectedAgent || undefined,
          system_prompt: systemPrompt || undefined,
        })

        console.log('Received response:', response.data)
        
        // Check if response seems incomplete
        const responseText = response.data.response || 'No response'
        if (responseText.length < 100 && responseText.includes('Let me')) {
          console.warn('Response may be incomplete - appears to be cut off')
        }

        // Add assistant response
        const assistantMessage: Message = {
          role: 'assistant',
          content: responseText,
        }

        const updatedTabs = [...newTabs]
        updatedTabs[currentTab].messages.push(assistantMessage)
        setTabs(updatedTabs)
      }
    } catch (error: any) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: `Error: ${error?.response?.data?.detail || error?.message || 'Failed to get response'}`,
      }
      const updatedTabs = [...newTabs]
      updatedTabs[currentTab].messages.push(errorMessage)
      setTabs(updatedTabs)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewTab = () => {
    const newTab: ChatTab = {
      id: `${Date.now()}`,
      title: `Chat ${tabs.length + 1}`,
      messages: [],
    }
    setTabs([...tabs, newTab])
    setCurrentTab(tabs.length)
  }

  const handleCloseTab = (index: number) => {
    // If this is the last tab, replace it with a fresh empty tab
    if (tabs.length === 1) {
      const freshTab: ChatTab = {
        id: `${Date.now()}`,
        title: 'Chat 1',
        messages: [],
      }
      setTabs([freshTab])
      setCurrentTab(0)
      return
    }

    const newTabs = tabs.filter((_, i) => i !== index)
    setTabs(newTabs)
    if (currentTab >= newTabs.length) {
      setCurrentTab(newTabs.length - 1)
    }
  }

  const handleClearHistory = () => {
    const newTabs = [...tabs]
    newTabs[currentTab].messages = []
    setTabs(newTabs)
  }

  const handleGenerateReport = async () => {
    const currentTabData = tabs[currentTab]
    
    if (!currentTabData || currentTabData.messages.length === 0) {
      alert('No conversation to generate report from')
      return
    }
    
    try {
      setLoading(true)
      const response = await claudeApi.generateChatReport({
        tab_title: currentTabData.title,
        messages: currentTabData.messages,
        notes: undefined, // Could be extended to include notes
      })
      
      // Show success notification
      notificationService.notify({
        title: 'Report Generated',
        body: response.data.message || 'Chat report PDF has been generated successfully',
        tag: 'chat-report',
      })
      
      alert(`Report generated successfully!\n\nFile: ${response.data.filename}\nLocation: ${response.data.path}`)
    } catch (error: any) {
      console.error('Report generation error:', error)
      const errorMessage = error?.response?.data?.detail || 'Failed to generate report'
      alert(`Error generating report: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const renderMessageContent = (content: string | ContentBlock[]) => {
    if (typeof content === 'string') {
      return <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>{content}</Typography>
    }

    return (
      <Box>
        {content.map((block, index) => (
          <Box key={index} sx={{ mb: 1 }}>
            {block.type === 'text' && block.text && (
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {block.text}
              </Typography>
            )}
            {block.type === 'image' && block.source && (
              <img
                src={`data:${block.source.media_type};base64,${block.source.data}`}
                alt="Attached image"
                style={{ maxWidth: '100%', borderRadius: 8, marginTop: 8 }}
              />
            )}
          </Box>
        ))}
      </Box>
    )
  }

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      sx={{
        '& .MuiDrawer-paper': {
          width: { xs: '100%', sm: 500, md: 600 },
        },
      }}
    >
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box
          sx={{
            p: 2,
            borderBottom: 1,
            borderColor: 'divider',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Typography variant="h6">DeepTempo Chat</Typography>
          <Box>
            <IconButton onClick={() => setShowSettings(!showSettings)} size="small">
              <SettingsIcon />
            </IconButton>
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Settings Panel */}
        <Collapse in={showSettings}>
          <Box sx={{ 
            p: 2, 
            bgcolor: 'background.default', 
            borderBottom: 1, 
            borderColor: 'divider',
            position: 'relative',
            zIndex: 1
          }}>
            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 'bold' }}>
              Chat Settings
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, width: '100%' }}>
              {/* MCP Status */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, justifyContent: 'space-between', bgcolor: 'background.paper', p: 1.5, borderRadius: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" fontWeight="bold">MCP Tools:</Typography>
                  {mcpStatus ? (
                    <Chip
                      icon={mcpStatus.available > 0 ? <CheckCircleIcon /> : <ErrorIcon />}
                      label={`${mcpStatus.available}/${mcpStatus.total}`}
                      size="small"
                      color={mcpStatus.available > 0 ? 'success' : 'error'}
                    />
                  ) : mcpError ? (
                    <Chip icon={<ErrorIcon />} label="Error" size="small" color="error" />
                  ) : (
                    <CircularProgress size={16} />
                  )}
                </Box>
                <IconButton size="small" onClick={loadMcpStatus}>
                  <RefreshIcon fontSize="small" />
                </IconButton>
              </Box>

              {/* Token Usage */}
              <Box sx={{ bgcolor: 'background.paper', p: 1.5, borderRadius: 1 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                  <Typography variant="body2" fontWeight="bold">Token Usage:</Typography>
                  <Typography variant="caption" color="textSecondary">
                    ~{estimatedTokens.toLocaleString()} / {maxTokens.toLocaleString()}
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={Math.min((estimatedTokens / maxTokens) * 100, 100)}
                  sx={{ height: 6, borderRadius: 1 }}
                />
              </Box>

              {/* Token Warning Alert */}
              {!validationError && estimatedTokens > maxTokens * 0.8 && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  Conversation is approaching token limit ({estimatedTokens.toLocaleString()} / {maxTokens.toLocaleString()} tokens).
                  {estimatedTokens > maxTokens && ' Consider clearing history or increasing max tokens.'}
                </Alert>
              )}
              
              {/* Model Selection */}
              <FormControl fullWidth size="small">
                <InputLabel>Model</InputLabel>
                <Select value={model} onChange={(e) => setModel(e.target.value)} label="Model">
                  {models.map((m) => (
                    <MenuItem key={m.id} value={m.id}>
                      {m.name}
                    </MenuItem>
                  ))}
                  {models.length === 0 && (
                    <>
                      <MenuItem value="claude-sonnet-4-20250514">DeepTempo 4.5 Sonnet</MenuItem>
                      <MenuItem value="claude-3-5-sonnet-20241022">DeepTempo 3.5 Sonnet</MenuItem>
                      <MenuItem value="claude-3-5-haiku-20241022">DeepTempo 3.5 Haiku</MenuItem>
                    </>
                  )}
                </Select>
              </FormControl>

              {/* Max Tokens */}
              <TextField
                fullWidth
                size="small"
                type="number"
                label="Max Tokens"
                value={maxTokens || ''}
                onChange={(e) => {
                  const value = e.target.value === '' ? 0 : parseInt(e.target.value)
                  setMaxTokens(value)
                }}
                inputProps={{ min: 256, max: 32768, step: 1 }}
                helperText={maxTokensError || "Maximum response length (256-32,768 tokens)"}
                error={!!maxTokensError}
              />

              {/* Extended Thinking */}
              <Box sx={{ width: '100%' }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={enableThinking}
                      onChange={(e) => setEnableThinking(e.target.checked)}
                    />
                  }
                  label="Enable Extended Thinking"
                />
                {enableThinking && (
                  <Box sx={{ mt: 1, width: '100%' }}>
                      <TextField
                        fullWidth
                        size="small"
                        type="number"
                        label="Thinking Budget (k tokens)"
                        value={thinkingBudget || ''}
                        onChange={(e) => {
                          const value = e.target.value === '' ? 0 : parseInt(e.target.value)
                          setThinkingBudget(value)
                        }}
                        inputProps={{ min: 1, max: Math.min(100, Math.floor(maxTokens / 1000) - 1), step: 1 }}
                        helperText={thinkingBudgetError || `Budget for extended thinking (1-${Math.min(100, Math.floor(maxTokens / 1000) - 1)}k tokens, must be < max tokens)`}
                        error={!!thinkingBudgetError}
                      />
                  </Box>
                )}
              </Box>

              {/* Streaming Toggle */}
              <Box sx={{ width: '100%' }}>
                <FormControlLabel
                  control={
                    <Checkbox checked={streaming} onChange={(e) => setStreaming(e.target.checked)} />
                  }
                  label="Enable Streaming"
                />
              </Box>

              {/* System Prompt */}
              <TextField
                fullWidth
                size="small"
                multiline
                rows={3}
                label="System Prompt (Optional)"
                value={systemPrompt}
                onChange={(e) => {
                  const value = e.target.value
                  if (value.length <= 10000) {
                    setSystemPrompt(value)
                  }
                }}
                placeholder="Enter custom system prompt..."
                helperText={systemPromptError || `${systemPrompt.length}/10,000 characters`}
                error={!!systemPromptError}
              />
            </Box>
          </Box>
        </Collapse>

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', position: 'relative', zIndex: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Tabs
              value={currentTab}
              onChange={(_, v) => setCurrentTab(v)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ flexGrow: 1 }}
            >
              {tabs.map((tab, index) => (
                <Tab
                  key={tab.id}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <span>{tab.title}</span>
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleCloseTab(index)
                        }}
                        sx={{ ml: 1 }}
                      >
                        <CloseIcon fontSize="small" />
                      </IconButton>
                    </Box>
                  }
                />
              ))}
            </Tabs>
            <Button 
              startIcon={<AddIcon />} 
              onClick={handleNewTab} 
              size="small" 
              sx={{ m: 1, minWidth: 'auto', whiteSpace: 'nowrap' }}
            >
              New
            </Button>
          </Box>
        </Box>

        {/* Messages */}
        <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
          {tabs[currentTab]?.messages.length === 0 && (
            <Box sx={{ textAlign: 'center', mt: 4 }}>
              <Typography variant="body2" color="textSecondary">
                Begin a conversation with DeepTempo
              </Typography>
              {selectedAgent && (
                <Chip label={`Agent: ${agents.find(a => a.id === selectedAgent)?.name}`} sx={{ mt: 1 }} />
              )}
            </Box>
          )}

          {tabs[currentTab]?.messages.map((msg, index) => (
            <Paper
              key={index}
              sx={{
                p: 2,
                mb: 2,
                bgcolor: msg.role === 'user' ? 'error.dark' : 'background.paper',
                ml: msg.role === 'user' ? 4 : 0,
                mr: msg.role === 'user' ? 0 : 4,
              }}
            >
              <Typography variant="caption" color="textSecondary" sx={{ fontWeight: 'bold' }}>
                {msg.role === 'user' ? 'You' : 'DeepTempo'}
              </Typography>
              <Box sx={{ mt: 1 }}>{renderMessageContent(msg.content)}</Box>
            </Paper>
          ))}

          {loading && (
            <Box display="flex" justifyContent="center" my={2}>
              <CircularProgress size={24} />
            </Box>
          )}
          <div ref={messagesEndRef} />
        </Box>

        {/* Attached Files Preview */}
        {attachedFiles.length > 0 && (
          <Box sx={{ px: 2, pb: 1 }}>
            <List dense>
              {attachedFiles.map((file, index) => (
                <ListItem key={index} sx={{ bgcolor: 'background.paper', mb: 0.5, borderRadius: 1 }}>
                  <ImageIcon sx={{ mr: 1 }} fontSize="small" />
                  <ListItemText primary={file.name} secondary={file.type} />
                  <ListItemSecondaryAction>
                    <IconButton edge="end" size="small" onClick={() => removeFile(index)}>
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        {/* Input */}
        <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', gap: 1, mb: 1, flexWrap: 'wrap', alignItems: 'center' }}>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept="image/*,.txt,.json,.csv,.md"
              multiple
              style={{ display: 'none' }}
            />
            <Button
              variant="outlined"
              size="small"
              startIcon={<AttachFileIcon />}
              onClick={() => fileInputRef.current?.click()}
              disabled={loading}
            >
              Attach
            </Button>
            
            {/* Agent Selection */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <FormControl size="small" sx={{ minWidth: 180 }}>
                <InputLabel>Agent</InputLabel>
                <Select
                  value={selectedAgent}
                  onChange={(e) => setSelectedAgent(e.target.value)}
                  label="Agent"
                >
                  <MenuItem value="">
                    <em>None</em>
                  </MenuItem>
                  {agents.map((agent) => (
                    <MenuItem key={agent.id} value={agent.id}>
                      <Box sx={{ display: 'flex', flexDirection: 'column', py: 0.5 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <span>{agent.icon}</span>
                          <span>{agent.name}</span>
                        </Box>
                        {agent.specialization && (
                          <Typography variant="caption" color="text.secondary" sx={{ ml: 3 }}>
                            {agent.specialization}
                          </Typography>
                        )}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Tooltip title="View all agents and their capabilities">
                <IconButton 
                  size="small" 
                  onClick={() => setAgentInfoDialogOpen(true)}
                  sx={{ ml: -0.5 }}
                >
                  <InfoIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            
            <Button
              variant="outlined"
              size="small"
              onClick={handleClearHistory}
              disabled={tabs[currentTab]?.messages.length === 0}
            >
              Clear History
            </Button>
            <Button
              variant="outlined"
              size="small"
              startIcon={<PdfIcon />}
              onClick={handleGenerateReport}
              disabled={tabs[currentTab]?.messages.length === 0 || loading}
              color="success"
            >
              Generate Report
            </Button>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              disabled={loading}
            />
            <Button
              variant="contained"
              color="error"
              onClick={handleSend}
              disabled={(!input.trim() && attachedFiles.length === 0) || loading || !!validationError}
              endIcon={<SendIcon />}
            >
              Send
            </Button>
          </Box>
        </Box>
      </Box>

      {/* Agent Info Dialog */}
      <Dialog
        open={agentInfoDialogOpen}
        onClose={() => setAgentInfoDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon color="primary" />
            <Typography variant="h6">Available SOC Agents</Typography>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" color="text.secondary" paragraph>
            Choose the right agent for your security task. Each agent is specialized for specific SOC operations.
          </Typography>
          
          <List>
            {agents.map((agent) => (
              <ListItem
                key={agent.id}
                sx={{
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  borderLeft: 3,
                  borderColor: agent.color || 'primary.main',
                  mb: 2,
                  bgcolor: 'background.default',
                  borderRadius: 1,
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="h6" component="span" sx={{ fontSize: '1.5rem' }}>
                    {agent.icon}
                  </Typography>
                  <Box>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {agent.name}
                    </Typography>
                    {agent.specialization && (
                      <Chip
                        label={agent.specialization}
                        size="small"
                        sx={{ 
                          height: 20, 
                          fontSize: '0.7rem',
                          bgcolor: agent.color || 'primary.main',
                          color: 'white'
                        }}
                      />
                    )}
                  </Box>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  {agent.description}
                </Typography>
                {selectedAgent === agent.id && (
                  <Chip
                    label="Currently Selected"
                    size="small"
                    color="success"
                    sx={{ mt: 1 }}
                  />
                )}
              </ListItem>
            ))}
          </List>
          
          {agents.length === 0 && (
            <Alert severity="info">
              No agents available. Please check your backend connection.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAgentInfoDialogOpen(false)} variant="contained">
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Drawer>
  )
}
