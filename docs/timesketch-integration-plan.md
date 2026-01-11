# Timesketch Integration Plan - DeepTempo AI SOC

## Executive Summary

This plan outlines a comprehensive integration of Timesketch into the DeepTempo AI SOC desktop application. Timesketch will enhance the application with advanced timeline analysis, collaborative investigation capabilities, forensic timeline visualization, and powerful search/query features.

## Integration Goals

1. **Enhanced Timeline Visualization**: Replace basic timeline arrays with interactive Timesketch timelines
2. **Collaborative Investigations**: Enable multi-user case collaboration through Timesketch sketches
3. **Advanced Analysis**: Leverage Timesketch analyzers and LLM features
4. **Forensic Correlation**: Better identify relationships between findings and events
5. **Evidence Management**: Improved evidence organization and analysis
6. **Export/Import Capabilities**: Seamless data flow between DeepTempo and Timesketch

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│              Enhanced Desktop Application                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │ Timesketch   │  │  Timeline    │          │
│  │  (Enhanced)  │  │  Integration │  │  Visualizer  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    New Services Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Timesketch   │  │ Timeline     │  │ Sketch       │          │
│  │   Service    │  │   Service    │  │   Manager    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Timesketch Server                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Sketches   │  │  Analyzers   │  │  Timeline    │          │
│  │   (Cases)    │  │  (LLM/AI)    │  │  Analysis    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### Phase 1: Core Integration Infrastructure

#### 1.1 Timesketch Service (`services/timesketch_service.py`)

**Purpose**: Primary interface for Timesketch API communication.

**Key Features**:
- Authentication and session management
- Sketch creation and management
- Timeline event import/export
- Search and query execution
- Analyzer execution
- Collaboration features

**Methods**:
```python
class TimesketchService:
    def __init__(self, server_url, username, password)
    def authenticate() -> bool
    def create_sketch(name, description) -> str  # Returns sketch_id
    def get_sketch(sketch_id) -> dict
    def list_sketches() -> list
    def add_timeline(sketch_id, timeline_name, events) -> str
    def search_sketch(sketch_id, query) -> list
    def run_analyzer(sketch_id, analyzer_name, timeline_id) -> dict
    def export_timeline(sketch_id, timeline_id, format='json') -> bytes
    def import_timeline(sketch_id, timeline_data, format='json') -> str
    def get_timeline_events(sketch_id, timeline_id, filters) -> list
    def add_comment(sketch_id, event_id, comment) -> bool
    def add_label(sketch_id, event_id, label) -> bool
    def get_sketch_analyses(sketch_id) -> list
```

**Dependencies**:
- `timesketch-api-client` (Python client library)
- `requests` for HTTP communication
- Authentication token management

#### 1.2 Timeline Service (`services/timeline_service.py`)

**Purpose**: Convert DeepTempo findings and cases into Timesketch timeline format.

**Key Features**:
- Transform findings to timeline events
- Generate timeline from case data
- Merge multiple findings into coherent timeline
- Add metadata and context to events

**Methods**:
```python
class TimelineService:
    def findings_to_timeline_events(findings: list) -> list
    def case_to_timeline_events(case: dict, findings: list) -> list
    def create_event_timeline(findings: list, case: dict) -> dict
    def enrich_event_with_context(event: dict, finding: dict) -> dict
    def generate_timeline_summary(events: list) -> dict
    def filter_events_by_timeframe(events: list, start, end) -> list
    def correlate_events(events: list) -> list
```

**Event Format**:
```json
{
    "timestamp": "2026-01-10T14:32:18Z",
    "timestamp_desc": "Event Time",
    "message": "C2 beaconing detected from workstation-042",
    "source": "DeepTempo Finding",
    "source_short": "DT",
    "data_type": "security:finding",
    "finding_id": "f-20260110-abc123",
    "case_id": "case-2026-01-10-xyz",
    "severity": "high",
    "mitre_techniques": ["T1071.001", "T1573.001"],
    "entity_context": {
        "src_ip": "10.0.1.15",
        "dst_ip": "203.0.113.50",
        "hostname": "workstation-042"
    }
}
```

#### 1.3 Sketch Manager Service (`services/sketch_manager.py`)

**Purpose**: Manage the relationship between DeepTempo cases and Timesketch sketches.

