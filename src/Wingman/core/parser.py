import re
from typing import List
from enum import StrEnum
from Wingman.core.status_indicator import StatusIndicator
from Wingman.core.resource_bar import ResourceBar
from Wingman.core.character import Character
from Wingman.core.group import Group

class MobMovement(StrEnum):
    LEAVING = "LEAVING"
    ENTERING = "ENTERING"

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
                    
                    # NEW: Exclude pets/mobs immediately
                    if not includePets and data['cls'] == 'mob':
                        continue

                    c = Character(data['name'],
                                data['cls'],
                                int(data['lvl']),
                                StatusIndicator.FromString(data['status']),
                                ResourceBar.FromString(data['hp']),
                                ResourceBar.FromString(data['fat']),
                                ResourceBar.FromString(data['pwr']))

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

    def parse_has_group_leader_disbanded_party(self, text: str, group:Group) -> bool:
        """
        Checks whether the group leader has disbanded the party.

        This does not work for disguised/shapeshifted leaders, too many assumptions would be needed.
        
        :param text: Line to parse
        :type text: str
        :param group: Current party group
        :type group: Group
        :return: True if the group leader disbanded the party, False otherwise
        :rtype: bool
        """
        if group.Leader is None:
            return False

        if ' disbanded their group.' not in text:
            return False
        
        groupLeaderName = r"(?P<leaderName>[A-Za-z -']+)"
        pattern = re.compile(f'{groupLeaderName} disbanded their group.', re.IGNORECASE)
        
        disbandingGroup = pattern.findall(text)
        return disbandingGroup[0] == group.Leader.Name
    
    class AfkStatus(StrEnum):
        BeginAfk = "You are now listed as AFK."
        EndAfk = "You are no longer AFK."
    def parseAfkStatus(self, text: str) -> bool | None:
        """
        Parse line of text to determine if it indicates AFK status.

        - True = `You are now listed as AFK.`
        - False = `You are no longer AFK.`
        - None = Anything else.

        :param text: line of text to parse
        :type text: str
        :return: True for AFK, False for not-AFK, None if doesn't deal with AFK status
        :rtype: bool | None
        """
        if "AFK" not in text:
            return None

        afkPattern = re.compile(self.AfkStatus.BeginAfk.value, re.IGNORECASE)
        foundAfk = afkPattern.findall(text)
        if len(foundAfk) > 0:
            return True

        notAfkPattern = re.compile(self.AfkStatus.EndAfk.value, re.IGNORECASE)
        notAfk = notAfkPattern.findall(text)
        if len(notAfk) > 0:
            return False
        
        return None
    
    class Meditation(StrEnum):
        Begin = "You slip into a meditative trance..."
        Termination_Voluntary = "You end your meditation."
        Termination_NonVoluntary = "Your meditation is interrupted."
    def parseMeditation(self, text: str) -> bool | None:
        """
        Parse line of text to determine if it indicates meditation status.

- True = `You slip into a meditative trance...`
- False = `You end your meditation.` or `Your meditation is interrupted.`
- None = Anything non-meditation-related.

        :param text: line of text to parse
        :type text: str
        :return: True for meditation-related, False for non-meditation-related, None if it doesn't deal with meditation status
        :rtype: bool | None
        """
        if self.Meditation.Begin.value in text:
            return True
        
        voluntaryTermination = self.Meditation.Termination_Voluntary.value
        nonVoluntaryTermination = self.Meditation.Termination_NonVoluntary.value
        meditatingEndPattern = re.compile(f"({voluntaryTermination}|{nonVoluntaryTermination})", re.IGNORECASE)
        hasMeditationEnded = meditatingEndPattern.findall(text)
        if len(hasMeditationEnded) > 0:
            return False
        
        return None
    
    class HideStatus(StrEnum):
        Begin = "You're hidden."
        AlreadyHidden = "You are already hiding."
        EndHiding = "You are no longer hidden."
    def parseHideStatus(self, text: str) -> bool | None:
        """
        Parse line of text to determine if it indicates hiding status.

        - True = `You're hidden.`
        - False = `You are no longer hidden.`
        - None = Anything else.

        :param text: line of text to parse
        :type text: str
        :return: True for hiding, False for not-hiding, None if doesn't deal with hiding status
        :rtype: bool | None
        """
        if self.HideStatus.Begin.value in text or self.HideStatus.AlreadyHidden.value in text:
            return True

        if self.HideStatus.EndHiding.value in text:
            return False
        
        return None

    class ParseMobs:
        def hasAnsiColorCodedMobs(self, text: str, outMobList: list[str]) -> bool:
            '''Parse text for mobs that still have Ansi color coding applied. The color codes permit parsing via `re` to get the mob names.

Method returns `True` if mobs are found with Ansi color coding, `False` otherwise.

The list passed in `outMobList` is populated with the found mobs if any are found, and cleared if none are found.
'''
            tempList = Parser().ParseMobs().parsePreAnsiScrubbingForMobs(text)
            if not tempList:
                outMobList.clear()
                return False
            
            outMobList.clear()
            outMobList.extend(tempList)
            return True

        def parsePreAnsiScrubbingForMobs(self, text: str) -> List[str]:
            r"""Parse pre-Ansi scrubbed input text for mobs in the room. 
```
\x1b[1;30m\x1b[1;30m\n\nAlso there is \x1b[1;31ma mithril dealer\x1b[1;30m\x1b[1;30m\x1b[1;30m.\n\n\n\x1b[8m
```
Ansi color codes are left in to aid in identifying mobs.
        
Works under the assumption that the Ansi foreground color of `31` is always used for mob coloring.

Looks for `Also there is ` to determine whether to parse or not.
```
Ansi				Olmran
BG	FC	Color			Color
30	40	Black	
31	41	Red			Red
32	42	Green			Green
33	43	Yellow			Brown
34	44	Blue			Blue
35	45	Magenta			Purple
36	46	Cyan			Cyan
37	47	White			Darkgrey
90	100	Bright Black (Gray)	Grey
91	101	Bright Red	        Lightred
92	102	Bright Green		Lightgreen
93	103	Bright Yellow		Yellow
94	104	Bright Blue		Lightblue
95	105	Bright Magenta		Lightpurple
96	106	Bright Cyan		Lightcyan
97	107	Bright White		White
```
"""
            if "Also there is " not in text:
                return []

            mobIndicator = r"(?P<subMob>\x1b\[1;31m(?P<name>[a-zA-Z '-,]+))+"
            searchPattern = re.compile(mobIndicator)
            foundMobs = searchPattern.findall(text)

            if not foundMobs:
                return []
            
            listedMobs = list[str]()
            for mob in foundMobs:
                listedMobs.append(mob[1])
            return listedMobs
    
    class ParseMovement:
        def playerMovement(self, text: str) -> bool:
            return "Obvious exits:" in text
            
        def mobRelatedMovement(self, text: str, mobsInRoom: list[str]) -> tuple[bool, MobMovement | None, str | None]:
            '''Parse text for mob related movement. Assumes `mobsInRoom` have their indefinite-articles (a, an) lower cased as part of `Also there is `.

- First Tuple Part: `bool` - `True` = mob movement occurred - `False` = no mob movement, remaining tuple parts are then `None`.
- Second Tuple Part: `MobMovement` - indicates the kind of movement, either entering/leaving.
- Last Tuple Part: `str` - the mob that moved.

Subsequent removal of mob from the model needs to be dealt with by the caller.'''
            text = text[:1].lower() + text[1:]
            isDeathMovement = "dies" in text
            isExitingRoom = 'leaves' in text or ('chases' in text and 'out of the room' in text)            
            if isDeathMovement or isExitingRoom:
                for mob in mobsInRoom:
                    if mob in text:
                        return True, MobMovement.LEAVING, mob
            
            if ' arrives from ' in text:
                index = text.find(' arrives from ')
                return True, MobMovement.ENTERING, text[:index]
            
            
            if ' enters the room' in text:
                index = text.find(' enters the room')
                return True, MobMovement.ENTERING, text[:index]

            if ' chases ' in text and ' into the room' in text:
                index = text.find(' chases ')
                return True, MobMovement.ENTERING, text[:index]

            return False, None, None

    class ParseBuffOrShieldText(StrEnum):
        NotApplicable = "Default value for `unassigned` values."

        BlurEnded = "The blur about you stops."
        BlurStarts = "You look very blurry!"
        ProtectEnded = "The magical sheen about you fades."
        ProtectStarts = "You are surrounded by a magical sheen!"
        ShieldEnded = "The glowing shield in front of you disappears."
        ShieldStarts = "You are fronted by a glowing shield!"
        ToughSkinEnded = "Your skin softens."
        ToughSkinStarts = "You get tougher skin!"

        #Chaos
        BleedResistEnded = "Your bleeding resistance fades."
        BleedResistStarts = "You look resistant to bleeding."
        ChaosFortitudeEnded = "The hale look about you fades."
        ChaosFortitudeStarts = "You look hale."
        CombatEnded = "The combat skill about you goes away."
        CombatStarts = "You look adept at combat skills!"
        DiseaseResistEnded = "Your disease resistance fades."
        DiseaseResistStarts = "You look resistant to disease."
        PoisonResistEnded = "Your poison resistance fades."
        PoisonResistStarts = "You look resistant to poison."

        #Good
        BlessEnded = "The blessed look about you fades."
        BlessStarts = "You look blessed!"

        #Evil
        RegenerateEnded = "The healthful glow surrounding you fades."
        RegenerateStarts = "You look extremely healthy!"
        VitalizeEnded = "The aura of vitality surrounding you fades."
        VitalizeStarts = "You look extremely vital!"

        @staticmethod
        def mapOfStartingToEndingEnumMembers() -> dict['Parser.ParseBuffOrShieldText', 'Parser.ParseBuffOrShieldText']:
            """Given a starting value for a buff or shield, return the corresponding ending value."""
            map = {
                Parser.ParseBuffOrShieldText.BlurStarts: Parser.ParseBuffOrShieldText.BlurEnded,
                Parser.ParseBuffOrShieldText.ProtectStarts: Parser.ParseBuffOrShieldText.ProtectEnded,
                Parser.ParseBuffOrShieldText.ShieldStarts: Parser.ParseBuffOrShieldText.ShieldEnded,
                Parser.ParseBuffOrShieldText.ToughSkinStarts: Parser.ParseBuffOrShieldText.ToughSkinEnded,

                #Chaos
                Parser.ParseBuffOrShieldText.BleedResistStarts: Parser.ParseBuffOrShieldText.BleedResistEnded,
                Parser.ParseBuffOrShieldText.ChaosFortitudeStarts: Parser.ParseBuffOrShieldText.ChaosFortitudeEnded,
                Parser.ParseBuffOrShieldText.CombatStarts: Parser.ParseBuffOrShieldText.CombatEnded,
                Parser.ParseBuffOrShieldText.DiseaseResistStarts: Parser.ParseBuffOrShieldText.DiseaseResistEnded,
                Parser.ParseBuffOrShieldText.PoisonResistStarts: Parser.ParseBuffOrShieldText.PoisonResistEnded,

                #Good
                Parser.ParseBuffOrShieldText.BlessStarts: Parser.ParseBuffOrShieldText.BlessEnded,

                #Evil
                Parser.ParseBuffOrShieldText.RegenerateStarts: Parser.ParseBuffOrShieldText.RegenerateEnded,
                Parser.ParseBuffOrShieldText.VitalizeStarts: Parser.ParseBuffOrShieldText.VitalizeEnded
            }

            return map

    def parseBuffOrShieldIsRefreshing(self, text: str) -> tuple[bool | None, ParseBuffOrShieldText | None]:
        """Parse text to determine if a buff or shield has refreshed, and if so, which spell it is.

If the text includes the ending and starting value for the spell, this is treated as a refresh of the buff/shield and results in a `True` return value.

- First Tuple Part: `bool` - `True` = a buff or shield has refreshed, `False` = buff or shield has ended, `None` - non-buff/shield related.
- Second Tuple Part: `ParseBuffOrShieldText` indicates which buff/shield has refreshed. `None` for non-buff/shield related."""
        if self.ParseBuffOrShieldText.ShieldEnded.value in text:
            if self.ParseBuffOrShieldText.ShieldStarts.value in text:
                return True, self.ParseBuffOrShieldText.ShieldStarts
            return False, self.ParseBuffOrShieldText.ShieldEnded

        if self.ParseBuffOrShieldText.BlurEnded.value in text:
            if self.ParseBuffOrShieldText.BlurStarts.value in text:
                return True, self.ParseBuffOrShieldText.BlurStarts
            return False, self.ParseBuffOrShieldText.BlurEnded

        if self.ParseBuffOrShieldText.ProtectEnded.value in text:
            if self.ParseBuffOrShieldText.ProtectStarts.value in text:
                return True, self.ParseBuffOrShieldText.ProtectStarts
            return False, self.ParseBuffOrShieldText.ProtectEnded

        if self.ParseBuffOrShieldText.ToughSkinEnded.value in text:
            if self.ParseBuffOrShieldText.ToughSkinStarts.value in text:
                return True, self.ParseBuffOrShieldText.ToughSkinStarts
            return False, self.ParseBuffOrShieldText.ToughSkinEnded

        #Chaos
        if self.ParseBuffOrShieldText.BleedResistEnded.value in text:
            if self.ParseBuffOrShieldText.BleedResistStarts.value in text:
                return True, self.ParseBuffOrShieldText.BleedResistStarts
            return False, self.ParseBuffOrShieldText.BleedResistEnded

        if self.ParseBuffOrShieldText.ChaosFortitudeEnded.value in text:
            if self.ParseBuffOrShieldText.ChaosFortitudeStarts.value in text:
                return True, self.ParseBuffOrShieldText.ChaosFortitudeStarts
            return False, self.ParseBuffOrShieldText.ChaosFortitudeEnded

        if self.ParseBuffOrShieldText.CombatEnded.value in text:
            if self.ParseBuffOrShieldText.CombatStarts.value in text:
                return True, self.ParseBuffOrShieldText.CombatStarts
            return False, self.ParseBuffOrShieldText.CombatEnded

        if self.ParseBuffOrShieldText.DiseaseResistEnded.value in text:
            if self.ParseBuffOrShieldText.DiseaseResistStarts.value in text:
                return True, self.ParseBuffOrShieldText.DiseaseResistStarts
            return False, self.ParseBuffOrShieldText.DiseaseResistEnded

        if self.ParseBuffOrShieldText.PoisonResistEnded.value in text:
            if self.ParseBuffOrShieldText.PoisonResistStarts.value in text:
                return True, self.ParseBuffOrShieldText.PoisonResistStarts
            return False, self.ParseBuffOrShieldText.PoisonResistEnded

        #Good
        if self.ParseBuffOrShieldText.BlessEnded.value in text:
            if self.ParseBuffOrShieldText.BlessStarts.value in text:
                return True, self.ParseBuffOrShieldText.BlessStarts
            return False, self.ParseBuffOrShieldText.BlessEnded

        #Evil
        if self.ParseBuffOrShieldText.RegenerateEnded.value in text:
            if self.ParseBuffOrShieldText.RegenerateStarts.value in text:
                return True, self.ParseBuffOrShieldText.RegenerateStarts
            return False, self.ParseBuffOrShieldText.RegenerateEnded

        if self.ParseBuffOrShieldText.VitalizeEnded.value in text:
            if self.ParseBuffOrShieldText.VitalizeStarts.value in text:
                return True, self.ParseBuffOrShieldText.VitalizeStarts
            return False, self.ParseBuffOrShieldText.VitalizeEnded

        return None, None
    
    class ParseSpellMitigationAffect(StrEnum):
        ToughSkin = "Your hardened skin tempers the impact!"
        BleedResist = "You start to bleed, but you are resistant!"
        DiseaseResist = "Disease starts to enter your system, but you are resistant!"
        PoisonResist = "Poison starts to enter your system, but you are resistant!"

    def parseSpellMitigationAffect(self, text: str) -> tuple[bool, str | None]:
        map = self.ParseSpellMitigationAffect._value2member_map_
        if map.__contains__(text):
            return True, map[text].name
        
        return False, None