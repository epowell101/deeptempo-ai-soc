# Force Manual Approval Feature

## Overview

The **Force Manual Approval** feature allows you to override the confidence-based auto-approval system and require manual approval for ALL actions, regardless of their confidence score.

## Use Cases

### When to Enable Force Manual Approval

1. **Training/Testing Environment**
   - Learning how the system works
   - Testing new agents or workflows
   - Demonstrating to stakeholders

2. **High-Security Periods**
   - During security incidents
   - When under active attack
   - During compliance audits

3. **New Deployment**
   - First few weeks of deployment
   - Building confidence in the system
   - Establishing baseline behavior

4. **Regulatory Requirements**
   - Compliance mandates human oversight
   - Industry-specific regulations
   - Internal security policies

### When to Disable (Normal Operation)

1. **Mature Deployment**
   - System has proven reliable
   - Confidence scoring is well-tuned
   - Team trusts the automation

2. **High-Volume Operations**
   - Need fast response times
   - High-confidence threats are common
   - Manual review would be bottleneck

3. **Off-Hours Coverage**
   - Limited analyst availability
   - Auto-response needed for critical threats
   - Escalation procedures in place

## How It Works

### Normal Behavior (Force Manual Approval OFF)

| Confidence | Behavior |
|------------|----------|
| ≥ 0.90 | ✅ Auto-approved & executed |
| 0.85-0.89 | ✅ Auto-approved with review flag |
| 0.70-0.84 | ⏸️ Requires manual approval |
| < 0.70 | 👁️ Monitor only |

### With Force Manual Approval ON

| Confidence | Behavior |
|------------|----------|
| ≥ 0.90 | ⏸️ **Requires manual approval** |
| 0.85-0.89 | ⏸️ **Requires manual approval** |
| 0.70-0.84 | ⏸️ Requires manual approval |
| < 0.70 | 👁️ Monitor only |

**All actions, even those with 100% confidence, will require manual approval.**

## Using the Feature

### In the UI

1. Open **Dashboard → Approval Queue** tab
2. Look for the checkbox at the top: **"Force Manual Approval for All Actions"**
3. Check the box to enable
4. Uncheck the box to disable

**Visual Indicators:**
- When enabled, the info label shows: ⚠️ **Force Manual Approval Enabled**
- The label is highlighted in orange
- A confirmation dialog appears when you toggle the setting

### Programmatically

```python
from services.approval_service import get_approval_service

approval_service = get_approval_service()

# Enable force manual approval
approval_service.set_force_manual_approval(True)

# Check current setting
is_forced = approval_service.get_force_manual_approval()
print(f"Force manual approval: {is_forced}")

# Disable force manual approval
approval_service.set_force_manual_approval(False)
```

## Examples

### Example 1: High-Confidence Action with Force Approval OFF

```python
# Normal operation
approval_service.set_force_manual_approval(False)

# Create action with 95% confidence
action = approval_service.create_action(
    action_type=ActionType.ISOLATE_HOST,
    target="192.168.1.100",
    confidence=0.95,
    reason="Confirmed ransomware",
    evidence=["finding-001"]
)

print(action.status)  # "approved" (auto-approved)
print(action.requires_approval)  # False
```

### Example 2: Same Action with Force Approval ON

```python
# Force manual approval enabled
approval_service.set_force_manual_approval(True)

# Create action with 95% confidence
action = approval_service.create_action(
    action_type=ActionType.ISOLATE_HOST,
    target="192.168.1.100",
    confidence=0.95,
    reason="Confirmed ransomware",
    evidence=["finding-001"]
)

print(action.status)  # "pending" (requires approval)
print(action.requires_approval)  # True
```

### Example 3: Auto-Responder Behavior

**With Force Approval OFF:**
```
Auto-Responder detects ransomware (confidence: 0.93)
→ Creates isolation action
→ Action auto-approved
→ Host isolated immediately
→ Analyst notified
```