**Key Features**:
- Map cases to sketches (1:1 relationship)
- Sync case updates to sketches
- Track sketch metadata
- Handle sketch permissions

**Methods**:
```python
class SketchManager:
    def create_sketch_for_case(case: dict) -> str
    def get_sketch_for_case(case_id: str) -> Optional[str]
    def sync_case_to_sketch(case_id: str) -> bool
    def update_sketch_from_case(case: dict, sketch_id: str) -> bool
    def link_findings_to_sketch(finding_ids: list, sketch_id: str) -> bool
    def get_sketch_metadata(sketch_id: str) -> dict
    def archive_sketch(sketch_id: str) -> bool
```

**Storage**:
- New file: `data/sketch_mappings.json`
- Maps `case_id` → `sketch_id`
- Stores sketch metadata and sync status

### Phase 2: UI Components

#### 2.1 Timesketch Configuration (`ui/timesketch_config.py`)

**Purpose**: Configure Timesketch server connection.

**Features**:
- Server URL input
- Authentication (username/password or API token)
- Connection testing
- Sketch default settings
- Auto-sync preferences

**UI Elements**:
- Server URL field
- Authentication method selection
- Credentials input (password field)
- Test Connection button
- Auto-sync toggle
- Default sketch settings

#### 2.2 Timeline Visualizer Widget (`ui/widgets/timesketch_timeline.py`)

**Purpose**: Display interactive timeline for cases using Timesketch data.

**Features**:
- Timeline visualization (using Timesketch API or embedded viewer)
- Event filtering and search
- Zoom and pan controls
- Event details on click
- Correlation view
- Export timeline

**Integration Options**:
- **Option A**: Embed Timesketch web UI in QWebEngineView
- **Option B**: Build custom timeline widget using Timesketch API data
- **Option C**: Link to Timesketch web interface (open in browser)

**Recommended**: Hybrid approach - Custom widget for basic view, link to full Timesketch UI for advanced features.

#### 2.3 Sketch Manager Widget (`ui/widgets/sketch_manager.py`)

**Purpose**: Manage Timesketch sketches associated with cases.

**Features**:
- List all sketches
- Show sketch status (synced, pending, error)
- Create new sketch from case
- Sync case to sketch
- Open sketch in Timesketch
- View sketch analytics

**UI Elements**:
- Sketch list table (Case, Sketch Name, Status, Last Sync, Actions)
- Create Sketch button
- Sync All button
- Open in Timesketch button
- Refresh button

#### 2.4 Enhanced Case Widget (`ui/widgets/case_list.py` - Enhanced)

**New Features**:
- "Export to Timesketch" button for each case
- "View Timeline" button (opens timeline visualizer)
- Sketch status indicator
- Auto-sync indicator
- Timeline preview

#### 2.5 Enhanced Finding Widget (`ui/widgets/finding_list.py` - Enhanced)

**New Features**:
- "Add to Timesketch" button (adds finding to active sketch)
- Timeline correlation view
- Event relationship visualization
- Timesketch search integration

#### 2.6 Timeline Analysis Widget (`ui/widgets/timeline_analysis.py`)

**Purpose**: Advanced timeline analysis and correlation.

**Features**:
- Event correlation analysis
- Pattern detection
- Attack chain visualization
- Time-based filtering
- Event grouping
- Statistical analysis

### Phase 3: Enhanced Features

#### 3.1 Auto-Sync Functionality

**Purpose**: Automatically sync cases and findings to Timesketch.

**Implementation**:
- Background sync service
- Configurable sync intervals
- Conflict resolution
- Sync status tracking
- Error handling and retry logic

**Sync Triggers**:
- Case created → Create new sketch
- Case updated → Update sketch
- Finding added to case → Add timeline event
- Finding updated → Update timeline event
- Manual sync button

#### 3.2 Timesketch Analyzers Integration

**Purpose**: Run Timesketch analyzers on imported data.

**Available Analyzers**:
- Sigma analyzer (detection rules)
- Feature extraction analyzer
- HashR analyzer
- LLM analyzer (log analysis with AI)
- Tagger analyzer

**Implementation**:
- Analyzer selection UI
- Run analyzer on sketch/timeline
- Display analyzer results
- Import results back to case notes

#### 3.3 Collaborative Features

**Purpose**: Enable team collaboration through Timesketch.

