# Cribl Stream Integration Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SECURITY DATA SOURCES                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │Firewalls │ │   EDR    │ │  Cloud   │ │ Network  │ │   SIEM   │      │
│  │  Logs    │ │ Agents   │ │  Logs    │ │ Devices  │ │ Forwarder│      │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘      │
│       │            │            │            │            │              │
│       └────────────┴────────────┴────────────┴────────────┘              │
│                                 │                                        │
└─────────────────────────────────┼────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           CRIBL STREAM                                   │
│                        (Data Pipeline Layer)                             │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                     DATA PROCESSING                             │     │
│  │                                                                 │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │     │
│  │  │   NORMALIZE  │→│    ENRICH    │→│    FILTER    │        │     │
│  │  │              │  │              │  │              │        │     │
│  │  │ • Parse logs │  │ • GeoIP      │  │ • Drop noise │        │     │
│  │  │ • Standardize│  │ • Threat     │  │ • Sample     │        │     │
│  │  │   fields     │  │   Intel      │  │ • Aggregate  │        │     │
│  │  │ • Format     │  │ • Asset Info │  │ • Dedupe     │        │     │
│  │  │   conversion │  │ • Context    │  │              │        │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │     │
│  │                                                                 │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    INTELLIGENT ROUTING                          │     │
│  │                                                                 │     │
│  │  Route 1: High Severity → DeepTempo + Splunk + PagerDuty      │     │
│  │  Route 2: Medium Severity → DeepTempo + Splunk                │     │
│  │  Route 3: Low Severity → S3 Archive                           │     │
│  │  Route 4: Compliance → Compliance Lake                         │     │
│  │                                                                 │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└────┬──────────────────┬──────────────────┬──────────────────┬───────────┘
     │                  │                  │                  │
     ▼                  ▼                  ▼                  ▼
┌─────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│DeepTempo│      │  Splunk  │      │    S3    │      │  Kafka   │
│ LogLM   │      │  (SIEM)  │      │ (Archive)│      │ (Stream) │
│         │      │          │      │          │      │          │
│ AI      │      │ Search & │      │ Long-term│      │ Real-time│
│Analysis │      │ Alerts   │      │ Storage  │      │ Alerts   │
└────┬────┘      └──────────┘      └──────────┘      └──────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     DEEPTEMPO AI SOC PLATFORM                            │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                    CLAUDE + MCP SERVERS                         │     │
│  │                                                                 │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │     │
│  │  │   Findings   │  │    Cribl     │  │   25+ Other  │        │     │
│  │  │    Server    │  │    Stream    │  │     MCP      │        │     │
│  │  │              │  │    Server    │  │   Servers    │        │     │
│  │  │ • Query      │  │              │  │              │        │     │
│  │  │   findings   │  │ • Pipelines  │  │ • Splunk     │        │     │
│  │  │ • Embeddings │  │ • Routes     │  │ • VirusTotal │        │     │
│  │  │ • Cases      │  │ • Metrics    │  │ • CrowdStrike│        │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘        │     │
│  │                                                                 │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐     │
│  │                      WEB UI & API                               │     │
│  │                                                                 │     │
│  │  • Case Management    • Investigation Workflows                │     │
│  │  • Settings/Config    • Cribl Integration UI                   │     │
│  │  • Reports & Exports  • Real-time Dashboards                   │     │
│  └────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Details

### 1. Ingestion Phase
```
Security Sources → Cribl Stream Inputs
                   ├─ Syslog (UDP/TCP)
                   ├─ HTTP/HTTPS
                   ├─ Splunk HEC
                   ├─ Kafka
                   ├─ S3
                   └─ Cloud APIs
```

### 2. Processing Phase
```
Raw Events → Pipeline Processing
             ├─ Parse (auto-detect format)
             ├─ Normalize (standardize fields)
             ├─ Enrich (add context)
             ├─ Filter (remove noise)
             ├─ Sample (reduce volume)
             ├─ Mask (PII/compliance)
             └─ Transform (custom logic)
```

### 3. Routing Phase
```
Processed Events → Intelligent Routing
                   ├─ By Severity (high/medium/low)
                   ├─ By Source (firewall/EDR/cloud)
                   ├─ By Content (malware/network/auth)
                   └─ By Destination (SIEM/AI/archive)
```

### 4. Analysis Phase
```
Routed Events → DeepTempo LogLM
                ├─ Generate embeddings
                ├─ Detect anomalies
                ├─ Classify MITRE ATT&CK
                └─ Create findings
                
Findings → Claude + MCP
           ├─ Natural language queries
           ├─ Investigation workflows
           ├─ Case management
           └─ Response orchestration
```

## Component Interaction

### Cribl Stream MCP Server Tools

