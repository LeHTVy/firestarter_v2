"""Target parsing module for Firestarter AI."""

import re
from enum import Enum
from typing import Optional, Union, List
from pydantic import BaseModel
from urllib.parse import urlparse


class TargetType(str, Enum):
    """Types of targets that can be parsed."""
    IP = "ip"
    DOMAIN = "domain"
    URL = "url"
    IP_RANGE = "ip_range"
    SUBDOMAIN_LIST = "subdomain_list"
    AMBIGUOUS = "ambiguous"


class ParsedTarget(BaseModel):
    """Parsed and validated target information."""
    raw: str
    type: TargetType
    normalized: Union[str, List[str]]
    is_valid: bool
    error: Optional[str] = None

    class Config:
        use_enum_values = True


class TargetParser:
    """Parse and validate target inputs (IP, domain, URL, etc.)."""

    # Regex patterns
    IP_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )
    IP_RANGE_CIDR_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)/(?:[0-9]|[1-2][0-9]|3[0-2])$"
    )
    DOMAIN_PATTERN = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    )
    URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

    def parse(self, raw: str) -> ParsedTarget:
        """
        Parse a raw target string and determine its type.
        
        Args:
            raw: Raw target string from user input
            
        Returns:
            ParsedTarget with type, normalized value, and validation status
        """
        raw = raw.strip()

        if not raw:
            return ParsedTarget(
                raw=raw,
                type=TargetType.AMBIGUOUS,
                normalized=raw,
                is_valid=False,
                error="Empty target provided"
            )

        # Check for IP address
        if self.IP_PATTERN.match(raw):
            return ParsedTarget(
                raw=raw,
                type=TargetType.IP,
                normalized=raw,
                is_valid=True
            )

        # Check for IP range (CIDR notation)
        if self.IP_RANGE_CIDR_PATTERN.match(raw):
            return ParsedTarget(
                raw=raw,
                type=TargetType.IP_RANGE,
                normalized=raw,
                is_valid=True
            )

        # Check for URL
        if self.URL_PATTERN.match(raw):
            try:
                parsed_url = urlparse(raw)
                domain = parsed_url.netloc
                # Remove port if present
                if ":" in domain:
                    domain = domain.split(":")[0]
                return ParsedTarget(
                    raw=raw,
                    type=TargetType.URL,
                    normalized=domain.lower(),
                    is_valid=True
                )
            except Exception:
                return ParsedTarget(
                    raw=raw,
                    type=TargetType.AMBIGUOUS,
                    normalized=raw,
                    is_valid=False,
                    error="Invalid URL format"
                )

        # Check for domain
        if self.DOMAIN_PATTERN.match(raw):
            return ParsedTarget(
                raw=raw,
                type=TargetType.DOMAIN,
                normalized=raw.lower(),
                is_valid=True
            )

        # Ambiguous - cannot determine type
        return ParsedTarget(
            raw=raw,
            type=TargetType.AMBIGUOUS,
            normalized=raw,
            is_valid=False,
            error=f"Cannot determine target type for: {raw}. Please specify a valid IP, domain, or URL."
        )

    def parse_list(self, raw_list: List[str]) -> List[ParsedTarget]:
        """Parse a list of targets."""
        return [self.parse(item) for item in raw_list]

    def extract_domain_from_url(self, url: str) -> Optional[str]:
        """Extract domain from a URL string."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            if ":" in domain:
                domain = domain.split(":")[0]
            return domain.lower() if domain else None
        except Exception:
            return None