**Features**:
- Share sketches with team members
- View collaborator comments
- Real-time updates (polling or webhooks)
- Activity feed
- Permission management

#### 3.4 Advanced Search Integration

**Purpose**: Use Timesketch's powerful search capabilities.

**Features**:
- Timesketch query builder UI
- Search across all sketches
- Save search queries
- Search result export
- Integration with finding search

**Query Examples**:
- `data_type:"security:finding" AND severity:"high"`
- `mitre_techniques:"T1071.001" AND timestamp:[2026-01-01 TO 2026-01-10]`
- `entity_context.src_ip:"10.0.1.15"`

#### 3.5 Evidence Correlation

**Purpose**: Correlate findings and events across timelines.

**Features**:
- Automatic event correlation
- Relationship graph visualization
- Timeline merging
- Cross-case analysis
- Pattern detection

### Phase 4: Data Integration

#### 4.1 Finding to Timeline Event Mapping

**Mapping Rules**:
```
Finding → Timeline Event:
- timestamp → timestamp
- finding_id → event_id (custom field)
- severity → tags/labels
- data_source → source
- entity_context → event attributes
- mitre_predictions → tags
- anomaly_score → custom field
- cluster_id → tags
```

#### 4.2 Case to Sketch Mapping

**Mapping Rules**:
```
Case → Sketch:
- case_id → sketch name prefix
- title → sketch name
- description → sketch description
- finding_ids → timeline events
- timeline → additional events
- notes → sketch comments
- tags → sketch tags
```

#### 4.3 Bidirectional Sync

**DeepTempo → Timesketch**:
- Findings → Timeline events
- Cases → Sketches
- Notes → Comments
- Tags → Labels

**Timesketch → DeepTempo**:
- Analyzer results → Case notes
- Comments → Case notes
- Labels → Case tags
- Search results → Finding filters

### Phase 5: Configuration and Setup

#### 5.1 Timesketch Server Setup

**Requirements**:
- Timesketch server (Docker or standalone)
- API access enabled
- User account with appropriate permissions
- Network connectivity from desktop app

**Configuration File** (`config/timesketch.json`):
```json
{
    "server_url": "https://timesketch.example.com",
    "username": "analyst",
    "api_token": "encrypted_token",
    "verify_ssl": true,
    "auto_sync": true,
    "sync_interval": 300,
    "default_sketch_settings": {
        "permissions": ["read", "write"],
        "analyzer_auto_run": false
    }
}
```

#### 5.2 Installation Updates

**New Dependencies**:
- `timesketch-api-client` (if available)
- Or `requests` + custom API client
- `cryptography` for token encryption

**Install Script Updates**:
- Add Timesketch server setup instructions
- Add API client installation
- Add configuration wizard step

### Phase 6: Enhanced Reporting

#### 6.1 Timeline Reports

**Purpose**: Generate PDF reports with timeline visualizations.

**Features**:
- Include Timesketch timeline screenshots
- Timeline event summaries
- Correlation analysis in reports
- Analyzer results in reports

#### 6.2 Sketch Export

**Purpose**: Export sketches for sharing or archiving.

**Features**:
- Export sketch as JSON
- Export timeline as CSV/JSON
- Generate sketch summary report
- Archive sketches

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Create Timesketch service with basic API client
- [ ] Create timeline service for data transformation
- [ ] Create sketch manager service
- [ ] Add Timesketch configuration UI
- [ ] Add configuration storage

### Phase 2: Basic Integration (Week 3-4)
- [ ] Add "Export to Timesketch" to case widget
- [ ] Implement case-to-sketch creation
- [ ] Implement findings-to-timeline export
- [ ] Add sketch manager widget
- [ ] Basic timeline visualization

### Phase 3: Enhanced Features (Week 5-6)
- [ ] Auto-sync functionality
- [ ] Timeline visualizer widget
- [ ] Enhanced case widget with timeline view
- [ ] Search integration
- [ ] Analyzer integration

### Phase 4: Advanced Features (Week 7-8)
- [ ] Collaborative features
- [ ] Evidence correlation
- [ ] Advanced timeline analysis
- [ ] Bidirectional sync
- [ ] Enhanced reporting

