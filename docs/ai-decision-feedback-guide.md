# AI Decision Feedback System

## Overview

The **AI Decision Feedback System** enables continuous improvement of AI agents through structured human oversight and feedback. This system implements **Pillar 2 (Process Framework)** and **Pillar 3 (Human Element)** from the AI-Ready SOC framework.

## Features

✅ **Track All AI Decisions** - Log every decision made by AI agents  
✅ **Collect Human Feedback** - SOC analysts grade and provide feedback  
✅ **Measure AI Accuracy** - Calculate agreement rates and accuracy scores  
✅ **Monitor Performance** - Track time saved and effectiveness metrics  
✅ **Pending Feedback Queue** - Prioritize low-confidence decisions for review  
✅ **Analytics Dashboard** - Visualize AI performance over time

## Getting Started

### 1. Run Database Migration

The AI decision logs table needs to be created in your PostgreSQL database:

```bash
# Start the database if not already running
./start_database.sh

# Run the migration
psql -U postgres -d deeptempo_soc -f database/init/003_ai_decision_logs.sql

# Or if using Docker-based Postgres:
docker exec -i $(docker ps -qf "name=postgres") psql -U postgres -d deeptempo_soc < database/init/003_ai_decision_logs.sql
```

### 2. Access the UI

Start the web application and navigate to the **AI Decisions** page:

```bash
# Start web application (if not already running)
./start_web.sh

# Access the UI
open http://localhost:6988/ai-decisions
```

### 3. Provide Feedback

The AI Decisions page has three tabs:

1. **Pending Feedback** - Decisions awaiting review (prioritized by confidence)
2. **All Decisions** - Complete history with filters
3. **Analytics** - Performance metrics and trends

To provide feedback:
1. Click "Provide Feedback" on any decision
2. Fill out the feedback form:
   - Your name/ID
   - Agreement level (Agree, Partial, Disagree)
   - Grade accuracy, reasoning, and action appropriateness (1-5 stars)
   - Specify actual outcome (True Positive, False Positive, etc.)
   - Estimate time saved by AI
   - Add optional comments
3. Submit

## For Developers: Logging AI Decisions

### Backend (Python)

When your AI agent makes a decision, log it using the `DatabaseService`:

```python
from database.service import DatabaseService
import uuid
from datetime import datetime

db_service = DatabaseService()

# Log an AI decision
decision = db_service.create_ai_decision(
    decision_id=f"dec-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
    agent_id="triage",  # Your agent's ID
    decision_type="escalate",
    confidence_score=0.82,
    reasoning="High anomaly score (0.89) combined with critical MITRE technique T1486 (Ransomware) detected.",
    recommended_action="Escalate to Investigation Agent for deep analysis. Consider immediate containment.",
    finding_id="f-20260115-abc123",  # Optional
    case_id=None,  # Optional
    workflow_id="triage-standard",  # Optional
    decision_metadata={
        "anomaly_score": 0.89,
        "mitre_techniques": ["T1486", "T1021.002"],
        "affected_hosts": 3
    }
)

print(f"Logged decision: {decision.decision_id}")
```

### Frontend (TypeScript/React)

Log decisions from the frontend:

```typescript
import { aiDecisionsApi } from '../services/api'

const logDecision = async () => {
  try {
    const response = await aiDecisionsApi.create({
      decision_id: `dec-${Date.now()}-${Math.random().toString(36).substr(2, 8)}`,
      agent_id: 'triage',
      decision_type: 'escalate',
      confidence_score: 0.82,
      reasoning: 'High anomaly score detected with ransomware indicators',
      recommended_action: 'Escalate for investigation',
      finding_id: 'f-20260115-abc123',
    })
    console.log('Decision logged:', response.data)
  } catch (error) {
    console.error('Failed to log decision:', error)
  }
}
```

### Example: Integrating with Triage Agent

Here's how to integrate decision logging into an existing agent:

