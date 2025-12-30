import re
from typing import List, Dict, Any


def parse_xp_message(text_block: str) -> int:
    """Parses text for XP gains."""
    # Use finditer to find ALL occurrences in the block
    xp_pattern = re.compile(r'You gain\s+(\d+)(?:\s+\(\+(\d+)\))?.*experience', re.IGNORECASE)

    total_xp = 0
    for match in xp_pattern.finditer(text_block):
        base = int(match.group(1))
        bonus = int(match.group(2)) if match.group(2) else 0
        total_xp += (base + bonus)

    return total_xp


def parse_group_status(text_block: str) -> List[Dict[str, Any]]:
    """
    Parses a text block for group member status.
    Returns a list of dictionaries for valid rows found.
    """
    members = []

    # Regex Breakdown:
    # 1. Capture Class and Level inside brackets: [Orc 40]
    # 2. Capture optional Status (if present)
    # 3. Capture Name
    # 4. Capture HP, Fat, Power (e.g. "227/ 394") ignoring the percentages

    pattern = re.compile(
        r"\[\s*(?P<cls>[A-Za-z]+)\s+(?P<lvl>\d+)\s*\]"  # [Class Lvl]
        r"\s+"  # Space after bracket
        r"(?P<status>(?:[BPDS]\s)*)"  # Status: Only B, P, D, or S followed by a space (optional, repeated)
        r"(?P<name>.+?)"  # Name: Capture anything (including spaces) non-greedily...
        r"\s+"  # ...until the space before the HP
        r"(?P<hp>\d+/\s*\d+)"  # HP (This anchors the end of the name)
        r".*?"  # Skip percent
        r"\s+(?P<fat>\d+/\s*\d+)"  # Fat
        r".*?"  # Skip percent
        r"\s+(?P<pwr>\d+/\s*\d+)",  # Power
        re.DOTALL
    )

    for line in text_block.splitlines():
        if "]" in line and "/" in line:
            match = pattern.search(line)
            if match:
                # NEW: We must .strip() the status because '.*?' might catch surrounding spaces
                data = match.groupdict()
                data['status'] = data['status'].strip()
                members.append(data)

    return members
