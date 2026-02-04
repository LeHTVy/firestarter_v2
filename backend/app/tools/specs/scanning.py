"""Scanning Tools Specifications.

Port scanning, service detection, network mapping.
"""
from typing import List
from app.tools.specs import ToolSpec, ToolCategory, CommandTemplate


def get_specs() -> List[ToolSpec]:
    """Get scanning tool specifications."""
    return [
        # ─────────────────────────────────────────────────────────
        # NMAP - Port Scanner
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="nmap_scan",
            category=ToolCategory.SCANNING,
            description="Network exploration and port scanner",
            executable_names=["nmap"],
            install_hint="apt install nmap",
            aliases=["nmap", "port_scan", "service_detection", "os_detection"],
            rag_description="The industry-standard network mapper and port scanner. It is used to discover hosts and services on a computer network by sending packets and analyzing the responses.",
            when_to_use=[
                "discovering open TCP/UDP ports",
                "identifying running services and their versions",
                "detecting the operating system of a target",
                "running security scripts for basic vulnerability checks"
            ],
            commands={
                "quick": CommandTemplate(
                    args=["-T4", "-F", "-Pn", "{target}"],
                    timeout=120,
                    description="Fast scan of common ports (skips ping)"
                ),
                "full": CommandTemplate(
                    args=["-T4", "-p-", "-Pn", "{target}"],
                    timeout=1800,
                    description="Full port scan (skips ping)"
                ),
                "service": CommandTemplate(
                    args=["-sV", "-T4", "-Pn", "{target}"],
                    timeout=600,
                    description="Service version detection (skips ping)"
                ),
                "comprehensive": CommandTemplate(
                    args=["-sV", "-Pn", "-O", "-T4", "{target}"],
                    timeout=900,
                    requires_sudo=True,
                    description="Service detection, skips ping, and OS detection"
                ),
                "vuln": CommandTemplate(
                    args=["--script", "vuln", "-T4", "-Pn", "{target}"],
                    timeout=600,
                    description="Vulnerability scan via Nmap scripts"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # MASSCAN - IP Port Scanner
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="masscan",
            category=ToolCategory.SCANNING,
            description="Mass IP port scanner",
            executable_names=["masscan"],
            install_hint="apt install masscan",
            rag_description="An extremely fast IP port scanner. It can scan the entire Internet in under 6 minutes, transmitting 10 million packets per second. Used for large networks.",
            when_to_use=[
                "scanning large ranges of IP addresses (subnets)",
                "extremely high-speed port discovery",
                "finding specific open ports across a massive target list"
            ],
            commands={
                "top1000": CommandTemplate(
                    args=["--top-ports", "1000", "--rate=1000", "{target}"],
                    timeout=300,
                    requires_sudo=True,
                    description="Scan top 1000 ports"
                ),
                "all": CommandTemplate(
                    args=["-p1-65535", "--rate=10000", "{target}"],
                    timeout=600,
                    requires_sudo=True,
                    description="Full port scan at high speed"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # NAABU - High-speed Port Scanner
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="naabu",
            category=ToolCategory.SCANNING,
            description="Fast port discovery tool written in Go",
            executable_names=["naabu"],
            install_hint="go install github.com/projectdiscovery/naabu/v2/cmd/naabu@latest",
            aliases=["naabu_scan", "fast_port_scan"],
            rag_description="A target-focused fast port discovery tool written in Go. It performs fast SYN scans on large numbers of hosts with high reliability.",
            when_to_use=[
                "rapid port discovery on multiple hosts",
                "integrating with other ProjectDiscovery tools like httpx",
                "finding open ports with a simple, modern interface"
            ],
            commands={
                "scan": CommandTemplate(
                    args=["-host", "{target}", "-p", "-", "-silent"],
                    timeout=600,
                    description="Full port scan"
                ),
                "top": CommandTemplate(
                    args=["-host", "{target}", "-top-ports", "100", "-silent"],
                    timeout=120,
                    description="Top 100 ports scan"
                ),
            }
        ),

        # ─────────────────────────────────────────────────────────
        # SSLSCAN - SSL/TLS Scanner
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="sslscan",
            category=ToolCategory.SCANNING,
            description="SSL/TLS vulnerability scanner",
            executable_names=["sslscan"],
            install_hint="apt install sslscan",
            aliases=["ssl_cert_scan", "tls_scan"],
            rag_description="Tests SSL/TLS enabled services to discover supported cipher suites and certificate information. It helps identify misconfigured or vulnerable SSL/TLS setups.",
            when_to_use=[
                "checking SSL/TLS certificate validity",
                "identifying weak or insecure cipher suites",
                "verifying heartbleed, POODLE, or other SSL vulns"
            ],
            commands={
                "scan": CommandTemplate(
                    args=["{target}"],
                    timeout=300,
                    description="Comprehensive SSL/TLS scan"
                ),
            }
        ),

        # ─────────────────────────────────────────────────────────
        # SNOWCRAFT - Simple Banner Grabbing
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="banner_grabbing",
            category=ToolCategory.SCANNING,
            description="Service banner grabbing",
            executable_names=[],
            install_hint="Built-in using socket",
            implementation="app.tools.implementations.scanning_tools.banner_grabbing",
            rag_description="Connects to open ports to retrieve the service banners (introduction text) sent by the server, which often contains name and version info.",
            when_to_use=[
                "manually verifying service types",
                "gathering version information from exposed services",
                "low-interaction service identification"
            ],
            commands={
                "grab": CommandTemplate(
                    args=["{target}", "{port}"],
                    timeout=30,
                    description="Grab banner from a specific port"
                ),
            }
        ),
    ]
