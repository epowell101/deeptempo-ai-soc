import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Findings API
export const findingsApi = {
  getAll: (params?: {
    severity?: string
    data_source?: string
    cluster_id?: number
    min_anomaly_score?: number
    limit?: number
    force_refresh?: boolean
  }) => api.get('/findings/', { params }),
  
  getById: (id: string) => api.get(`/findings/${id}`),
  
  getSummary: () => api.get('/findings/stats/summary'),
  
  export: (format: 'json' | 'jsonl' = 'json') =>
    api.post('/findings/export', null, { params: { output_format: format } }),
}

// Cases API
export const casesApi = {
  getAll: (params?: {
    status?: string
    priority?: string
    force_refresh?: boolean
  }) => api.get('/cases/', { params }),
  
  getById: (id: string) => api.get(`/cases/${id}`),
  
  create: (data: {
    title: string
    description?: string
    finding_ids: string[]
    priority?: string
    status?: string
  }) => api.post('/cases/', data),
  
  update: (id: string, data: {
    title?: string
    description?: string
    status?: string
    priority?: string
    notes?: string
    assignee?: string
  }) => api.patch(`/cases/${id}`, data),
  
  delete: (id: string) => api.delete(`/cases/${id}`),
  
  addActivity: (id: string, data: {
    activity_type: string
    description: string
    details?: any
  }) => api.post(`/cases/${id}/activities`, data),
  
  addResolutionStep: (id: string, data: {
    description: string
    action_taken: string
    result?: string
  }) => api.post(`/cases/${id}/resolution-steps`, data),
  
  addFinding: (id: string, finding_id: string) =>
    api.post(`/cases/${id}/findings/${finding_id}`),
  
  removeFinding: (id: string, finding_id: string) =>
    api.delete(`/cases/${id}/findings/${finding_id}`),
  
  generateReport: (id: string) => api.post(`/cases/${id}/generate-report`),
  
  getSummary: () => api.get('/cases/stats/summary'),
}

// MCP Servers API
export const mcpApi = {
  listServers: () => api.get('/mcp/servers'),
  
  getStatuses: () => api.get('/mcp/servers/status'),
  
  getServerStatus: (name: string) => api.get(`/mcp/servers/${name}/status`),
  
  startServer: (name: string) => api.post(`/mcp/servers/${name}/start`),
  
  stopServer: (name: string) => api.post(`/mcp/servers/${name}/stop`),
  
  startAll: () => api.post('/mcp/servers/start-all'),
  
  stopAll: () => api.post('/mcp/servers/stop-all'),
  
  getLogs: (name: string, lines: number = 100) =>
    api.get(`/mcp/servers/${name}/logs`, { params: { lines } }),
  
  testServer: (name: string) => api.get(`/mcp/servers/${name}/test`),
}

// Claude API
export const claudeApi = {
  chat: (data: {
    messages: Array<{ 
      role: string
      content: string | Array<{
        type: string
        text?: string
        source?: {
          type: string
          media_type: string
          data: string
        }
      }>
    }>
    system_prompt?: string
    model?: string
    max_tokens?: number
    enable_thinking?: boolean
    thinking_budget?: number
    agent_id?: string
    streaming?: boolean
  }) => api.post('/claude/chat', data),
  
  chatStream: (data: {
    messages: Array<{ 
      role: string
      content: string | Array<{
        type: string
        text?: string
        source?: {
          type: string
          media_type: string
          data: string
        }
      }>
    }>
    system_prompt?: string
    model?: string
    max_tokens?: number
    enable_thinking?: boolean
    thinking_budget?: number
    agent_id?: string
  }) => api.post('/claude/chat/stream', data, {
    responseType: 'stream',
    headers: {
      'Accept': 'text/event-stream',
    }
  }),
  
  uploadFile: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/claude/upload-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
  },
  
  getModels: () => api.get('/claude/models'),
  
  analyzeFinding: (finding_id: string, context?: string) =>
    api.post('/claude/analyze-finding', null, {
      params: { finding_id, context },
    }),
  
  generateChatReport: (data: {
    tab_title: string
    messages: Array<{
      role: string
      content: string | Array<{
        type: string
        text?: string
        source?: any
      }>
    }>
    notes?: string
  }) => api.post('/claude/generate-chat-report', data),
}

// Agents API
export const agentsApi = {
  listAgents: () => api.get('/agents/agents'),
  
  getAgent: (agent_id: string) => api.get(`/agents/agents/${agent_id}`),
  
  setCurrentAgent: (agent_id: string) => 
    api.post('/agents/agents/set-current', null, { params: { agent_id } }),
  
  startInvestigation: (data: {
    finding_id: string
    agent_id?: string
    additional_context?: string
  }) => api.post('/agents/agents/investigate', data),
}

// Config API
export const configApi = {
  getClaude: () => api.get('/config/claude'),
  setClaude: (api_key: string) => api.post('/config/claude', { api_key }),
  
  getS3: () => api.get('/config/s3'),
  setS3: (data: {
    bucket_name: string
    region: string
    access_key_id: string
    secret_access_key: string
    findings_path?: string
    cases_path?: string
  }) => api.post('/config/s3', data),
  
  
  
  getIntegrations: () => api.get('/config/integrations'),
  setIntegrations: (data: {
    enabled_integrations: string[]
    integrations: Record<string, any>
  }) => api.post('/config/integrations', data),
  
  getGeneral: () => api.get('/config/general'),
  setGeneral: (data: {
    auto_start_sync: boolean
    show_notifications: boolean
    theme: string
    enable_keyring: boolean
  }) => api.post('/config/general', data),
  
  getTheme: () => api.get('/config/theme'),
  setTheme: (theme: string) => api.post('/config/theme', { theme }),
  
  getGitHub: () => api.get('/config/github'),
  setGitHub: (token: string) => api.post('/config/github', { token }),
  
  getPostgreSQL: () => api.get('/config/postgresql'),
  setPostgreSQL: (connection_string: string) => api.post('/config/postgresql', { connection_string }),
}

// Storage API
export const storageApi = {
  getStatus: () => api.get('/storage/status'),
  getHealth: () => api.get('/storage/health'),
  reconnect: () => api.post('/storage/reconnect'),
  switchBackend: (backend: string) => api.post('/storage/switch-backend', { backend }),
}

// Timesketch API
export const timesketchApi = {
  getStatus: () => api.get('/timesketch/status'),
  
  listSketches: () => api.get('/timesketch/sketches'),
  
  createSketch: (data: { name: string; description?: string }) =>
    api.post('/timesketch/sketches', data),
  
  getSketch: (id: number) => api.get(`/timesketch/sketches/${id}`),
  
  getDockerStatus: () => api.get('/timesketch/docker/status'),
  
  startDocker: (port: number = 5000) =>
    api.post('/timesketch/docker/start', null, { params: { port } }),
  
  stopDocker: () => api.post('/timesketch/docker/stop'),
  
  exportToTimesketch: (data: {
    sketch_id?: string
    sketch_name?: string
    sketch_description?: string
    finding_ids?: string[]
    case_id?: string
    timeline_name: string
  }) => api.post('/timesketch/export', data),
}

// ATT&CK API
export const attackApi = {
  getLayer: () => api.get('/attack/layer'),
  
  getTechniqueRollup: (min_confidence: number = 0.0) =>
    api.get('/attack/techniques/rollup', { params: { min_confidence } }),
  
  getFindingsByTechnique: (technique_id: string) =>
    api.get(`/attack/techniques/${technique_id}/findings`),
  
  getTacticsSummary: () => api.get('/attack/tactics/summary'),
}

export default api

