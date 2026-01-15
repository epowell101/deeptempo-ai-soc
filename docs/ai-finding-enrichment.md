# AI Finding Enrichment Feature

## Overview

The AI Finding Enrichment feature automatically generates comprehensive, AI-powered analysis for security findings. This enrichment is generated once when a finding is first opened and cached in the database for instant retrieval on subsequent views.

## Key Features

### 1. **One-Time Generation with Caching**
- AI enrichment is generated automatically when a finding is opened for the first time
- Results are cached in the database to avoid redundant API calls
- Subsequent views load enrichment instantly from cache
- Option to force regeneration if needed

### 2. **Comprehensive Analysis**
The AI enrichment provides:
- **Threat Summary**: Clear, concise overview of the security threat
- **Threat Type**: Classification (e.g., Data Exfiltration, Lateral Movement, etc.)
- **Risk Level**: Critical, High, Medium, or Low assessment
- **Potential Impact**: Detailed explanation of business impact
- **Recommended Actions**: Prioritized list of immediate steps to take
- **Investigation Questions**: Key questions for deeper analysis
- **Related MITRE ATT&CK Techniques**: Relevant techniques with explanations
- **Timeline Context**: Sequence of events and attack progression
- **Business Context**: How the finding relates to normal operations
- **Indicators of Compromise**: Malicious IPs, domains, users, processes
- **Confidence Score**: AI's confidence in its analysis (0-100%)

### 3. **Rich UI Presentation**
- Clean, organized accordion-style interface
- Color-coded severity and risk indicators
- Expandable sections for detailed information
- Loading indicators during generation
- Error handling for missing Claude API configuration

## Implementation Details

### Database Schema

#### Added Field to `findings` Table
```sql
ALTER TABLE findings 
ADD COLUMN ai_enrichment JSONB;

CREATE INDEX idx_finding_has_enrichment 
ON findings ((ai_enrichment IS NOT NULL));
```

The `ai_enrichment` column stores:
- All analysis components (threat_summary, risk_level, etc.)
- Generation metadata (generated_at, model version)
- Confidence scores and additional notes

### Backend API

#### New Endpoint: `POST /api/findings/{finding_id}/enrich`

**Parameters:**
- `finding_id`: The finding to enrich
- `force_regenerate`: Optional boolean to force regeneration

**Response:**
```json
{
  "finding_id": "f-20260114-001",
  "cached": false,
  "enrichment": {
    "threat_summary": "...",
    "threat_type": "Data Exfiltration",
    "risk_level": "High",
    "potential_impact": "...",
    "recommended_actions": ["..."],
    "investigation_questions": ["..."],
    "related_techniques": [...],
    "indicators": {...},
    "confidence_score": 0.85,
    "generated_at": "2026-01-14T12:00:00Z",
    "model": "claude-sonnet-4-20250514"
  }
}
```

**Behavior:**
1. Checks if enrichment exists in database
2. If exists and `force_regenerate=false`, returns cached version
3. If not exists, generates using Claude AI with comprehensive prompt
4. Saves enrichment to database
5. Returns enrichment data

### Frontend Components

#### Updated `FindingDetailDialog.tsx`
- Added enrichment state and loading state
- Automatically loads enrichment when dialog opens
- Displays comprehensive enrichment in organized sections
- Uses Material-UI Accordions for collapsible sections
- Shows loading spinner during generation
- Handles errors gracefully

#### Updated `api.ts`
Added new methods to `findingsApi`:
```typescript
getEnrichment: (id: string, force_regenerate: boolean = false) =>
  api.post(`/findings/${id}/enrich`, null, { params: { force_regenerate } })
```

## Usage

### For End Users

1. **Open any finding** in the UI (click "View" button)
2. **Wait a moment** for AI analysis to generate (first time only)
3. **Review the enrichment** in the "AI-Generated Analysis" section
4. **Expand sections** of interest for detailed information
5. **Close and reopen** - enrichment loads instantly from cache

### For Developers

#### Accessing Enrichment via API
```bash
# Get or generate enrichment
curl -X POST "http://localhost:8000/api/findings/f-001/enrich"

# Force regeneration
curl -X POST "http://localhost:8000/api/findings/f-001/enrich?force_regenerate=true"
```

