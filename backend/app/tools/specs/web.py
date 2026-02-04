"""Web Application Tools Specifications.

Web scanning, directory bruteforce, technology profiling.
"""
from typing import List
from app.tools.specs import ToolSpec, ToolCategory, CommandTemplate


def get_specs() -> List[ToolSpec]:
    """Get web application tool specifications."""
    return [
        # ─────────────────────────────────────────────────────────
        # GOBUSTER - Directory Bruteforce
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="gobuster",
            category=ToolCategory.WEB,
            description="Directory/file/VHost bruteforcer",
            executable_names=["gobuster"],
            install_hint="go install github.com/OJ/gobuster/v3@latest",
            aliases=["directory_bruteforce", "vhost_discovery"],
            rag_description="A tool used to discover hidden directories and files on web servers, as well as virtual hosts on a target machine, by using brute-force with wordlists.",
            when_to_use=[
                "discovering hidden web folders and files",
                "finding virtual hosts on a target IP",
                "brute-forcing S3 buckets or DNS subdomains"
            ],
            commands={
                "dir": CommandTemplate(
                    args=["dir", "-u", "{url}", "-w", "/usr/share/wordlists/dirb/common.txt", "-q"],
                    timeout=600,
                    description="Standard directory bruteforce"
                ),
                "vhost": CommandTemplate(
                    args=["vhost", "-u", "{url}", "-w", "/usr/share/wordlists/dirb/common.txt", "-q"],
                    timeout=600,
                    description="Virtual host discovery"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # FFUF - Fast Fuzzer
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="ffuf",
            category=ToolCategory.WEB,
            description="Fast web fuzzer",
            executable_names=["ffuf"],
            install_hint="go install github.com/ffuf/ffuf/v2@latest",
            aliases=["fuzzer", "web_fuzzer"],
            rag_description="A high-performance web fuzzer written in Go. It allows for fast discovery of directories, files, parameters, and other web assets through wordlist-based fuzzing.",
            when_to_use=[
                "fuzzing URL parameters for vulnerabilities",
                "high-speed directory discovery",
                "brute-forcing HTTP headers or API endpoints"
            ],
            commands={
                "dir": CommandTemplate(
                    args=["-u", "{url}/FUZZ", "-w", "/usr/share/wordlists/dirb/common.txt", "-s"],
                    timeout=600,
                    description="Directory fuzzing"
                ),
                "param": CommandTemplate(
                    args=["-u", "{url}?FUZZ=test", "-w", "/usr/share/wordlists/dirb/common.txt", "-s"],
                    timeout=300,
                    description="Parameter fuzzing"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # NIKTO - Web Server Scanner
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="nikto",
            category=ToolCategory.WEB,
            description="Web server vulnerability scanner",
            executable_names=["nikto"],
            install_hint="apt install nikto",
            rag_description="A classic web server scanner which performs comprehensive tests against web servers for multiple items, including over 6700 potentially dangerous files/programs and outdated versions of servers.",
            when_to_use=[
                "comprehensive web server configuration scanning",
                "finding dangerous files on a server",
                "identifying outdated web server software and misconfigurations"
            ],
            commands={
                "scan": CommandTemplate(
                    args=["-h", "{url}", "-C", "all"],
                    timeout=600,
                    description="Full web server vulnerability scan"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # WPSCAN - WordPress Scanner
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="wpscan",
            category=ToolCategory.WEB,
            description="WordPress security scanner",
            executable_names=["wpscan"],
            install_hint="gem install wpscan",
            aliases=["wordpress_scan"],
            rag_description="A black box WordPress security scanner that can check if a WordPress installation is vulnerable to known attacks, enumerate plugins, and find users.",
            when_to_use=[
                "scanning WordPress-based websites",
                "enumerating vulnerable WordPress plugins/themes",
                "identifying WordPress users for brute-force preparation"
            ],
            commands={
                "enum": CommandTemplate(
                    args=["--url", "{url}", "--enumerate", "vp,vt,u", "--batch"],
                    timeout=600,
                    description="Enumerate vulnerable plugins, themes, and users"
                ),
            }
        ),
        
        # ─────────────────────────────────────────────────────────
        # CURL - HTTP Header Analysis (Simple)
        # ─────────────────────────────────────────────────────────
        ToolSpec(
            name="curl",
            category=ToolCategory.WEB,
            description="Command line tool for transferring data with URLs",
            executable_names=["curl"],
            install_hint="apt install curl",
            aliases=["http_header_analysis", "header_check", "request_tool"],
            rag_description="A versatile command-line tool for making web requests. In security context, it is often used for manual inspection of HTTP headers, cookies, and responses.",
            when_to_use=[
                "inspecting HTTP response headers",
                "manually verifying web server responses",
                "testing HTTP methods (GET, POST, PUT, DELETE)"
            ],
            commands={
                "headers": CommandTemplate(
                    args=["-I", "-L", "-s", "{url}"],
                    timeout=30,
                    description="Analyze HTTP response headers"
                ),
            }
        ),
    ]
