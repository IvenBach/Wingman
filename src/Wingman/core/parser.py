import re
from typing import List, overload
from enum import Flag, auto

class StatusIndicator(Flag):
    BLEED = auto()
    POISON = auto()
    DISEASE = auto()
    STUN = auto()     

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StatusIndicator):
            return self.value == other.value

        if isinstance(other, str):
            other_flag = StatusIndicator.FromString(other)
            return self.value == other_flag.value

        return False
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __str__(self):
        match self:
            case StatusIndicator.BLEED:
                return "B"
            case StatusIndicator.POISON:
                return "P"
            case StatusIndicator.DISEASE:
                return "D"
            case StatusIndicator.STUN:
                return "S"
            case _:
                return ''

    @staticmethod
    def FromString(stringRepresentation: str) -> 'StatusIndicator':
        value = StatusIndicator(0)
        stringToFlag = {
            'B': StatusIndicator.BLEED,
            'P': StatusIndicator.POISON,
            'D': StatusIndicator.DISEASE,
            'S': StatusIndicator.STUN
        }
        for char in stringRepresentation:
            if char in stringToFlag:
                value |= stringToFlag[char]
        
        return value

class ResourceBar:
    def __init__(self, current: int, maximum: int):
        self.Current = current
        self.Maximum = maximum
    
    @staticmethod
    def FromString(value: str) -> 'ResourceBar':
        parts = value.strip().split('/')
        current = int(parts[0].strip())
        maximum = int(parts[1].strip())
        return ResourceBar(current, maximum)
    
    def __str__(self):
        return f"{self.Current}/{self.Maximum}"
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, ResourceBar):
            return self.Current == other.Current and self.Maximum == other.Maximum
        
        if isinstance(other, str):
            return self.__str__() == other.replace("/ ", "/")
        
        return False

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    
    def __repr__(self):
        return f"{self.Current}/{self.Maximum}"

class Character:
    def __init__(self, name: str, 
                        classProfession: str = "", 
                        level: int = -1, 
                        status: StatusIndicator = StatusIndicator(0), 
                        hp: ResourceBar = ResourceBar(-1,-1), 
                        fat: ResourceBar = ResourceBar(-1,-1), 
                        pow: ResourceBar = ResourceBar(-1,-1), 
                        isNewFollower: bool = False):
        self.Name = name.strip()
        
        self.ClassProfession = classProfession.strip(); """Restricted because of `class` keyword"""
        self.Level = level
        self.Status = status
        self.Hp = hp
        self.Fat = fat
        self.Pow = pow
        self.IsNewGroupFollower = isNewFollower

    def __repr__(self):
        return f"{self.Name}"


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


def parse_group_status(text_block: str, includePets: bool = False) -> List[Character]:
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
                data['hp'].split('/')
                data['fat'].split('/')
                data['pwr'].split('/')

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

def parse_leaveGroup(text: str) -> List[str]:
    """Input of text to check.
    
    :param text: The text to check for a leaving group member.

    :returns: The name of the member(s) who is/are leaving the group."""
    pattern = re.compile(r"(?P<leavingMember>([A-Za-z -]+)) disbands from (your|the) group", re.IGNORECASE)
    
    members = []
    leavingMembers = pattern.findall(text)
    for member in leavingMembers:
        members.append(member[1].strip())
    
    return members

class Group:
    '''
    Character group management class.
    '''
    def __init__(self, members: List[Character] = []):
        self._members: List[Character] = []
        if members:
            for member in members:
                self._members.append(member)

    @property
    def Leader(self) -> Character | None:
        return self._members[0] if self._members else None

    def TryFind(self, character: str, outCharacter: Character) -> bool:
        for member in self._members:
            if member.Name == character:
                outCharacter = member
                return True
        
        return False

    def Disband(self):
        self._members.clear()

    def AddMembers(self, newMembers: List[Character]):
        for member in newMembers:
            self._members.append(member)
    @overload
    def RemoveMembers(self, membersToRemove: List[str]): ...
    @overload
    def RemoveMembers(self, membersToRemove: List[Character]): ...

    def RemoveMembers(self, membersToRemove: List[Character] | List[str]):
        for memberToRemove in membersToRemove:
            if isinstance(memberToRemove, Character):
                if memberToRemove in self._members:
                    self._members.remove(memberToRemove)
            elif isinstance(memberToRemove, str):
                for member in self._members:
                    if member.Name == memberToRemove:
                        self._members.remove(member)

    def __iter__(self):
        return iter(self._members)

    @property
    def Count(self) -> int:
        '''Count of the members in the group.'''
        return len(self._members)
    
    @property
    def Members(self) -> List[Character]:
        '''List of members in the group.'''
        return self._members
    
    def __repr__(self):
        return f"{self.Leader.Name}'s group"