#### Accessing Enrichment in Code
```python
from services.database_data_service import DatabaseDataService

data_service = DatabaseDataService()
finding = data_service.get_finding("f-001")

# Check if enrichment exists
if finding.get('ai_enrichment'):
    enrichment = finding['ai_enrichment']
    threat_summary = enrichment['threat_summary']
    risk_level = enrichment['risk_level']
```

## AI Prompt Engineering

The enrichment uses a carefully crafted prompt that:
- Provides comprehensive finding context (severity, entities, techniques, etc.)
- Requests structured JSON output for consistent parsing
- Emphasizes actionable, specific recommendations
- Focuses on SOC analyst decision-making needs
- Includes business and timeline context

## Performance Considerations

### First View
- **Time**: ~3-8 seconds (depending on finding complexity)
- **Cost**: 1 Claude API call per finding
- **User Experience**: Loading indicator shown

### Subsequent Views
- **Time**: <100ms (database query)
- **Cost**: No API calls
- **User Experience**: Instant display

### Database Impact
- **Storage**: ~2-5KB per enrichment (JSONB compressed)
- **Indexed**: Fast lookup with boolean index
- **Efficient**: No duplicate generations

## Configuration

### Requirements
- Claude API key configured in system settings
- PostgreSQL database (for JSONB storage)
- Model: claude-sonnet-4-20250514

### Settings Location
- UI: Settings → Integrations → Claude API
- Environment: `ANTHROPIC_API_KEY` in `.env`

## Migration

### Running the Migration
```bash
# Database migration is in: database/init/003_add_ai_enrichment.sql
# If using PostgreSQL, it will auto-apply on next database service start

# Or manually apply:
psql -d deeptempo_soc -f database/init/003_add_ai_enrichment.sql
```

### Existing Findings
- Enrichment generates on-demand (lazy loading)
- No need to bulk-process existing findings
- Each finding enriched when first viewed

## Error Handling

### Claude API Not Configured
- UI shows info message: "AI enrichment is not available"
- No error thrown, graceful degradation
- Finding details still fully accessible

### Claude API Error
- Error logged on backend
- User sees error notification
- Finding details remain accessible
- Can retry by reopening finding

### JSON Parse Error
- Fallback structure created with raw response
- User still gets some analysis
- Confidence score reduced to 0.7

## Future Enhancements

### Potential Improvements
1. **Regenerate on Update**: Automatically regenerate if finding severity changes
2. **Bulk Enrichment**: API endpoint to enrich multiple findings
3. **Feedback Loop**: Allow analysts to rate enrichment quality
4. **Custom Prompts**: Allow customization of analysis focus areas
5. **Export**: Include enrichment in PDF reports
6. **Comparison**: Show how enrichment changed over time

### Monitoring
- Track generation times
- Monitor cache hit rates
- Measure user engagement with enrichment sections
- Collect feedback on usefulness

## Troubleshooting

### Enrichment Not Generating
1. Check Claude API key is configured
2. Verify database connection
3. Check backend logs for errors
4. Ensure finding has sufficient context data

### Slow Generation
- Normal for first time (3-8 seconds)
- Check Claude API rate limits
- Verify network connectivity
- Consider using higher token limits

### Incomplete Enrichment
- Some sections may be empty if AI determines not applicable
- Check finding has sufficient source data
- Try force regeneration

## Technical Notes

### Database Model Changes
```python
# database/models.py - Finding model
ai_enrichment: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
```

### API Implementation
- Location: `backend/api/findings.py`
- Function: `get_or_generate_enrichment()`
- Uses asyncio executor for Claude API calls
- Comprehensive error handling and fallbacks

### Frontend Implementation
- Component: `frontend/src/components/findings/FindingDetailDialog.tsx`
- Material-UI components for rich display
- Automatic loading on dialog open
- Responsive design with accordions

## Security Considerations

- Enrichment stored in database (no PII sent to Claude by default)
- API calls only made when necessary
- Enrichment includes confidence scores
- All data subject to database security controls

## Compliance

- AI-generated content clearly labeled
- Human review still required for actions
- Confidence scores provided for transparency
- Audit trail in database (generated_at timestamps)

---

**Version**: 1.0  
**Date**: January 14, 2026  
**Author**: DeepTempo AI SOC Team