### Phase 5: Polish and Testing (Week 9-10)
- [ ] Error handling and recovery
- [ ] Performance optimization
- [ ] User documentation
- [ ] Testing and bug fixes
- [ ] Deployment guide

## File Structure Changes

```
deeptempo-ai-soc/
├── services/
│   ├── timesketch_service.py      # NEW: Timesketch API client
│   ├── timeline_service.py        # NEW: Timeline transformation
│   └── sketch_manager.py          # NEW: Sketch-case mapping
├── ui/
│   ├── timesketch_config.py       # NEW: Configuration dialog
│   └── widgets/
│       ├── timesketch_timeline.py # NEW: Timeline visualizer
│       ├── sketch_manager.py     # NEW: Sketch management
│       └── timeline_analysis.py   # NEW: Advanced analysis
├── data/
│   └── sketch_mappings.json       # NEW: Case-sketch mappings
├── config/
│   └── timesketch.json            # NEW: Timesketch configuration
└── requirements.txt               # UPDATED: Add timesketch dependencies
```

## Dependencies to Add

```python
# requirements.txt additions
timesketch-api-client>=2024.1.0  # If available
# OR
requests>=2.31.0                   # For custom API client
cryptography>=41.0.0               # For token encryption
```

## User Workflows

### Workflow 1: Create Case and Export to Timesketch

1. User creates case in DeepTempo
2. User adds findings to case
3. User clicks "Export to Timesketch"
4. System creates sketch in Timesketch
5. System exports findings as timeline events
6. System links case to sketch
7. User can view timeline in DeepTempo or Timesketch

### Workflow 2: Analyze Timeline in Timesketch

1. User opens case with Timesketch integration
2. User clicks "View Timeline"
3. Timeline visualizer shows events
4. User runs analyzer (e.g., Sigma rules)
5. Analyzer results imported back to case notes
6. User updates case based on analysis

### Workflow 3: Collaborative Investigation

1. Analyst A creates case and exports to Timesketch
2. Analyst B accesses same sketch in Timesketch
3. Analyst B adds comments and labels
4. DeepTempo syncs updates back to case
5. Both analysts see updates in real-time

### Workflow 4: Advanced Correlation

1. User has multiple cases with findings
2. User runs correlation analysis
3. System identifies related events across cases
4. System creates correlation timeline
5. User views relationship graph
6. User creates new case for correlated findings

## Benefits Summary

1. **Better Visualization**: Interactive timelines vs. static arrays
2. **Collaboration**: Multi-user investigations
3. **Advanced Analysis**: Timesketch analyzers and AI features
4. **Forensic Capabilities**: Professional timeline analysis
5. **Scalability**: Handle large volumes of events
6. **Integration**: Works with existing forensic tools
7. **Search**: Powerful query capabilities
8. **Standards**: Industry-standard timeline format

## Technical Considerations

### Performance
- Lazy loading of timeline events
- Caching of sketch metadata
- Background sync to avoid UI blocking
- Pagination for large timelines

### Security
- Encrypted API token storage
- Secure authentication
- Permission management
- Audit logging

### Error Handling
- Connection retry logic
- Sync conflict resolution
- Graceful degradation if Timesketch unavailable
- User-friendly error messages

### Compatibility
- Support Timesketch API v1
- Handle API version differences
- Fallback to manual export if API unavailable

## Success Metrics

- Cases successfully synced to Timesketch: >95%
- Timeline events exported correctly: >99%
- User adoption of Timesketch features: >70%
- Reduction in investigation time: 30-40%
- Improved case correlation: Measurable increase

## Future Enhancements

1. **Real-time Sync**: WebSocket integration for live updates
2. **Mobile Support**: Timesketch mobile app integration
3. **AI Enhancement**: Leverage Timesketch LLM features more deeply
4. **Custom Analyzers**: Create DeepTempo-specific analyzers
5. **Plugin System**: Allow custom Timesketch integrations
6. **Multi-Server**: Support multiple Timesketch instances
7. **Offline Mode**: Queue syncs when offline

## Conclusion

This integration will transform DeepTempo AI SOC from a single-user desktop application into a collaborative, enterprise-grade security operations platform. Timesketch brings professional forensic timeline analysis capabilities that complement DeepTempo's AI-powered detection and Claude's reasoning capabilities.

The phased approach allows for incremental implementation and testing, ensuring stability while adding powerful new features.

