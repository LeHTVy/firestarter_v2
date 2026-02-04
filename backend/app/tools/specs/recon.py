"""Reconnaissance Tools Specifications.

Subdomain enumeration, OSINT, DNS lookup.
"""
from typing import List
from app.tools.specs import ToolSpec, ToolCategory, CommandTemplate


def get_specs() -> List[ToolSpec]:
    """Get reconnaissance tool specifications."""
    return [
        # ─────────────────────────────────────────────────────────
        # SUBFINDER - Subdomain Enumeration
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="subfinder",
            category=ToolCategory.RECON,
            description="Fast subdomain discovery tool",
            executable_names=["subfinder"],
            install_hint="go install github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest",
            aliases=["finder", "subdomain_discovery", "subdomain_enum", "subdomains"],
            rag_description="High-speed subdomain discovery tool that utilizes multiple APIs and passive sources to find sub-domains of a target domain.",
            when_to_use=[
                "initial reconnaissance of a domain",
                "finding hidden assets of an organization",
                "mapping the external attack surface"
            ],
            commands={
                "enum": CommandTemplate(
                    args=["-d", "{domain}", "-silent"],
                    timeout=120,
                    description="Basic subdomain enumeration"
                ),
                "enum_all": CommandTemplate(
                    args=["-d", "{domain}", "-all", "-silent"],
                    timeout=300,
                    description="All sources enumeration"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # AMASS - Advanced Subdomain Enumeration
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="amass",
            category=ToolCategory.RECON,
            description="In-depth subdomain enumeration",
            executable_names=["amass"],
            install_hint="go install github.com/owasp-amass/amass/v4/...@master",
            aliases=["mass", "subdomain_bruteforce"],
            rag_description="Advanced OSINT tool for in-depth subdomain discovery, DNS enumeration, and network mapping using cumulative information gathering techniques.",
            when_to_use=[
                "deep recon beyond passive discovery",
                "brute-forcing subdomains",
                "active DNS enumeration"
            ],
            commands={
                "passive": CommandTemplate(
                    args=["enum", "-passive", "-d", "{domain}"],
                    timeout=1200,
                    description="Passive subdomain enumeration"
                ),
                "active": CommandTemplate(
                    args=["enum", "-d", "{domain}"],
                    timeout=1800,
                    description="Active subdomain enumeration"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # WHOIS - Domain Registration Lookup
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="whois",
            category=ToolCategory.OSINT,
            description="Domain/IP registration lookup",
            executable_names=["whois"],
            install_hint="apt install whois",
            aliases=["whois_lookup", "domain_whois", "domain_info"],
            rag_description="Standard WHOIS client to query registration information for domain names and IP address blocks.",
            when_to_use=[
                "gathering domain owner contact info",
                "identifying registration/expiration dates",
                "verifying target IP ownership"
            ],
            commands={
                "lookup": CommandTemplate(
                    args=["{target}"],
                    timeout=30,
                    success_codes=[0, 1],
                    description="WHOIS lookup"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # DIG - DNS Lookup
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="dig",
            category=ToolCategory.RECON,
            description="DNS query tool",
            executable_names=["dig"],
            install_hint="apt install dnsutils",
            aliases=["dns_enum", "dns_lookup", "dns_query", "dns_recon"],
            rag_description="Powerful command-line tool for querying Domain Name System (DNS) name servers to troubleshoot or gather info on records.",
            when_to_use=[
                "querying specific DNS records (A, MX, TXT, NS)",
                "checking DNS zone transfers",
                "verifying DNS configuration"
            ],
            commands={
                "any": CommandTemplate(args=["@8.8.8.8", "+short", "ANY", "{domain}"], timeout=30, description="Query ANY records"),
                "mx": CommandTemplate(args=["@8.8.8.8", "+short", "MX", "{domain}"], timeout=30, description="Query MX records"),
                "ns": CommandTemplate(args=["@8.8.8.8", "+short", "NS", "{domain}"], timeout=30, description="Query NS records"),
                "txt": CommandTemplate(args=["@8.8.8.8", "+short", "TXT", "{domain}"], timeout=30, description="Query TXT records"),
                "a": CommandTemplate(args=["@8.8.8.8", "+short", "A", "{domain}"], timeout=30, description="Query A records"),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # HTTPX - HTTP Probing
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="httpx",
            category=ToolCategory.RECON,
            description="Fast HTTP toolkit",
            executable_names=["httpx"],
            install_hint="go install github.com/projectdiscovery/httpx/cmd/httpx@latest",
            aliases=["probe", "web_probe", "httpx_scan"],
            rag_description="Fast HTTP toolkit that allows running multiple probes. It is used to verify subdomains, check status codes, detect technologies, and gather screenshots.",
            when_to_use=[
                "probing a list of subdomains for live web services",
                "checking HTTP status codes",
                "identifying web server technologies and titles"
            ],
            commands={
                "probe": CommandTemplate(
                    args=["-u", "{url}", "-sc", "-title", "-silent"],
                    timeout=120,
                    description="HTTP probe with status and title"
                ),
                "full": CommandTemplate(
                    args=["-u", "{url}", "-sc", "-title", "-td", "-ip", "-vhost", "-silent"],
                    timeout=300,
                    description="Comprehensive HTTP probe with tech detection and IP"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # KATANA - Web Crawler
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="katana",
            category=ToolCategory.RECON,
            description="Fast web crawler for endpoint discovery",
            executable_names=["katana"],
            install_hint="go install github.com/projectdiscovery/katana/cmd/katana@latest",
            aliases=["crawler", "spider", "web_spider"],
            rag_description="Next-generation web crawler that provides high-performance endpoint and asset discovery, supporting both headless and standard crawling.",
            when_to_use=[
                "crawling a website to find hidden endpoints",
                "discovering parameters and files",
                "mapping the structure of a web application"
            ],
            commands={
                "crawl": CommandTemplate(
                    args=["-u", "{url}", "-d", "3", "-silent"],
                    timeout=300,
                    description="Standard web crawl (depth 3)"
                ),
                "js": CommandTemplate(
                    args=["-u", "{url}", "-jc", "-d", "2", "-silent"],
                    timeout=300,
                    description="Crawling with JavaScript discovery"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # THEHARVESTER - OSINT Email/Subdomain Harvesting
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="theHarvester",
            category=ToolCategory.OSINT,
            description="OSINT tool for email and subdomain harvesting",
            executable_names=["theHarvester", "theharvester"], 
            install_hint="apt install theharvester",
            aliases=["harvester", "email_harvester", "email_harvesting"],
            rag_description="Gather emails, subdomains, hosts, employee names, open ports and banners from different public sources like search engines, PGP key servers and SHODAN database.",
            when_to_use=[
                "initial OSINT on a company",
                "harvesting corporate email addresses",
                "finding hostnames and virtual hosts"
            ],
            commands={
                "enum": CommandTemplate(
                    args=["-d", "{domain}", "-b", "all"],
                    timeout=300,
                    description="Harvest information from all sources"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # BBOT - OSINT Automation Framework
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="bbot",
            category=ToolCategory.OSINT,
            description="OSINT automation framework",
            executable_names=["bbot"],
            install_hint="pip install bbot",
            aliases=["bionic_bot", "osint_scanner"],
            rag_description="Recursive OSINT framework that can perform subdomain enumeration, port scanning, web crawling, and more in a single command, designed for scale.",
            when_to_use=[
                "comprehensive recursive reconnaissance",
                "automated attack surface mapping",
                "gathering OSINT at scale"
            ],
            commands={
                "subdomain": CommandTemplate(
                    args=["-t", "{target}", "-f", "subdomain-enum", "-y"],
                    timeout=600,
                    description="Recursive subdomain enumeration"
                ),
                "quick": CommandTemplate(
                    args=["-t", "{target}", "-m", "nmap", "httpx", "-y"],
                    timeout=300,
                    description="Quick active scan with nmap and httpx"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # WEB SEARCH - OSINT via Search Engines
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="web_search",
            category=ToolCategory.OSINT,
            description="Search the web for target information",
            executable_names=[],
            install_hint="pip install google-search-results",
            implementation="app.tools.implementations.websearch.search",
            aliases=["google_search", "online_recon", "osint_search"],
            rag_description="Utilizes search engines (via SerpAPI) to find public information, vulnerabilities, and data leaks related to the target.",
            when_to_use=[
                "finding public mentions of a target",
                "searching for specific vulnerabilities or files",
                "gathering organizational intelligence"
            ],
            commands={
                "search": CommandTemplate(
                    args=["{query}"],
                    timeout=60,
                    description="Perform web search query"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # TECHNOLOGY DETECTION - Site Fingerprinting
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="technology_detection",
            category=ToolCategory.RECON,
            description="Identify technologies used by a target web site",
            executable_names=[],
            install_hint="pip install python-Wappalyzer",
            implementation="app.tools.implementations.web_tools.technology_detection",
            aliases=["tech_detect", "fingerprint", "cms_detect"],
            rag_description="Analyzes a website to identify CMS, web servers, JavaScript libraries, and other technologies used by the application.",
            when_to_use=[
                "identifying the tech stack of a target",
                "finding versioned technologies for exploit matching",
                "fingerprinting web applications"
            ],
            commands={
                "detect": CommandTemplate(
                    args=[],
                    timeout=60,
                    description="Detect technologies on target URL"
                ),
            }
        ),
    ]
