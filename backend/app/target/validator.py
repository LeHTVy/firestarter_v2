"""Target validation module for Firestarter AI."""

import os
import re
from typing import Tuple, List, Optional
from .parser import ParsedTarget


class TargetValidator:
    """
    Validate targets against blacklist.
    
    Blacklist is loaded from a markdown file with the following format:
    ```
    # Blacklist Targets
    - example.com
    - *.gov
    - 192.168.1.0/24
    ```
    """

    # Default blocked TLDs (always blocked regardless of blacklist file)
    DEFAULT_BLOCKED_TLDS = [".gov", ".mil"]

    def __init__(self, blacklist_path: Optional[str] = None):
        """
        Initialize validator with optional blacklist file.
        
        Args:
            blacklist_path: Path to blacklist.md file. If None, uses default path.
        """
        if blacklist_path is None:
            # Default path: backend/app/config/blacklist.md
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            blacklist_path = os.path.join(base_dir, "config", "blacklist.md")
        
        self.blacklist_path = blacklist_path
        self.blacklist: List[str] = []
        self._load_blacklist()

    def _load_blacklist(self) -> None:
        """Load blacklist from markdown file."""
        self.blacklist = []
        
        if not os.path.exists(self.blacklist_path):
            return
        
        try:
            with open(self.blacklist_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse markdown list items
            # Match lines starting with - or * followed by content
            pattern = re.compile(r"^[\-\*]\s+(.+)$", re.MULTILINE)
            matches = pattern.findall(content)
            
            for match in matches:
                item = match.strip()
                # Skip comments and empty items
                if item and not item.startswith("#") and not item.startswith("<!--"):
                    self.blacklist.append(item.lower())
                    
        except Exception as e:
            print(f"⚠️ Failed to load blacklist: {e}")

    def reload_blacklist(self) -> None:
        """Reload blacklist from file."""
        self._load_blacklist()

    def is_allowed(self, target: ParsedTarget) -> Tuple[bool, str]:
        """
        Check if target is allowed (not in blacklist).
        
        Args:
            target: ParsedTarget to validate
            
        Returns:
            Tuple of (is_allowed: bool, reason: str)
        """
        if not target.is_valid:
            return False, target.error or "Invalid target"

        # Get the domain/IP to check
        normalized = target.normalized
        if isinstance(normalized, list):
            # For lists, check all items
            for item in normalized:
                allowed, reason = self._check_single(item)
                if not allowed:
                    return False, reason
            return True, "All targets allowed"
        
        return self._check_single(normalized)

    def _check_single(self, value: str) -> Tuple[bool, str]:
        """Check a single target value against blacklist."""
        value = value.lower()

        # Check default blocked TLDs
        for tld in self.DEFAULT_BLOCKED_TLDS:
            if value.endswith(tld):
                return False, f"Target '{value}' is in a restricted TLD ({tld})"

        # Check blacklist
        for blocked in self.blacklist:
            # Wildcard matching (*.example.com)
            if blocked.startswith("*."):
                suffix = blocked[1:]  # Remove the *
                if value.endswith(suffix) or value == suffix[1:]:
                    return False, f"Target '{value}' matches blacklist pattern '{blocked}'"
            
            # Exact match
            elif value == blocked:
                return False, f"Target '{value}' is blacklisted"
            
            # Subdomain match
            elif value.endswith(f".{blocked}"):
                return False, f"Target '{value}' is a subdomain of blacklisted '{blocked}'"

        return True, "Target allowed"

    def add_to_blacklist(self, target: str) -> bool:
        """
        Add a target to the blacklist file.
        
        Args:
            target: Target to add
            
        Returns:
            True if successful
        """
        target = target.strip().lower()
        if target in self.blacklist:
            return True  # Already exists

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.blacklist_path), exist_ok=True)
            
            # Append to file
            with open(self.blacklist_path, "a", encoding="utf-8") as f:
                f.write(f"\n- {target}")
            
            self.blacklist.append(target)
            return True
        except Exception as e:
            print(f"❌ Failed to add to blacklist: {e}")
            return False
