"""
AI-Generated Explanation Generator

Generates human-readable explanations for security findings,
similar to Dropzone AI's investigation summaries.
"""

from typing import Dict, List, Optional
import json

# Templates for generating explanations based on technique and context
EXPLANATION_TEMPLATES = {
    "T1071.001": {
        "template": "This host ({hostname}) established {connection_count} connection(s) to {dest_ip} over port {dest_port}. The traffic pattern shows characteristics of command-and-control communication: {pattern_details}. This behavior is consistent with {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "irregular timing intervals designed to evade beacon detection, use of legitimate cloud infrastructure (CDN/cloud provider IPs), and encrypted payloads",
            "standard": "regular beacon intervals, known malicious infrastructure, and encoded command responses"
        }
    },
    "T1071.004": {
        "template": "DNS tunneling activity detected from {hostname}. The host made {query_count} DNS queries to subdomains of suspicious domains. Key indicators: {pattern_details}. This matches {technique_name} ({technique_id}), commonly used for covert data exfiltration or C2 communication.",
        "pattern_details": {
            "evasive": "short subdomain labels (avoiding length-based detection), A record queries only (mimicking normal lookups), queries spread over extended time periods",
            "standard": "long encoded subdomains, TXT record queries, high query frequency"
        }
    },
    "T1048.001": {
        "template": "Data exfiltration detected from {hostname} to {dest_ip}. Approximately {data_size} of data was transferred over an encrypted channel. The transfer pattern shows: {pattern_details}. This is consistent with {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "small chunk sizes (50-200KB) staying under volume thresholds, transfers spread across multiple sessions, use of legitimate cloud storage endpoints",
            "standard": "large data transfers, sustained high-bandwidth connections, known exfiltration infrastructure"
        }
    },
    "T1048.003": {
        "template": "DNS-based data exfiltration detected from {hostname}. Data is being encoded in DNS query subdomains and sent to {dest_domain}. Indicators: {pattern_details}. This matches {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "low query rate to avoid volume detection, base32/hex encoded data in short segments, queries to seemingly legitimate domains",
            "standard": "high query volume, base64 encoded payloads, queries to suspicious TLDs"
        }
    },
    "T1021.001": {
        "template": "Remote Desktop Protocol (RDP) lateral movement detected. {hostname} initiated an RDP session to {dest_ip}. Context: {pattern_details}. This behavior matches {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "connection during business hours to blend with normal activity, use of valid credentials, targeting of high-value systems",
            "standard": "off-hours connection, brute-force authentication attempts, rapid pivoting between systems"
        }
    },
    "T1021.002": {
        "template": "SMB/Windows Admin Share lateral movement detected. {hostname} accessed admin shares on {dest_ip}. Analysis shows: {pattern_details}. This is consistent with {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "use of legitimate admin tools, access patterns mimicking normal IT operations, valid domain credentials",
            "standard": "access to C$ or ADMIN$ shares, file staging for execution, credential dumping artifacts"
        }
    },
    "T1021.006": {
        "template": "Windows Remote Management (WinRM) lateral movement detected from {hostname} to {dest_ip}. This living-off-the-land technique uses built-in Windows tools. Indicators: {pattern_details}. Matches {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "use of native Windows management tools (avoiding custom malware), PowerShell remoting with valid credentials, commands executed during business hours",
            "standard": "rapid command execution across multiple hosts, encoded PowerShell payloads, persistence mechanism installation"
        }
    },
    "T1047": {
        "template": "Windows Management Instrumentation (WMI) execution detected on {hostname}. WMI was used to execute commands remotely. Details: {pattern_details}. This matches {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "use of legitimate WMI queries mixed with malicious commands, execution through trusted processes, minimal artifacts left on disk",
            "standard": "process creation via WMI, lateral movement to multiple hosts, persistence through WMI subscriptions"
        }
    },
    "T1078": {
        "template": "Valid account abuse detected. Credentials for {user} were used on {hostname} in a manner inconsistent with normal behavior. Indicators: {pattern_details}. This matches {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "login during normal hours, access to systems within user's typical scope, gradual privilege escalation",
            "standard": "off-hours authentication, access to unusual systems, rapid privilege escalation"
        }
    },
    "T1573.001": {
        "template": "Encrypted command-and-control channel detected from {hostname} to {dest_ip}. The connection uses encryption to conceal C2 traffic. Analysis: {pattern_details}. Matches {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "use of standard HTTPS on port 443, certificate mimicking legitimate services, traffic blending with normal web browsing",
            "standard": "custom encryption protocols, unusual ports, distinctive TLS fingerprints"
        }
    },
    "T1041": {
        "template": "Data exfiltration over C2 channel detected. {hostname} is sending data to {dest_ip} using the established command-and-control connection. Volume: approximately {data_size}. Pattern: {pattern_details}. Matches {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "data chunked into small segments, transfer rate throttled to avoid detection, encryption matching normal C2 traffic",
            "standard": "large data transfers, sustained outbound connections, compression artifacts in traffic"
        }
    },
    "T1133": {
        "template": "External remote service persistence detected. {hostname} has established persistent access via external remote services. Details: {pattern_details}. This matches {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "use of legitimate remote access tools, connections during business hours, minimal configuration changes",
            "standard": "installation of unauthorized remote access tools, off-hours connections, registry/startup modifications"
        }
    },
    "T1190": {
        "template": "Exploitation of public-facing application detected targeting {dest_ip}. Attack originated from {hostname}. Analysis: {pattern_details}. Matches {technique_name} ({technique_id}).",
        "pattern_details": {
            "evasive": "low-and-slow exploitation attempts, use of legitimate-looking requests, exploitation of zero-day or recently disclosed vulnerabilities",
            "standard": "rapid exploitation attempts, known exploit signatures, scanning activity preceding exploitation"
        }
    }
}