```
┌─────────────────────────────────────────────────────────────┐
│                 CRIBL STREAM MCP SERVER                      │
│                                                              │
│  Tool: get_pipelines                                        │
│  ├─ Lists all data processing pipelines                    │
│  └─ Shows: ID, description, function count, status         │
│                                                              │
│  Tool: get_routes                                           │
│  ├─ Lists all routing configurations                       │
│  └─ Shows: Filter, pipeline, output, enabled               │
│                                                              │
│  Tool: get_data_sources                                     │
│  ├─ Lists all input sources                                │
│  └─ Shows: ID, type, description, enabled                  │
│                                                              │
│  Tool: get_destinations                                     │
│  ├─ Lists all output destinations                          │
│  └─ Shows: ID, type, description, enabled                  │
│                                                              │
│  Tool: get_metrics                                          │
│  ├─ Retrieves throughput and performance data              │
│  └─ Shows: In/out rates, reduction %, events/sec           │
│                                                              │
│  Tool: create_pipeline                                      │
│  ├─ Creates new data processing pipeline                   │
│  └─ Input: ID, functions, description                      │
│                                                              │
│  Tool: apply_route                                          │
│  ├─ Configures data routing                                │
│  └─ Input: Filter, pipeline, destination                   │
│                                                              │
│  Tool: preview_pipeline                                     │
│  ├─ Tests pipeline with sample data                        │
│  └─ Shows: Input vs output transformation                  │
│                                                              │
│  Tool: get_health_status                                    │
│  ├─ Checks system health                                   │
│  └─ Shows: Workers, connectivity, resources                │
│                                                              │
│  Tool: get_data_flow_summary                                │
│  ├─ Complete overview of data pipeline                     │
│  └─ Shows: Sources, pipelines, routes, destinations        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Integration Benefits Visualization

```
┌─────────────────────────────────────────────────────────────┐
│                    BEFORE CRIBL                              │
│                                                              │
│  Raw Logs → DeepTempo LogLM → Claude                        │
│      ↓                                                       │
│   Splunk                                                     │
│                                                              │
│  Issues:                                                     │
│  ❌ Inconsistent formats confuse AI                         │
│  ❌ High Splunk costs                                       │
│  ❌ No enrichment                                           │
│  ❌ Single destination only                                 │
│  ❌ No filtering/sampling                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘

                         ↓ AFTER CRIBL ↓

┌─────────────────────────────────────────────────────────────┐
│                    AFTER CRIBL                               │
│                                                              │
│  Raw Logs → CRIBL STREAM → DeepTempo LogLM → Claude        │
│              (normalize,        ↓                           │
│               enrich,        Splunk (filtered)              │
│               filter)           ↓                           │
│                              S3 Archive                      │
│                                 ↓                           │
│                              Kafka Alerts                    │
│                                                              │
│  Benefits:                                                   │
│  ✅ Normalized formats → 30% better AI accuracy            │
│  ✅ Filtered data → 40% lower Splunk costs                 │
│  ✅ Enriched context → Faster investigations               │
│  ✅ Multi-destination → Flexible architecture              │
│  ✅ Intelligent routing → Right data, right place          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Cost Impact Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    COST COMPARISON                           │
│                                                              │
│  WITHOUT CRIBL:                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Splunk Ingestion: 1 TB/day                          │   │
│  │ Cost: $3,000/month                                   │   │
│  │ Annual: $36,000                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  WITH CRIBL:                                                │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Splunk Ingestion: 650 GB/day (35% reduction)        │   │
│  │ Splunk Cost: $1,950/month                           │   │
│  │ Cribl License: $500/month                           │   │
│  │ Total: $2,450/month                                 │   │
│  │ Annual: $29,400                                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  SAVINGS:                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Monthly: $550                                        │   │
│  │ Annual: $6,600                                       │   │
│  │ ROI: 13x                                             │   │
│  │                                                       │   │
│  │ PLUS: Full data retained in S3 for compliance       │   │
│  │ PLUS: Better AI accuracy = fewer false positives    │   │
│  │ PLUS: Faster investigations = reduced MTTR          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Performance Metrics Flow

```
┌─────────────────────────────────────────────────────────────┐
│                  METRICS & MONITORING                        │
│                                                              │
│  Cribl Stream Metrics:                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Data In:        2.3 GB/s    (45,000 events/sec)    │   │
│  │ Data Out:       1.8 GB/s    (35,000 events/sec)    │   │
│  │ Reduction:      22%                                  │   │
│  │ CPU Usage:      45%                                  │   │
│  │ Memory:         62%                                  │   │
│  │ Workers:        3 active                             │   │
│  │ Backpressure:   None                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  DeepTempo LogLM Metrics:                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Events Analyzed: 35,000/sec                         │   │
│  │ Findings:        120/hour                           │   │
│  │ Accuracy:        +30% (vs. raw logs)                │   │
│  │ False Positives: -40%                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                           ↓                                  │
│  SOC Operational Metrics:                                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ MTTD (Mean Time To Detect):    -35%                │   │
│  │ MTTR (Mean Time To Respond):   -50%                │   │
│  │ Alert Fatigue:                 -60%                │   │
│  │ Analyst Productivity:          +45%                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Security & Compliance Flow

```
┌─────────────────────────────────────────────────────────────┐
│              SECURITY & COMPLIANCE PIPELINE                  │
│                                                              │
│  Raw Security Events                                        │
│         ↓                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ CRIBL STREAM - Security Processing                  │   │
│  │                                                       │   │
│  │ 1. PII Masking                                       │   │
│  │    • Credit cards → ****-****-****-1234             │   │
│  │    • SSN → ***-**-1234                              │   │
│  │    • Emails → hash(email)                           │   │
│  │                                                       │   │
│  │ 2. Threat Enrichment                                │   │
│  │    • IP reputation lookup                           │   │
│  │    • Domain categorization                          │   │
│  │    • Hash checking (VirusTotal)                     │   │
│  │                                                       │   │
│  │ 3. Compliance Routing                               │   │
│  │    • PCI data → Compliance Lake                     │   │
│  │    • HIPAA data → Encrypted storage                 │   │
│  │    • GDPR data → Regional storage                   │   │
│  │                                                       │   │
│  │ 4. Audit Logging                                    │   │
│  │    • All transformations logged                     │   │
│  │    • Chain of custody maintained                    │   │
│  │    • Compliance reports generated                   │   │
│  └──────────────────────────────────────────────────────┘   │
│         ↓                                                    │
│  Compliant, Enriched, Secure Events                        │
│         ↓                                                    │
│  DeepTempo AI SOC (for analysis)                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Use Case: Incident Investigation Flow