**With Force Approval ON:**
```
Auto-Responder detects ransomware (confidence: 0.93)
→ Creates isolation action
→ Action goes to approval queue
→ Analyst must approve
→ Host isolated after approval
```

## Configuration Storage

The setting is stored in: `data/approval_config.json`

```json
{
  "force_manual_approval": false
}
```

This file is automatically created and persists across application restarts.

## Impact on Agents

### Auto-Responder Agent
- **Normal**: Auto-executes high-confidence actions (≥90%)
- **Force Approval ON**: All actions require approval, even 100% confidence

### Investigation Agent
- **Normal**: Can create actions that auto-approve if confidence ≥90%
- **Force Approval ON**: All proposed actions require approval

### Response Agent
- **Normal**: High-confidence recommendations auto-approve
- **Force Approval ON**: All recommendations require approval

### Threat Hunter
- **Normal**: High-confidence blocking actions auto-approve
- **Force Approval ON**: All blocking actions require approval

## Best Practices

### 1. Start with Force Approval ON
When first deploying:
```python
# Initial setup
approval_service.set_force_manual_approval(True)
```
- Review all actions manually
- Build confidence in the system
- Tune confidence scoring

### 2. Gradually Transition
After 1-2 weeks:
```python
# Transition to normal operation
approval_service.set_force_manual_approval(False)
```
- Monitor auto-approved actions
- Review execution results
- Adjust if needed

### 3. Toggle During Incidents
During active incidents:
```python
# Increase oversight during incident
approval_service.set_force_manual_approval(True)

# ... handle incident ...

# Return to normal after incident
approval_service.set_force_manual_approval(False)
```

### 4. Document Your Policy
Create a policy document:
- When to enable force approval
- Who can toggle the setting
- Review procedures
- Escalation paths

## Monitoring

### Check Current Setting

**In UI:**
- Look at the checkbox state in Approval Queue tab
- Check the info label color/text

**In Python:**
```python
approval_service = get_approval_service()
is_forced = approval_service.get_force_manual_approval()

if is_forced:
    print("⚠️ Force manual approval is ENABLED")
else:
    print("✅ Normal auto-approval is active")
```

### Audit Log
All setting changes are logged:
```
INFO: Force manual approval set to: True
INFO: Force manual approval set to: False
```

## Troubleshooting

### Issue: Setting Doesn't Persist

**Problem**: Force approval resets after restart

**Solution**: Check file permissions on `data/approval_config.json`
```bash
ls -la data/approval_config.json
chmod 644 data/approval_config.json
```

### Issue: Actions Still Auto-Approving

**Problem**: Actions auto-approve even with force approval ON

**Solution**: 
1. Verify setting is actually enabled:
```python
print(approval_service.get_force_manual_approval())
```
2. Restart the application
3. Check for multiple ApprovalService instances

### Issue: Can't Toggle Checkbox

**Problem**: Checkbox is disabled/grayed out

**Solution**: Ensure approval service loaded correctly:
```python
# Check in Python
from services.approval_service import get_approval_service
approval_service = get_approval_service()
print("Service loaded:", approval_service is not None)
```

## Security Considerations

### Access Control
- Only authorized analysts should toggle this setting
- Consider adding authentication/authorization
- Log all setting changes with user identity

### Compliance
- Document when and why setting is changed
- Include in audit reports
- Review setting changes during compliance audits

### Incident Response
- Have a procedure for enabling during incidents
- Document decision criteria
- Include in incident response playbooks

## Summary

**Force Manual Approval** provides an important safety override:

✅ **Enabled**: All actions require manual approval (maximum oversight)  
✅ **Disabled**: Confidence-based auto-approval (normal operation)  
✅ **Persistent**: Setting saved across restarts  
✅ **Visible**: Clear UI indicators  
✅ **Flexible**: Easy to toggle on/off  

Use this feature to balance automation efficiency with human oversight based on your organization's needs and risk tolerance.

