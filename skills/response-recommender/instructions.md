# Response Recommender - Detailed Instructions

## Response Philosophy

### Defense in Depth

Response actions should follow defense in depth:

1. **Detect**: Identify the threat (already done via finding)
2. **Contain**: Limit the threat's ability to spread
3. **Eradicate**: Remove the threat from the environment
4. **Recover**: Restore normal operations
5. **Learn**: Improve defenses based on incident

### Proportional Response

Match response intensity to threat severity:

| Severity | Response Intensity |
|----------|-------------------|
| Critical | Immediate, aggressive containment |
| High | Rapid containment, parallel investigation |
| Medium | Measured response, thorough investigation |
| Low | Monitoring, scheduled investigation |

## Containment Strategies

### Network Containment

**Full Isolation**
- Disconnect from all networks
- Use for: Active compromise, ransomware
- Risk: Complete business disruption

**Segment Isolation**
- Move to quarantine VLAN
- Use for: Suspected compromise, investigation
- Risk: Partial disruption, may alert attacker

**Traffic Filtering**
- Block specific IPs/ports
- Use for: C2 blocking, exfil prevention
- Risk: May miss alternate channels

### Host Containment

**Process Termination**
- Kill malicious processes
- Use for: Active malware, crypto miners
- Risk: May trigger persistence mechanisms

**Account Suspension**
- Disable compromised accounts
- Use for: Credential theft, insider threat
- Risk: User disruption, may need exceptions

**Service Disabling**
- Stop vulnerable services
- Use for: Exploitation prevention
- Risk: Application availability

## Investigation Priorities

### Evidence Collection Order

1. **Volatile data first**
   - Memory dumps
   - Network connections
   - Running processes

2. **Logs second**
   - Security logs
   - Application logs
   - Network logs

3. **Persistent data third**
   - File system artifacts
   - Registry (Windows)
   - Configuration files

### Scope Determination

Questions to answer:
- How many systems affected?
- How long has this been happening?
- What data was accessed?
- Are there other indicators?

## Communication Templates

### Initial Notification

```
Subject: Security Incident - [Severity] - [Brief Description]

Summary:
A [severity] security incident has been detected involving [brief description].

Current Status:
- Detection Time: [time]
- Affected Systems: [count/list]
- Current Actions: [what's being done]

Next Steps:
- [Planned action 1]
- [Planned action 2]

Updates will be provided every [frequency].

Contact: [responder info]
```

### Escalation Request

```
Subject: ESCALATION REQUIRED - [Incident ID]

Escalation Reason:
[Why escalation is needed]

Current Situation:
- Incident: [description]
- Severity: [level]
- Duration: [time since detection]

Actions Taken:
- [Action 1]
- [Action 2]

Decision Required:
[What decision is needed from escalation target]

Deadline: [when decision is needed]
```

## Action Templates

### Block IP/Domain

```markdown
#### Block External IP

**Action**: Add firewall block rule
**Target**: 203.0.113.50
**Direction**: Outbound
**Protocol**: All

**Implementation**:
1. Log into firewall management console
2. Navigate to block rules
3. Add rule: Block outbound to 203.0.113.50
4. Apply and verify

**Verification**:
- Confirm rule is active
- Test connectivity is blocked
- Monitor for bypass attempts

**Rollback**:
1. Remove block rule
2. Document reason for removal
```

### Isolate Host

```markdown
#### Network Isolation

**Action**: Move host to quarantine VLAN
**Target**: workstation-042 (10.0.1.15)
**Method**: Switch port reassignment

**Implementation**:
1. Identify switch port for host
2. Reassign port to VLAN 999 (quarantine)
3. Verify isolation

**Verification**:
- Ping test fails from production
- Host can reach forensic server only
- No new outbound connections

**Rollback**:
1. Reassign port to original VLAN
2. Verify connectivity restored
3. Document reason
```

### Disable Account

```markdown
#### Account Suspension

**Action**: Disable Active Directory account
**Target**: jsmith
**Reason**: Credentials potentially compromised

**Implementation**:
1. Open Active Directory Users and Computers
2. Locate user: jsmith
3. Right-click > Disable Account
4. Document in ticket

**Verification**:
- User cannot authenticate
- Active sessions terminated
- No new logins possible

**Rollback**:
1. Re-enable account
2. Force password reset
3. Monitor for suspicious activity
```

## Risk Assessment Matrix

| Action Type | Business Impact | Reversibility | Typical Approval |
|-------------|-----------------|---------------|------------------|
| Block external IP | Low | Easy | SOC Lead |
| Isolate workstation | Medium | Easy | SOC Manager |
| Disable user account | Medium | Easy | SOC Manager + HR |
| Isolate server | High | Medium | IT Director |
| Network segment isolation | Very High | Hard | CISO |

## Post-Incident Checklist

After immediate response:

- [ ] All affected systems identified
- [ ] Threat fully contained
- [ ] Evidence preserved
- [ ] Stakeholders notified
- [ ] Timeline documented
- [ ] Root cause identified
- [ ] Remediation plan created
- [ ] Lessons learned captured
- [ ] Detection rules updated
- [ ] Playbooks revised