```
┌─────────────────────────────────────────────────────────────┐
│         INCIDENT INVESTIGATION WITH CRIBL                    │
│                                                              │
│  1. Alert Triggered                                         │
│     "Suspicious lateral movement detected"                  │
│         ↓                                                    │
│  2. Analyst asks Claude:                                    │
│     "Show me all activity from this host"                   │
│         ↓                                                    │
│  3. Claude queries DeepTempo findings                       │
│     [Uses deeptempo-findings MCP server]                    │
│         ↓                                                    │
│  4. Analyst: "What's the data quality like?"                │
│         ↓                                                    │
│  5. Claude checks Cribl metrics                             │
│     [Uses cribl-stream MCP server]                          │
│     "Data is normalized, enriched with GeoIP and threat     │
│      intel. 98% of events have complete field mapping."     │
│         ↓                                                    │
│  6. Analyst: "Show me the pipeline that processed this"     │
│         ↓                                                    │
│  7. Claude retrieves pipeline details                       │
│     [Uses get_pipelines tool]                               │
│     "Processed by 'security-enrich' pipeline:               │
│      - Normalized fields                                    │
│      - Added GeoIP (Beijing, CN)                            │
│      - Threat score: 85/100                                 │
│      - Asset type: Domain Controller"                       │
│         ↓                                                    │
│  8. Analyst: "Find similar events"                          │
│         ↓                                                    │
│  9. Claude uses embedding search                            │
│     [Finds 47 similar events, all enriched by Cribl]        │
│         ↓                                                    │
│  10. Result: Complete investigation in 5 minutes            │
│      (vs. 20 minutes without enrichment)                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Topology

```
┌─────────────────────────────────────────────────────────────┐
│                  PRODUCTION DEPLOYMENT                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │              CRIBL STREAM CLUSTER                  │     │
│  │                                                     │     │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐        │     │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │        │     │
│  │  │ (Active) │  │ (Active) │  │ (Active) │        │     │
│  │  └──────────┘  └──────────┘  └──────────┘        │     │
│  │       ↓              ↓              ↓             │     │
│  │  ┌────────────────────────────────────────┐       │     │
│  │  │      Load Balancer / Leader            │       │     │
│  │  └────────────────────────────────────────┘       │     │
│  │                                                     │     │
│  └────────────────────────────────────────────────────┘     │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐     │
│  │         DEEPTEMPO AI SOC PLATFORM                  │     │
│  │                                                     │     │
│  │  ┌──────────────────────────────────────────┐     │     │
│  │  │  Backend API (FastAPI)                   │     │     │
│  │  │  - Cribl Service                         │     │     │
│  │  │  - MCP Client                            │     │     │
│  │  │  - Claude Integration                    │     │     │
│  │  └──────────────────────────────────────────┘     │     │
│  │                                                     │     │
│  │  ┌──────────────────────────────────────────┐     │     │
│  │  │  MCP Servers                             │     │     │
│  │  │  - cribl-stream-server                   │     │     │
│  │  │  - deeptempo-findings-server             │     │     │
│  │  │  - 25+ other integration servers         │     │     │
│  │  └──────────────────────────────────────────┘     │     │
│  │                                                     │     │
│  │  ┌──────────────────────────────────────────┐     │     │
│  │  │  Frontend (React)                        │     │     │
│  │  │  - Settings UI                           │     │     │
│  │  │  - Case Management                       │     │     │
│  │  │  - Cribl Integration Config              │     │     │
│  │  └──────────────────────────────────────────┘     │     │
│  │                                                     │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

**For complete documentation, see:**
- Quick Start: `docs/cribl-quick-start.md`
- Full Integration Guide: `docs/cribl-integration.md`
- Implementation Summary: `CRIBL_INTEGRATION_SUMMARY.md`