# Default template for unknown techniques
DEFAULT_TEMPLATE = {
    "template": "Suspicious activity detected on {hostname} involving {dest_ip}. The behavior pattern indicates potential {technique_name} ({technique_id}). {pattern_details}",
    "pattern_details": {
        "evasive": "The attack uses evasion techniques to avoid traditional detection methods.",
        "standard": "The activity matches known malicious patterns."
    }
}


def generate_explanation(finding: Dict) -> str:
    """
    Generate a human-readable explanation for a security finding.
    
    Args:
        finding: The finding dictionary containing event details and MITRE classification
        
    Returns:
        A detailed explanation string
    """
    # Extract key information
    technique_id = finding.get("mitre_predictions", [{}])[0].get("technique_id", "Unknown")
    technique_name = finding.get("mitre_predictions", [{}])[0].get("technique_name", "Unknown Technique")
    is_evasive = finding.get("evasive", False)
    
    # Get template
    template_data = EXPLANATION_TEMPLATES.get(technique_id, DEFAULT_TEMPLATE)
    template = template_data["template"]
    pattern_key = "evasive" if is_evasive else "standard"
    pattern_details = template_data["pattern_details"].get(pattern_key, "")
    
    # Extract event details
    raw_event = finding.get("raw_event", {})
    hostname = finding.get("hostname") or raw_event.get("hostname", "unknown host")
    dest_ip = finding.get("dest_ip") or raw_event.get("id.resp_h", "unknown destination")
    dest_port = finding.get("dest_port") or raw_event.get("id.resp_p", "unknown port")
    user = finding.get("user") or raw_event.get("user", "unknown user")
    
    # Estimate data size from bytes if available
    orig_bytes = raw_event.get("orig_bytes", 0) or 0
    resp_bytes = raw_event.get("resp_bytes", 0) or 0
    total_bytes = orig_bytes + resp_bytes
    if total_bytes > 1024 * 1024:
        data_size = f"{total_bytes / (1024*1024):.1f} MB"
    elif total_bytes > 1024:
        data_size = f"{total_bytes / 1024:.1f} KB"
    else:
        data_size = f"{total_bytes} bytes"
    
    # Get domain from DNS events if available
    dest_domain = raw_event.get("query", dest_ip)
    
    # Format the explanation
    explanation = template.format(
        hostname=hostname,
        dest_ip=dest_ip,
        dest_port=dest_port,
        dest_domain=dest_domain,
        user=user,
        data_size=data_size,
        technique_id=technique_id,
        technique_name=technique_name,
        pattern_details=pattern_details,
        connection_count=1,  # Could be enhanced to count related events
        query_count=1  # Could be enhanced to count DNS queries
    )
    
    # Add evasion context if applicable
    if is_evasive:
        evasion_technique = finding.get("evasion_technique", "unknown evasion method")
        explanation += f"\n\n**Evasion Note**: This attack uses {evasion_technique}, which is specifically designed to evade traditional signature-based detection. LogLM detected this through behavioral analysis rather than rule matching."
    
    return explanation