```python
# In services/soc_agents.py or your agent code

from database.service import DatabaseService
import uuid
from datetime import datetime

def triage_finding(finding_id: str):
    """Triage a finding and log the AI decision."""
    
    # Get finding details
    db_service = DatabaseService()
    finding = db_service.get_finding(finding_id)
    
    # AI makes a decision
    anomaly_score = finding.anomaly_score
    severity = finding.severity
    
    if anomaly_score >= 0.8 and severity == 'critical':
        decision_type = "escalate"
        recommended_action = "Escalate to Investigation Agent for deep analysis"
        confidence = 0.85
        reasoning = f"Critical severity with high anomaly score ({anomaly_score:.2f})"
    else:
        decision_type = "monitor"
        recommended_action = "Monitor for additional suspicious activity"
        confidence = 0.60
        reasoning = f"Medium priority - anomaly score {anomaly_score:.2f}"
    
    # Log the decision
    decision_id = f"dec-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    
    db_service.create_ai_decision(
        decision_id=decision_id,
        agent_id="triage",
        decision_type=decision_type,
        confidence_score=confidence,
        reasoning=reasoning,
        recommended_action=recommended_action,
        finding_id=finding_id,
        decision_metadata={
            "anomaly_score": anomaly_score,
            "severity": severity,
            "mitre_techniques": list(finding.mitre_predictions.keys())[:3]
        }
    )
    
    return {
        "decision_id": decision_id,
        "decision_type": decision_type,
        "confidence": confidence,
        "action": recommended_action
    }
```

## API Reference

### Create AI Decision

```http
POST /api/ai/decisions
Content-Type: application/json

{
  "decision_id": "dec-20260115-abc123",
  "agent_id": "triage",
  "decision_type": "escalate",
  "confidence_score": 0.82,
  "reasoning": "High anomaly score with ransomware indicators",
  "recommended_action": "Escalate for investigation",
  "finding_id": "f-20260115-xyz789",
  "case_id": null,
  "workflow_id": "triage-standard",
  "decision_metadata": {
    "anomaly_score": 0.89,
    "mitre_techniques": ["T1486"]
  }
}
```

### Submit Feedback

```http
POST /api/ai/decisions/{decision_id}/feedback
Content-Type: application/json

{
  "human_reviewer": "analyst_jones",
  "human_decision": "agree",
  "feedback_comment": "Correct assessment, good reasoning",
  "accuracy_grade": 0.8,
  "reasoning_grade": 0.9,
  "action_appropriateness": 0.85,
  "actual_outcome": "true_positive",
  "time_saved_minutes": 15
}
```

### List Decisions

```http
GET /api/ai/decisions?agent_id=triage&has_feedback=false&limit=50
```

### Get Statistics

```http
GET /api/ai/decisions/stats?agent_id=triage&days=30
```

Response:
```json
{
  "total_decisions": 150,
  "total_with_feedback": 120,
  "feedback_rate": 0.8,
  "agreement_rate": 0.75,
  "avg_accuracy_grade": 0.82,
  "outcomes": {
    "true_positive": 90,
    "false_positive": 30
  },
  "total_time_saved_minutes": 1800,
  "total_time_saved_hours": 30.0,
  "period_days": 30
}
```

## Metrics & KPIs

The system tracks several key metrics:

### AI Performance Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Feedback Rate** | % of decisions with human feedback | >80% |
| **Agreement Rate** | % of decisions humans agree with | >70% |
| **Avg Accuracy Grade** | Average human accuracy rating | >0.75 |
| **Time Saved** | Hours saved by AI automation | Increasing |

### Outcome Distribution

- **True Positive**: AI correctly identified a threat
- **False Positive**: AI incorrectly flagged benign activity
- **True Negative**: AI correctly dismissed non-threat
- **False Negative**: AI missed a real threat

## Best Practices

### For SOC Analysts

1. **Review Low-Confidence Decisions First**  
   The system prioritizes decisions with confidence <0.70 - these benefit most from feedback

2. **Be Specific in Comments**  
   Provide actionable feedback: "Missed checking for lateral movement indicators"

3. **Grade Honestly**  
   Accurate grading helps the AI improve. Don't artificially inflate scores

