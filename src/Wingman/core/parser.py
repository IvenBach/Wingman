import re
from typing import List
from Wingman.core.status_indicator import StatusIndicator
from Wingman.core.resource_bar import ResourceBar
from Wingman.core.character import Character

class Parser():
    def parse_xp_message(self, text_block: str) -> int:
        """Parses text for XP gains."""
        # Use finditer to find ALL occurrences in the block
        xp_pattern = re.compile(r'You gain\s+(\d+)(?:\s+\(\+(\d+)\))?.*experience', re.IGNORECASE)

        total_xp = 0
        for match in xp_pattern.finditer(text_block):
            base = int(match.group(1))
            bonus = int(match.group(2)) if match.group(2) else 0
            total_xp += (base + bonus)

        return total_xp
    
    def parse_group_status(self, text_block: str, includePets: bool = False) -> List[Character]:
        """
        Parses a text block for group member status.

        :returns: Returns a list of dictionaries for valid rows found.
        """
        members: List[Character] = []

        # Regex Breakdown:
        classAndLevel = r"\[\s*(?P<cls>[A-Za-z]+)\s+(?P<lvl>\d+)\s*\]"
        spaceAfterBracket = r"\s+"
        statusIndicators = r"(?P<status>(?:[BPDS]\s)*)"
        characterName = r"(?P<name>.+?)"
        health = r"\s+(?P<hp>\d+/\s*\d+)"
        skipPercentIndicators = r".*?"
        fatigue = r"\s+(?P<fat>\d+/\s*\d+)"
        power = r"\s+(?P<pwr>\d+/\s*\d+)"

        currentPartyMember = classAndLevel + spaceAfterBracket + statusIndicators + characterName \
                            + health + skipPercentIndicators \
                            + fatigue + skipPercentIndicators \
                            + power

        newFollowersName = r"(?P<NewGroupMember>[A-Za-z -]+)"
        newFollower = f"{newFollowersName} follows you"

        groupParserString = f"({currentPartyMember}|{newFollower})"

        pattern = re.compile(groupParserString,
            re.DOTALL
        )

        def isCurrentPartyMember(line: str) -> bool:
            return ']' in line and '/' in line

        def isNewFollower(line: str) -> bool:
            return 'follows you' in line

        for line in text_block.splitlines():
            if isCurrentPartyMember(line):
                match = pattern.search(line)
                if match:
                    data = match.groupdict()

                    c = Character(data['name'],
                                data['cls'],
                                int(data['lvl']),
                                StatusIndicator.FromString(data['status']),
                                ResourceBar.FromString(data['hp']),
                                ResourceBar.FromString(data['fat']),
                                ResourceBar.FromString(data['pwr']))
                    # NEW: Exclude pets/mobs immediately
                    if not includePets and c.ClassProfession == 'mob':
                        continue

                    members.append(c)

            elif isNewFollower(line):
                match = pattern.search(line)
                if match:
                    data = match.groupdict()
                    c = Character(data['NewGroupMember'],
                                isNewFollower=True)
                    members.append(c)

        return members

    def parse_leaveGroup(self, text: str) -> List[str]:
        """Input of text to check.

        :param text: The text to check for a leaving group member.

        :returns: The name of the member(s) who is/are leaving the group."""
        petArticleIdentifier = r"(?P<petArticleIdentifier>(A |An )?)"
        leavingMember = r"(?P<leavingMember>([A-Za-z -]+))"
        pattern = re.compile(f"{petArticleIdentifier}{leavingMember} disbands from (your|the) group", re.IGNORECASE)

        members = []
        leavingMembers = pattern.findall(text)
        for member in leavingMembers:
            members.append(member[2].strip())

        return members