def generate_incident_summary(incident: Dict, findings: List[Dict]) -> str:
    """
    Generate a summary explanation for an entire incident.
    
    Args:
        incident: The incident dictionary
        findings: List of findings associated with this incident
        
    Returns:
        A comprehensive incident summary
    """
    # Group findings by attack phase
    phases = {}
    for finding in findings:
        phase = finding.get("attack_phase", 0)
        if phase not in phases:
            phases[phase] = []
        phases[phase].append(finding)
    
    # Build narrative
    summary_parts = []
    summary_parts.append(f"## Incident Summary: {incident.get('title', 'Security Incident')}\n")
    summary_parts.append(f"**Severity**: {incident.get('severity', 'Unknown').upper()}")
    summary_parts.append(f"**Findings**: {len(findings)} related events")
    summary_parts.append(f"**Time Range**: {incident.get('start_time', 'Unknown')} to {incident.get('end_time', 'Unknown')}\n")
    
    # Describe attack progression
    summary_parts.append("### Attack Progression\n")
    
    phase_names = {
        1: "Initial Compromise",
        2: "Command & Control",
        3: "Lateral Movement",
        4: "Data Access & Exfiltration",
        5: "Persistence",
        6: "Evasive C2",
        7: "Evasive Exfiltration",
        8: "Living-off-the-Land Movement"
    }
    
    for phase_num in sorted(phases.keys()):
        phase_findings = phases[phase_num]
        phase_name = phase_names.get(phase_num, f"Phase {phase_num}")
        
        summary_parts.append(f"**{phase_name}** ({len(phase_findings)} events)")
        
        # Summarize key techniques in this phase
        techniques = set()
        hosts = set()
        for f in phase_findings:
            for pred in f.get("mitre_predictions", []):
                techniques.add(f"{pred.get('technique_name')} ({pred.get('technique_id')})")
            if f.get("hostname"):
                hosts.add(f["hostname"])
        
        if techniques:
            summary_parts.append(f"  - Techniques: {', '.join(techniques)}")
        if hosts:
            summary_parts.append(f"  - Affected hosts: {', '.join(hosts)}")
        summary_parts.append("")
    
    # Add recommendations
    summary_parts.append("### Recommended Actions\n")
    summary_parts.append("1. Isolate affected hosts from the network")
    summary_parts.append("2. Preserve forensic evidence before remediation")
    summary_parts.append("3. Reset credentials for compromised accounts")
    summary_parts.append("4. Block identified C2 infrastructure at the perimeter")
    summary_parts.append("5. Hunt for similar activity across the environment using embedding similarity search")
    
    return "\n".join(summary_parts)


def add_explanations_to_findings(findings: List[Dict]) -> List[Dict]:
    """
    Add AI-generated explanations to a list of findings.
    
    Args:
        findings: List of finding dictionaries
        
    Returns:
        Updated findings with 'explanation' field added
    """
    for finding in findings:
        finding["explanation"] = generate_explanation(finding)
    return findings


if __name__ == "__main__":
    # Test with sample finding
    sample_finding = {
        "id": "finding_00001",
        "hostname": "workstation-042",
        "dest_ip": "203.0.113.50",
        "dest_port": 443,
        "mitre_predictions": [
            {
                "technique_id": "T1071.001",
                "technique_name": "Web Protocols",
                "tactic": "Command and Control",
                "confidence": 0.89
            }
        ],
        "evasive": True,
        "evasion_technique": "HTTPS C2 via CDN",
        "raw_event": {
            "orig_bytes": 1024,
            "resp_bytes": 51200
        }
    }
    
    explanation = generate_explanation(sample_finding)
    print("Generated Explanation:")
    print(explanation)