4. **Track Time Saved**  
   Estimate time realistically - this demonstrates ROI to leadership

5. **Review Regularly**  
   Aim to provide feedback on at least 10 decisions per day

### For SOC Managers

1. **Monitor Error Budgets**  
   Review weekly stats to ensure AI stays within acceptable error rates

2. **Analyze Trends**  
   Look for patterns in disagreements to identify improvement areas

3. **Celebrate Wins**  
   Share time saved metrics with the team and leadership

4. **Adjust Thresholds**  
   If agreement rate drops below 70%, consider adjusting confidence thresholds

## Troubleshooting

### No Decisions Showing Up

**Problem**: The AI Decisions page is empty

**Solutions**:
1. Check that the database migration ran successfully
2. Verify agents are logging decisions (check application logs)
3. Ensure PostgreSQL is running and connected

```bash
# Check if table exists
psql -U postgres -d deeptempo_soc -c "SELECT COUNT(*) FROM ai_decision_logs;"

# Check application logs
tail -f ~/.deeptempo/api.log | grep "decision"
```

### API Errors

**Problem**: "Failed to submit feedback" or API 500 errors

**Solutions**:
1. Check backend logs for detailed error messages
2. Verify all required fields are provided
3. Ensure decision_id exists before submitting feedback

```bash
# Check backend logs
tail -f ~/.deeptempo/api.log
```

### Feedback Form Not Submitting

**Problem**: Feedback dialog doesn't close after submit

**Solutions**:
1. Check browser console for errors (F12)
2. Verify you've entered your reviewer name
3. Ensure backend is running and accessible

## Integration with Autonomous Response

The AI Decision Feedback system integrates with the Auto-Response Agent:

```python
# In mcp_servers/crowdstrike_server/server.py

from database.service import DatabaseService

async def isolate_host_with_logging(ip_address: str, reason: str, confidence: float):
    """Isolate host and log the AI decision."""
    
    db_service = DatabaseService()
    
    # Create decision log BEFORE taking action
    decision_id = f"dec-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}"
    
    db_service.create_ai_decision(
        decision_id=decision_id,
        agent_id="auto_responder",
        decision_type="isolate_host",
        confidence_score=confidence,
        reasoning=reason,
        recommended_action=f"Network isolate {ip_address}",
        decision_metadata={
            "ip_address": ip_address,
            "action_type": "isolation"
        }
    )
    
    # Take the action
    result = await isolate_host(ip_address)
    
    # If action failed, update decision log
    if not result["success"]:
        db_service.submit_ai_decision_feedback(
            decision_id=decision_id,
            human_reviewer="system",
            human_decision="disagree",
            actual_outcome="action_failed",
            feedback_comment=f"Action failed: {result['error']}"
        )
    
    return result
```

## Roadmap

Future enhancements planned:

- [ ] **AI Learning Loop**: Use feedback to fine-tune agent prompts
- [ ] **Agent Comparison**: Compare accuracy across different agents
- [ ] **Automated Reports**: Weekly AI performance reports via email/Slack
- [ ] **Feedback Predictions**: Predict which decisions need review
- [ ] **A/B Testing**: Test different agent prompts and measure improvement

## Contributing

To add decision logging to a new agent:

1. Import `DatabaseService` and `uuid`
2. Generate unique `decision_id`
3. Call `create_ai_decision()` after agent makes decision
4. Include relevant metadata for future analysis

See examples above for implementation patterns.

## Related Documentation

- [AI-Ready SOC Improvements Guide](./ai-readiness-improvements.md) - Complete framework
- [Autonomous Response Guide](./autonomous-response-guide.md) - Auto-response agent
- [SOC Agents Guide](./soc-agents-guide.md) - Agent system overview

## Support

For issues or questions:
1. Check application logs: `~/.deeptempo/api.log`
2. Review database logs: `docker logs <postgres-container>`
3. Open an issue on GitHub with relevant error messages

---

**Remember**: The goal is continuous improvement, not perfection. Every piece of feedback helps the AI learn and get better! 🎯

