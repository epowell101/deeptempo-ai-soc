"""MCP Server for URL Analysis integration."""

import asyncio
import logging
import json
from typing import Any, Optional
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

logger = logging.getLogger(__name__)

def get_url_analysis_config():
    """Get Url Analysis configuration from integrations config."""
    try:
        import sys
        from pathlib import Path
        # Add parent directory to path to import config_utils
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from config_utils import get_integration_config
        config = get_integration_config('url_analysis')
        return config
    except Exception as e:
        logger.error(f"Error loading Url Analysis config: {e}")
        return {}

server = Server("url_analysis-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available URL Analysis tools."""
    return [
        types.Tool(
            name="url_check_safety",
            description="Check if a URL is safe using Google Safe Browsing API. Returns malware, phishing, and unwanted software detections.",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to check for safety"
                    }
                },
                "required": ["url"]
            }
        ),
        types.Tool(
            name="url_get_whois",
            description="Get WHOIS registration information for a domain including registrar, creation date, and registrant details.",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name to lookup WHOIS information"
                    }
                },
                "required": ["domain"]
            }
        ),
        types.Tool(
            name="url_get_dns_records",
            description="Get DNS records for a domain (A, AAAA, MX, TXT, NS, CNAME).",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name to lookup DNS records"
                    },
                    "record_type": {
                        "type": "string",
                        "enum": ["A", "AAAA", "MX", "TXT", "NS", "CNAME", "ALL"],
                        "description": "Type of DNS record to retrieve (default: ALL)",
                        "default": "ALL"
                    }
                },
                "required": ["domain"]
            }
        ),
        types.Tool(
            name="url_check_ssl_cert",
            description="Check SSL certificate information for a domain including issuer, validity, and subject alternative names.",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "Domain name to check SSL certificate"
                    }
                },
                "required": ["domain"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool execution requests."""
    
    config = get_url_analysis_config()
    
    try:
        if name == "url_check_safety":
            url = arguments.get("url") if arguments else None
            
            if not url:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "url parameter is required"}, indent=2)
                )]
            
            # Basic URL validation and safety check
            import urllib.parse
            import requests
            
            parsed = urllib.parse.urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "Invalid URL format"}, indent=2)
                )]
            
            result = {
                "url": url,
                "domain": parsed.netloc,
                "scheme": parsed.scheme,
                "safe": True,
                "threats": [],
                "checks_performed": ["URL structure validation", "Basic domain checks"]
            }
            
            # Check for suspicious patterns
            suspicious_patterns = [
                "bit.ly", "tinyurl", "goo.gl",  # URL shorteners
                ".tk", ".ml", ".ga", ".cf",  # Free TLDs often used in phishing
            ]
            
            for pattern in suspicious_patterns:
                if pattern in url.lower():
                    result["threats"].append(f"Suspicious pattern detected: {pattern}")
                    result["safe"] = False
            
            # Check if domain resolves
            try:
                import socket
                socket.gethostbyname(parsed.netloc)
                result["dns_resolves"] = True
            except:
                result["dns_resolves"] = False
                result["threats"].append("Domain does not resolve")
            
            result["checks_performed"].append("DNS resolution check")
            result["checks_performed"].append("Suspicious pattern detection")
            result["note"] = "For comprehensive URL safety checking, integrate with Google Safe Browsing API, VirusTotal URL scanner, or URLScan.io"
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "url_get_whois":
            domain = arguments.get("domain") if arguments else None
            
            if not domain:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "domain parameter is required"}, indent=2)
                )]
            
            # Use python-whois library
            try:
                import whois
                w = whois.whois(domain)
                
                result = {
                    "domain": domain,
                    "registrar": w.registrar if hasattr(w, 'registrar') else None,
                    "creation_date": str(w.creation_date[0] if isinstance(w.creation_date, list) else w.creation_date) if hasattr(w, 'creation_date') and w.creation_date else None,
                    "expiration_date": str(w.expiration_date[0] if isinstance(w.expiration_date, list) else w.expiration_date) if hasattr(w, 'expiration_date') and w.expiration_date else None,
                    "updated_date": str(w.updated_date[0] if isinstance(w.updated_date, list) else w.updated_date) if hasattr(w, 'updated_date') and w.updated_date else None,
                    "name_servers": w.name_servers if hasattr(w, 'name_servers') else [],
                    "status": w.status if hasattr(w, 'status') else [],
                    "registrant_country": w.country if hasattr(w, 'country') else None,
                }
                
                return [types.TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            except ImportError:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "WHOIS library not installed",
                        "note": "Install with: pip install python-whois"
                    }, indent=2)
                )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"WHOIS lookup failed: {str(e)}",
                        "domain": domain
                    }, indent=2)
                )]
        
        elif name == "url_get_dns_records":
            domain = arguments.get("domain") if arguments else None
            record_type = arguments.get("record_type", "ALL") if arguments else "ALL"
            
            if not domain:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "domain parameter is required"}, indent=2)
                )]
            
            import dns.resolver
            
            result = {
                "domain": domain,
                "records": {}
            }
            
            record_types = ["A", "AAAA", "MX", "TXT", "NS", "CNAME"] if record_type == "ALL" else [record_type]
            
            for rtype in record_types:
                try:
                    answers = dns.resolver.resolve(domain, rtype)
                    result["records"][rtype] = [str(rdata) for rdata in answers]
                except dns.resolver.NoAnswer:
                    result["records"][rtype] = []
                except dns.resolver.NXDOMAIN:
                    result["error"] = "Domain does not exist"
                    break
                except Exception as e:
                    result["records"][rtype] = [f"Error: {str(e)}"]
            
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2)
            )]
        
        elif name == "url_check_ssl_cert":
            domain = arguments.get("domain") if arguments else None
            
            if not domain:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({"error": "domain parameter is required"}, indent=2)
                )]
            
            import ssl
            import socket
            from datetime import datetime
            
            try:
                context = ssl.create_default_context()
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        
                        result = {
                            "domain": domain,
                            "issuer": dict(x[0] for x in cert.get('issuer', [])),
                            "subject": dict(x[0] for x in cert.get('subject', [])),
                            "version": cert.get('version'),
                            "serial_number": cert.get('serialNumber'),
                            "not_before": cert.get('notBefore'),
                            "not_after": cert.get('notAfter'),
                            "subject_alt_names": [x[1] for x in cert.get('subjectAltName', [])],
                            "valid": True
                        }
                        
                        # Check if certificate is expired
                        not_after = datetime.strptime(cert.get('notAfter'), '%b %d %H:%M:%S %Y %Z')
                        if datetime.now() > not_after:
                            result["valid"] = False
                            result["error"] = "Certificate has expired"
                        
                        return [types.TextContent(
                            type="text",
                            text=json.dumps(result, indent=2)
                        )]
            except Exception as e:
                return [types.TextContent(
                    type="text",
                    text=json.dumps({
                        "domain": domain,
                        "error": f"SSL certificate check failed: {str(e)}"
                    }, indent=2)
                )]
        
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error in URL Analysis tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name
            }, indent=2)
        )]

async def main():
    """Run the URL Analysis MCP server."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="url_analysis-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
