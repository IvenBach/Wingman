from collections import deque
import re
from typing import Iterable, List
from enum import StrEnum
from Wingman.core.parsing.connection_payload_bytes import ConnectionPayloadBytes
from Wingman.core.parsing.boat_docking_bytes import BoatNotificationBytes
from Wingman.core.mob_movement_event import MobMovementEvent
from Wingman.core.parsing.tokenstream import TokenStream
from Wingman.core.status_indicator import StatusIndicator
from Wingman.core.resource_bar import ResourceBar
from Wingman.core.character import Character
from Wingman.core.group import Group
from Wingman.core.inventory import Equipment, Inventory
from Wingman.core.item import Item, ItemSlot, ItemEnchantments
from Wingman.core.item import ItemMaterial_Cloth, ItemMaterial_Leather, ItemMaterial_Studded_And_Plate, ItemMaterial_Wood
from Wingman.core.affect import Affect
from Wingman.core.ansi_code_stripper import remove_ANSI_color_codes
from Wingman.core.mob_movement_event import MobMovementType, MobEnteringReasons, MobLeavingReasons
from Wingman.core.afk_status import AfkStatus

class Parser:
    MOB_NAME_REGEX_TEXT = r"[a-zA-Z ',\-]+"
    CHARACTER_NAME_REGEX_TEXT = r"[a-zA-Z '\-]+"

    SHAPESHIFTED_WEREWOLF_NAMES = frozenset([
        "small wolf",
        "fierce wolf",
        "berserking wolf",
        "crimson-furred wolf",
        "ebon-furred stonewolf",
        "ice-blue frostwolf",
        "fiery-maned hellwolf",
        "arctic ghostwolf",
        "white-fanged banewolf",
        "ethereal wraithwolf",
        "storm-grey thunderwolf",
        "icy cobalt tundrawolf",
        "fierce ancient ba'alwolf",
        "vapor-shrouded mistwolf",
        "azure-eyed stormwolf",
        "primeval eldritch voidwolf"
        ])

    class ParseXp:
        XP_PATTERN = re.compile(r"\d+")
        @staticmethod
        def tokenize_xp_line(text: str) -> list[int]:
            if not text.strip().startswith("You gain") and not text.strip().endswith("experience points."):
                return []

            return [int(x) for x in Parser.ParseXp.XP_PATTERN.findall(text) if x.isdigit()]

        @staticmethod
        def parse_xp_message(text_block: str) -> int:
            """Parses text for XP gains."""
            # Use finditer to find ALL occurrences in the block
            for line in text_block.splitlines():
                line = line.strip()
                if not line:
                    continue

                tokens = Parser.ParseXp.tokenize_xp_line(text_block)

            return sum(tokens)

    class ParseGroup:
        _MAX_NAME_WORDS = 6
        _CHAR_STATE_ENDING_SET = { 'Standing', 'Sitting', 'Kneeling', 'Lying' }

        _BRACKETS_TEXT = r"\[|\]"
        _RESOURCE_BAR_TEXT = r"\d+\/\s*\d+"
        _WORDS_TEXT = r"[A-Za-z]+(?:[-'][A-Za-z]+)*"
        _STANDALONE_NUMBERS_TEXT = r"\d+"
        _TOKENIZE_GROUP_PATTERN = re.compile(rf"{_BRACKETS_TEXT}|{_RESOURCE_BAR_TEXT}|{_WORDS_TEXT}|{_STANDALONE_NUMBERS_TEXT}")
        @staticmethod
        def tokenize_group_line(text: str) -> list[str]:
            return Parser.ParseGroup._TOKENIZE_GROUP_PATTERN.findall(text)

        @staticmethod
        def parse_current_member(tokens: list[str], includePets: bool) -> Character | None:
            ts = TokenStream(tokens)

            if ts.consume() != '[':
                return None

            class_ = ts.consume()
            possible_Level = ts.consume()
            if not possible_Level or not possible_Level.isdigit():
                return None
            level = int(possible_Level)

            if not includePets and class_ == 'mob':
                return None

            if ts.consume() != ']':
                return None

            status_tokens: list[str] = []
            while ts.peek() in {'B', 'P', 'D', 'S'}:
                status_tokens.append(ts.consume())

            name_parts: list[str] = []
            while ts.peek() and '/' not in ts.peek():
                name_parts.append(ts.consume())

            hp = ts.consume()
            _ = ts.consume() # skip over percentage if it exists
            fat = ts.consume()
            _ = ts.consume() # skip over percentage if it exists
            pow = ts.consume()
            _ = ts.consume() # skip over percentage if it exists

            return Character(' '.join(name_parts),
                            class_,
                            level,
                            StatusIndicator.FromString(status_tokens),
                            ResourceBar.FromString(hp),
                            ResourceBar.FromString(fat),
                            ResourceBar.FromString(pow)
            )

        @staticmethod
        def parse_new_follower(tokens: list[str]) -> Character | None:
            if len(tokens) < 3:
                return None

            if tokens[-2:] != ['follows', 'you']:
                return None

            i = len(tokens) - 3 # start of name is 3rd from the end
            potential_name_parts: list[str] = []
            while i >= 0 and len(potential_name_parts) < Parser.ParseGroup._MAX_NAME_WORDS:
                t = tokens[i]

                if t in Parser.ParseGroup._CHAR_STATE_ENDING_SET and tokens[i-1] == 'pos': #position: Standing, Sitting, Kneeling, Lying
                    break

                if not t.replace('-', "").replace("'", '').isalpha():
                    break

                potential_name_parts.append(t)
                i -= 1

            if not potential_name_parts:
                return None

            name = ' '.join(reversed(potential_name_parts))

            return Character(name, isNewFollower=True)

        @staticmethod
        def parse_dragged_corpse(tokens: list[str]) -> Character | None:
            if len(tokens) < 4:
                return None

            if tokens[0] != 'You' or tokens[1] != 'drag':
                return None

            name = tokens[2].removesuffix("'s")

            return Character(name, isNewFollower=True)

        @staticmethod
        def parse_group_status(text_block: str, includePets: bool = False) -> List[Character]:
            """
            Parses a text block for group member status.

            :returns: Returns a list of dictionaries for valid rows found.
            """
            members: List[Character] = []

            for line in text_block.splitlines():
                line = line.strip()
                if not line:
                    continue

                if line.endswith("group:"):
                    continue

                if line.startswith('[ Class'):
                    continue

                tokens = Parser.ParseGroup.tokenize_group_line(line)

                if line.startswith('['):
                    character = Parser.ParseGroup.parse_current_member(tokens, includePets)
                elif line.endswith('follows you'):
                    character = Parser.ParseGroup.parse_new_follower(tokens)
                elif line.startswith('You drag'):
                    character = Parser.ParseGroup.parse_dragged_corpse(tokens)
                else:
                    continue

                if character:
                    members.append(character)

            return members

    class ParseLeaveGroup:
        _TOKENIZE_PATTERN = re.compile(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", re.IGNORECASE)
        @staticmethod
        def tokenize_leave_group_line(text: str) -> list[str]:
            return Parser.ParseLeaveGroup._TOKENIZE_PATTERN.findall(text)

        @staticmethod
        def parse_leaveGroup(text: str) -> List[str]:
            """Input of text to check.

            :param text: The text to check for a leaving group member.

            :returns: The name of the member(s) who is/are leaving the group."""
            members = []

            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue

                tokens = Parser.ParseLeaveGroup.tokenize_leave_group_line(line)

                if len(tokens) < 5:
                    continue

                if tokens[-4:] not in (
                    ['disbands', 'from', 'your', 'group'],
                    ['disbands', 'from', 'the', 'group'],
                ):
                    continue

                i = len(tokens) - 5
                potential_name_parts: list[str] = []
                while i >= 0 and len(potential_name_parts) < Parser.ParseGroup._MAX_NAME_WORDS:
                    t = tokens[i]

                    if t in Parser.ParseGroup._CHAR_STATE_ENDING_SET and tokens[i-1] == 'pos':
                        break

                    if t == 'An' or t == 'A':
                        break

                    if not t.replace('-', "").replace("'", '').isalpha():
                        break

                    potential_name_parts.append(t)
                    i -= 1

                if not potential_name_parts:
                    continue

                name = ' '.join(reversed(potential_name_parts))
                members.append(name)

            return members

    class ParseGroupDisband:
        @staticmethod
        def parse_has_group_leader_disbanded_party(text: str, group:Group) -> bool:
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

            if not text.endswith(' disbanded their group.'):
                return False

            disbandingLeaderName = text.split()[0]
            return disbandingLeaderName == group.Leader.Name

    class ParseAfk:
        @staticmethod
        def parseAfkStatus(text: str) -> bool | None:
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
            if not text.endswith("AFK."):
                return None

            if text == AfkStatus.BeginAfk.value:
                return True

            if text == AfkStatus.EndAfk.value:
                return False

            return None

    class MeditationState(StrEnum):
        Begin = "You slip into a meditative trance..."
        Termination_ByStanding = "You stand up.\nYou end your meditation."
        Termination_ByFullPower = "You end your meditation."
        Termination_ByInterruption = "Your meditation is interrupted."
    def parseMeditation(self, text: str) -> tuple[bool | None, MeditationState | None]:
        """
        Parse line of text to determine if it indicates meditation status.

- First Tuple Element: `True` = meditation has begun, `False` = meditation has ended, `None` = non-meditation related.
- Second Tuple Element: The enum member indicating the meditation status. `None` for non-meditation related.
"""
        if self.MeditationState.Begin.value in text:
                return True, self.MeditationState.Begin
        if self.MeditationState.Termination_ByStanding.value in text:
                return False, self.MeditationState.Termination_ByStanding
        if self.MeditationState.Termination_ByFullPower.value in text:
                return False, self.MeditationState.Termination_ByFullPower
        if self.MeditationState.Termination_ByInterruption.value in text:
                return False, self.MeditationState.Termination_ByInterruption

        return None, None

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
        _RED_TEXT_PATTERN = re.compile(
            r"\x1b\[1;31m(.*?)\x1b\[[0-9;]*m",
            re.DOTALL
        )

        _GREEN_TEXT_PATTERN = re.compile(
            r"\x1b\[1;32m(.*?)\x1b\[[0-9;]*m",
            re.DOTALL
        )

        @staticmethod
        def textFromGreenMobs(text: str) -> List[str]:
            return Parser.ParseMobs._textFromColoredMobs(Parser.ParseMobs._GREEN_TEXT_PATTERN, text)

        @staticmethod
        def textFromRedMobs(text: str) -> List[str]:
            return Parser.ParseMobs._textFromColoredMobs(Parser.ParseMobs._RED_TEXT_PATTERN, text)

        @staticmethod
        def _textFromColoredMobs(colorPattern: re.Pattern[str], text: str) -> list[str]:
            r"""Parse pre-Ansi scrubbed input text for mobs in the room. 
```
\x1b[1;30m\x1b[1;30m\n\nAlso there is \x1b[1;31ma mithril dealer\x1b[1;30m\x1b[1;30m\x1b[1;30m.\n\n\n\x1b[8m
```
Ansi color codes are left in to aid in identifying mobs.

Works under the assumption that the Ansi foreground color of `31` (Red) is always used for mob coloring.

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

            foundMobs = colorPattern.findall(text)
            cleanedMobs = [m.strip().rstrip('.,') for m in foundMobs if m.strip()]

            if not cleanedMobs:
                return []

            return cleanedMobs

    class ParseMovement:
        VERBS = { 'arrives', 'enters', 'leaves', 'dies', 'chases' }
        CHASE_DIRECTIONS = { 'into', 'out' }
        ARTICLES = { 'a', 'an' }

        @staticmethod
        def tokenize_movement(text: str) -> list[str]:
            return re.findall(r"[a-zA-Z',\-]+", text.lower())
        def playerMovement(self, text: str) -> bool:
            return "Obvious exits:" in text

        @staticmethod
        def parseMobMovements(text:str) -> tuple[list[MobMovementEvent], list[tuple[int, int]]]:
            '''Parse text for mob related movement.
- First Tuple Element: A list of `MobMovementEvent`s indicating the mob movement events parsed from the text.
- Second Tuple Element: A list of tuples indicating the indices in the text where mob movement related text was found.

Subsequent removal of mob from the model needs to be dealt with by the caller.'''
            movements: list[MobMovementEvent] = []
            indices: list[tuple[int, int]] = []

            duplicateMobNameOffset: int = 0
            checkedMobNames: set[str] = set()
            for raw_line in text.splitlines(keepends=True):
                line = raw_line.strip()
                if not line: continue

                tokens = Parser.ParseMovement.tokenize_movement(line)

                if not Parser.ParseMovement.VERBS.intersection(tokens):
                    continue

                isMovement, movement, reason, mobName, isChasingYou = Parser.ParseMovement._mobRelatedMovement_SingleLine(tokens)

                if isMovement:
                    assert movement is not None
                    assert reason is not None
                    assert mobName is not None
                    movements.append(MobMovementEvent(movement, reason, mobName, isChasingYou))

                    if mobName in checkedMobNames:
                        duplicateMobNameOffset += len(line)
                        startIndex = text.find(line, duplicateMobNameOffset)
                    else:
                        startIndex = text.find(line)
                        checkedMobNames.add(mobName)

                    endIndex = startIndex + len(line)
                    indices.append((startIndex, endIndex))

            return movements, indices

        @staticmethod
        def _mobRelatedMovement_SingleLine(tokenList: list[str]) -> tuple[bool, MobMovementType | None, MobEnteringReasons | MobLeavingReasons | None, str | None, bool]:
            """An empty list indicates no mob related movement. Each tuple in the returned list indicates a mob movement, and includes the following elements:
- First Tuple Element: `bool` - `True` = mob movement occurred - `False` = no mob movement, remaining Tuple Elements are then `None`.
- Second Tuple Element: `MobMovement` - indicates either entering/leaving.
- Third Tuple Element: (`MobEnteringReason`|`MobLeavingReason`) Enum - indicates the specific kind of entering or leaving movement. `None` if no mob movement.
- Fourth Tuple Element: `list[str]` - the mob(s) that moved.
- Last Tuple Element: `bool` - `True` if chasing you, `False` otherwise."""
            tokens = TokenStream(tokenList)

            #deal with extraneous text before the mob movement text
            while tokens.peek() and tokens.peek() not in Parser.ParseMovement.ARTICLES:
                if tokens.consume() is None:
                    return False, None, None, None, False

            article = tokens.consume_if(Parser.ParseMovement.ARTICLES)
            if not article:
                return False, None, None, None, False

            mobNameParts = []

            while tokens.peek() and tokens.peek() not in Parser.ParseMovement.VERBS:
                partOfMobName = tokens.consume()
                if partOfMobName is None:
                    return False, None, None, None, False

                mobNameParts.append(partOfMobName)

            unarticledMobName = ' '.join(mobNameParts)
            if unarticledMobName in Parser.SHAPESHIFTED_WEREWOLF_NAMES:
                return False, None, None, None, False

            mobName = f"{article} {unarticledMobName}"

            verb = tokens.consume()

            match verb:
                case 'leaves':
                    return True, MobMovementType.LEAVING, MobLeavingReasons.LEAVES, mobName, False
                case 'dies':
                    return True, MobMovementType.LEAVING, MobLeavingReasons.DIES, mobName, False
                case 'arrives':
                    tokens.consume_if("from")
                    tokens.consume_if("the")
                    tokens.consume() # direction
                    return True, MobMovementType.ENTERING, MobEnteringReasons.ARRIVES_FROM, mobName, False
                case 'enters':
                    tokens.consume_if('the')
                    tokens.consume_if('room')
                    return True, MobMovementType.ENTERING, MobEnteringReasons.ENTERS_THE_ROOM, mobName, False
                case 'chases':
                    characterTokens: list[str] = []
                    while tokens.peek() and  tokens.peek() not in Parser.ParseMovement.CHASE_DIRECTIONS:
                        characterTokens.append(tokens.consume())
                    character = ' '.join(characterTokens)

                    if tokens.isEmpty():
                        raise ValueError("Mob movement text indicates chasing but no direction provided.")

                    direction = tokens.consume()
                    tokens.consume_if('the')
                    tokens.consume_if('room')
                    areYouBeingChased = character == 'you'
                    if direction == 'out':
                        return True, MobMovementType.LEAVING, MobLeavingReasons.CHASES, mobName, areYouBeingChased
                    else:
                        return True, MobMovementType.ENTERING, MobEnteringReasons.CHASES, mobName, areYouBeingChased

            return False, None, None, None, False

    class ParseBuffOrShieldText(StrEnum):
        Blur_Ended = "The blur about you stops."
        BlurStarts = "You look very blurry!"
        Protect_Ended = "The magical sheen about you fades."
        ProtectStarts = "You are surrounded by a magical sheen!"
        Shield_Ended = "The glowing shield in front of you disappears."
        ShieldStarts = "You are fronted by a glowing shield!"
        ToughDotSkin_Ended = "Your skin softens."
        ToughDotSkinStarts = "You get tougher skin!"

        #Chaos
        BleedDotResist_Ended = "Your bleeding resistance fades."
        BleedDotResistStarts = "You look resistant to bleeding."
        ChaosDotFortitude_Ended = "The hale look about you fades."
        ChaosDotFortitudeStarts = "You look hale."
        Combat_Ended = "The combat skill about you goes away."
        CombatStarts = "You look adept at combat skills!"
        DiseaseDotResist_Ended = "Your disease resistance fades."
        DiseaseDotResistStarts = "You look resistant to disease."
        PoisonDotResist_Ended = "Your poison resistance fades."
        PoisonDotResistStarts = "You look resistant to poison."

        #Good
        Bless_Ended = "The blessed look about you fades."
        BlessStarts = "You look blessed!"

        #Evil
        Regenerate_Ended = "The healthful glow surrounding you fades."
        RegenerateStarts = "You look extremely healthy!"
        Vitalize_Ended = "The aura of vitality surrounding you fades."
        VitalizeStarts = "You look extremely vital!"

        @staticmethod
        def mapOfStartingToEndingEnumMembers() -> dict['Parser.ParseBuffOrShieldText', 'Parser.ParseBuffOrShieldText']:
            """Given a starting value for a buff or shield, return the corresponding ending value."""
            map = {
                Parser.ParseBuffOrShieldText.BlurStarts: Parser.ParseBuffOrShieldText.Blur_Ended,
                Parser.ParseBuffOrShieldText.ProtectStarts: Parser.ParseBuffOrShieldText.Protect_Ended,
                Parser.ParseBuffOrShieldText.ShieldStarts: Parser.ParseBuffOrShieldText.Shield_Ended,
                Parser.ParseBuffOrShieldText.ToughDotSkinStarts: Parser.ParseBuffOrShieldText.ToughDotSkin_Ended,

                #Chaos
                Parser.ParseBuffOrShieldText.BleedDotResistStarts: Parser.ParseBuffOrShieldText.BleedDotResist_Ended,
                Parser.ParseBuffOrShieldText.ChaosDotFortitudeStarts: Parser.ParseBuffOrShieldText.ChaosDotFortitude_Ended,
                Parser.ParseBuffOrShieldText.CombatStarts: Parser.ParseBuffOrShieldText.Combat_Ended,
                Parser.ParseBuffOrShieldText.DiseaseDotResistStarts: Parser.ParseBuffOrShieldText.DiseaseDotResist_Ended,
                Parser.ParseBuffOrShieldText.PoisonDotResistStarts: Parser.ParseBuffOrShieldText.PoisonDotResist_Ended,

                #Good
                Parser.ParseBuffOrShieldText.BlessStarts: Parser.ParseBuffOrShieldText.Bless_Ended,

                #Evil
                Parser.ParseBuffOrShieldText.RegenerateStarts: Parser.ParseBuffOrShieldText.Regenerate_Ended,
                Parser.ParseBuffOrShieldText.VitalizeStarts: Parser.ParseBuffOrShieldText.Vitalize_Ended
            }

            return map

    def parseBuffOrShieldIsRefreshing(self, text: str) -> tuple[bool | None, ParseBuffOrShieldText | None]:
        """Parse text to determine if a buff or shield has refreshed, and if so, which spell it is.

If the text includes the ending and starting value for the spell, this is treated as a refresh of the buff/shield and results in a `True` return value.

- First Tuple Element: `bool` - `True` = a buff or shield has refreshed, `False` = buff or shield has ended, `None` - non-buff/shield related.
- Second Tuple Element: `ParseBuffOrShieldText` indicates which buff/shield has started/ended. `None` for non-buff/shield related."""
        if self.ParseBuffOrShieldText.Shield_Ended.value in text:
            if self.ParseBuffOrShieldText.ShieldStarts.value in text:
                return True, self.ParseBuffOrShieldText.ShieldStarts
            return False, self.ParseBuffOrShieldText.Shield_Ended

        if self.ParseBuffOrShieldText.Blur_Ended.value in text:
            if self.ParseBuffOrShieldText.BlurStarts.value in text:
                return True, self.ParseBuffOrShieldText.BlurStarts
            return False, self.ParseBuffOrShieldText.Blur_Ended

        if self.ParseBuffOrShieldText.Protect_Ended.value in text:
            if self.ParseBuffOrShieldText.ProtectStarts.value in text:
                return True, self.ParseBuffOrShieldText.ProtectStarts
            return False, self.ParseBuffOrShieldText.Protect_Ended

        if self.ParseBuffOrShieldText.ToughDotSkin_Ended.value in text:
            if self.ParseBuffOrShieldText.ToughDotSkinStarts.value in text:
                return True, self.ParseBuffOrShieldText.ToughDotSkinStarts
            return False, self.ParseBuffOrShieldText.ToughDotSkin_Ended

        #Chaos
        if self.ParseBuffOrShieldText.BleedDotResist_Ended.value in text:
            if self.ParseBuffOrShieldText.BleedDotResistStarts.value in text:
                return True, self.ParseBuffOrShieldText.BleedDotResistStarts
            return False, self.ParseBuffOrShieldText.BleedDotResist_Ended

        if self.ParseBuffOrShieldText.ChaosDotFortitude_Ended.value in text:
            if self.ParseBuffOrShieldText.ChaosDotFortitudeStarts.value in text:
                return True, self.ParseBuffOrShieldText.ChaosDotFortitudeStarts
            return False, self.ParseBuffOrShieldText.ChaosDotFortitude_Ended

        if self.ParseBuffOrShieldText.Combat_Ended.value in text:
            if self.ParseBuffOrShieldText.CombatStarts.value in text:
                return True, self.ParseBuffOrShieldText.CombatStarts
            return False, self.ParseBuffOrShieldText.Combat_Ended

        if self.ParseBuffOrShieldText.DiseaseDotResist_Ended.value in text:
            if self.ParseBuffOrShieldText.DiseaseDotResistStarts.value in text:
                return True, self.ParseBuffOrShieldText.DiseaseDotResistStarts
            return False, self.ParseBuffOrShieldText.DiseaseDotResist_Ended

        if self.ParseBuffOrShieldText.PoisonDotResist_Ended.value in text:
            if self.ParseBuffOrShieldText.PoisonDotResistStarts.value in text:
                return True, self.ParseBuffOrShieldText.PoisonDotResistStarts
            return False, self.ParseBuffOrShieldText.PoisonDotResist_Ended

        #Good
        if self.ParseBuffOrShieldText.Bless_Ended.value in text:
            if self.ParseBuffOrShieldText.BlessStarts.value in text:
                return True, self.ParseBuffOrShieldText.BlessStarts
            return False, self.ParseBuffOrShieldText.Bless_Ended

        #Evil
        if self.ParseBuffOrShieldText.Regenerate_Ended.value in text:
            if self.ParseBuffOrShieldText.RegenerateStarts.value in text:
                return True, self.ParseBuffOrShieldText.RegenerateStarts
            return False, self.ParseBuffOrShieldText.Regenerate_Ended

        if self.ParseBuffOrShieldText.Vitalize_Ended.value in text:
            if self.ParseBuffOrShieldText.VitalizeStarts.value in text:
                return True, self.ParseBuffOrShieldText.VitalizeStarts
            return False, self.ParseBuffOrShieldText.Vitalize_Ended

        return None, None

    class SpellMitigationAffect(StrEnum):
        '''Spells that provide a mitigating affect. Whether reduced damage or preventing a status affect like Bleed, Poison, or Disease (BPD).'''
        ToughDotSkin = "Your hardened skin tempers the impact!"
        BleedDotResist = "You start to bleed, but you are resistant!"
        DiseaseDotResist = "Disease starts to enter your system, but you are resistant!"
        PoisonDotResist = "Poison starts to enter your system, but you are resistant!"

    def parseSpellMitigationAffect(self, text: str) -> tuple[bool, SpellMitigationAffect | None]:
        '''Parses text for a mitigating affect related to a spell.

- First Tuple Element: `bool` - `True` = pertains to spell mitigation, `False` otherwise.
- Second Tuple Element: The enum member indicating the reason for the mitigation. `None` if the text does not pertain to spell mitigation.'''

        map = self.SpellMitigationAffect._value2member_map_
        if map.__contains__(text):
            return True, map[text]

        return False, None

    def parseInventory(self, text: str) -> Inventory | None:
        '''Parses the text for the contents of the player's inventory.
        Current implementation limitations:
- Assumes gear to be fully equipped with no empty slots. If there are any empty slots then some worn gear will be placed in order: 
Head, Jewel1, Jewel2, Cloak, Body, Hands, Legs, Feet, Held_Right, Held_Left.
- Cannot differentiate 2handed items from 1handed items. Will list a 2handed item held in one hand.

TODO: Future update to correct the above limitation: `equipment` should be executed to display equipped items.
That parse is intended to overwrite with the correct worn gear.'''
        if "Inventory:" not in text:
            return None

        eg = Equipment()
        backpackStartIndex = 1
        lines = text.split('\n')
        equippedText = [line[6:] for line in lines if line.startswith("  (w) ")]

        wornCounter = 0
        for wornCounter, line in enumerate(equippedText):
            match wornCounter:
                case 0:
                    eg.Head = Item(line, slot=ItemSlot.HEAD)
                case 1:
                    eg.Jewel1 = Item(line, slot=ItemSlot.JEWEL)
                case 2:
                    eg.Jewel2 = Item(line, slot=ItemSlot.JEWEL)
                case 3:
                    eg.Cloak = Item(line, slot=ItemSlot.CLOAK)
                case 4:
                    eg.Body = Item(line, slot=ItemSlot.BODY)
                case 5:
                    eg.Hands = Item(line, slot=ItemSlot.HANDS)
                case 6:
                    eg.Legs = Item(line, slot=ItemSlot.LEGS)
                case 7:
                    eg.Feet = Item(line, slot=ItemSlot.FEET)

        heldText = [line[6:] for line in lines if line.startswith("  (h) ")]
        for heldCounter, line in enumerate(heldText):
            match heldCounter:
                case 0:
                    eg.Held_Right = Item(line, slot=ItemSlot.HELD)
                case 1:
                    eg.Held_Left = Item(line, slot=ItemSlot.HELD)

        backpackStartIndex = len(equippedText) + len(heldText) + 1

        footerLines = 0
        if '\n\n' in text:
            footerLines += 1
        if self._inventoryCountFooterPattern().findall(text):
            footerLines += 1
        if self._inventoryWeightFooterPattern().findall(text):
            footerLines += 1

        createFrom = lines[backpackStartIndex: len(lines) - footerLines]
        backpack = [self.ParseQuantityItem.parseQuantityItem(line) for line in createFrom]

        return Inventory(eg, backpack)

    _INVENTORY_COUNT_FOOTER_PATTERN = re.compile(r"Inventory:\s+(\d|\w)+\s*/\s*(\d|\w)+")
    def _inventoryCountFooterPattern(self) -> re.Pattern[str]:
        '''Pattern to search for inventory count footer `Inventory: xx / XX`'''
        return self._INVENTORY_COUNT_FOOTER_PATTERN

    _INVENTORY_WEIGHT_FOOTER_PATTERN = re.compile(r"Encumbrance:\s+(\d|\w)+\s*/\s*(\d|\w)+")
    def _inventoryWeightFooterPattern(self) -> re.Pattern[str]:
        '''Pattern to search for inventory weight footer `Encumbrance: yy / YYY`'''
        return self._INVENTORY_WEIGHT_FOOTER_PATTERN

    EQUIPPED_GEAR_PATTERN = re.compile(r"On (Head|Jewel|Cloak|Body|Hands|Legs|Feet|Held Right|Held Left):  .+")
    def parseEquippedGear(self, text: str) -> Equipment | None:
        if not Parser.EQUIPPED_GEAR_PATTERN.findall(text):
            return None

        eg = Equipment()
        lines = [lines.strip() for lines in text.split("\n")]
        for line in lines:
            if "Items in use:" in line:
                continue

            delimiter = ":  "
            delimiterIndex = line.find(delimiter)
            prefix = line[:delimiterIndex + len(delimiter)]
            name = line[len(prefix):]
            if name == 'nothing':
                continue

            match prefix:
                case "On Head:  ":
                    eg.Head = Item(name, slot=ItemSlot.HEAD)
                case "On Jewel:  ":
                    if eg.Jewel1 is None:
                        eg.Jewel1 = Item(name, slot=ItemSlot.JEWEL)
                    else:
                        eg.Jewel2 = Item(name, slot=ItemSlot.JEWEL)
                case "On Cloak:  ":
                    eg.Cloak = Item(name, slot=ItemSlot.CLOAK)
                case "On Body:  ":
                    eg.Body = Item(name, slot=ItemSlot.BODY)
                case "On Hands:  ":
                    eg.Hands = Item(name, slot=ItemSlot.HANDS)
                case "On Legs:  ":
                    eg.Legs = Item(name, slot=ItemSlot.LEGS)
                case "On Feet:  ":
                    eg.Feet = Item(name, slot=ItemSlot.FEET)
                case "Held Right:  ":
                    eg.Held_Right = Item(name, slot=ItemSlot.HELD)
                case "Held Left:  ":
                    eg.Held_Left = Item(name, slot=ItemSlot.HELD)

        return eg

    class ParseQuantityItem:
        _QUANTITY_ITEM_PATTERN = re.compile(rf"""
            ^\s*                # optional leading whitespace
            (?:                 # optional quantity group
                \(
                \s*(\d+)\s*     # capture quantity
                \)
                \s*             # whitespace after quantity
            )?
            (.+?)               # capture item name (greedily)
            \s*$                # optional trailing whitespace
""", re.VERBOSE)

        @staticmethod
        def tokenize_quantity_item_line(line: str) -> tuple[int | None, str]:
            """Returns a tuple containing the quantity and item name.

- First Tuple Element: `int` quantity if parenthesis with a number is found, `None` otherwise.
- Second Tuple Element: `str` item name, with leading and trailing whitespace removed."""
            match = Parser.ParseQuantityItem._QUANTITY_ITEM_PATTERN.findall(line)[0]

            if len(match) !=  1 and len(match) != 2:
                raise ValueError(f"Unexpected token count when parsing quantity item line: {line}\nTokens: {match}")

            if len(match) == 1:
                return (None, match[0].strip())

            if len(match) == 2:
                potentialQuantity = match[0].strip()
                quantity = int(potentialQuantity) if potentialQuantity.isdigit() else None
                return (quantity, match[1].strip())

            return (None, line)

        @staticmethod
        def parseQuantityItem(lineOfText: str) -> Item:
            '''Parses text for an item with quantity.

    Assumes any item lacking quantity parenthesis to be a non-quantity item and assigns it a `None` quantity.'''
            tokens = Parser.ParseQuantityItem.tokenize_quantity_item_line(lineOfText)
            if not tokens:
                raise ValueError(f"Could not parse item from line of text: {lineOfText}. Expected token count of `4` not met.")

            if len(tokens) != 2:
                raise ValueError(f"Could not parse item from line of text: {lineOfText}. Expected token count of `4` not met.\nTokens: {tokens}")

            quantity, name = tokens
            return Item(name, quantity=quantity)

    class ParseAffect:
        _AFFECT_NAME_TEXT = r"(?P<affectName>\S+)"
        #https://www.regextutorial.org/positive-and-negative-lookahead-assertions.php
        _POSITIVE_LOOKAHEAD_TEXT = r"(?=(?:.*\d+[hms]))" # asserts the regex includes a time component

        _HOURS_TEXT = r"(?:(?P<hours>\d+)h\s*)?" # capture group for time portion
        _MINUTES_TEXT = r"(?:(?P<minutes>\d+)m\s*)?"
        _SECONDS_TEXT = r"(?:(?P<seconds>\d+)s\s*)?"
        _TIME_TEXT = r"(?P<time>" + _HOURS_TEXT + _MINUTES_TEXT + _SECONDS_TEXT + r")"
        PATTERN = re.compile(r"^\s*" + _AFFECT_NAME_TEXT + r"(?:\s+" + _POSITIVE_LOOKAHEAD_TEXT + _TIME_TEXT + r")?\s*$",
            re.MULTILINE)

        def parseAffects(self, text: str) -> tuple[bool, list[Affect], tuple[int, int]]:
            '''Parses text for affects.
- First Tuple Element: `bool` - `True` = text contains affects, `False` = text does not contain affects
- Second Tuple Element: `list[Affect]` - list of Affect objects parsed from the text, or empty list if no affects are found.
- Third Tuple Element: tuple[int, int] - start and end index of the affects block in the text, `(-1, -1)` if no affects are found.'''
            startIndex = text.find("\x1b[1mYou are affected by: ")
            endingText = "\n\n\n\n\x1b[8m"
            endIndex = text.find(endingText, startIndex) + len(endingText) if startIndex > -1 else -1

            cleanedText = remove_ANSI_color_codes(text)

            if "You are affected by:" not in cleanedText or "You are affected by:\n" == cleanedText or "You are affected by: \n" == cleanedText:
                return (False, [], (-1, -1))

            affects: list[Affect] = []
            for line in Parser.ParseAffect.PATTERN.finditer(cleanedText):
                affectName = line.groupdict('affectName')['affectName']

                if line.lastgroup == 'affectName':
                    affects.append(Affect(affectName, None))
                else:
                    timeGroup = line.groupdict('time')
                    timeHours = int(timeGroup['hours']) * 3600 if timeGroup['hours'].isnumeric() else 0
                    timeMinutes = int(timeGroup['minutes']) * 60 if timeGroup['minutes'].isnumeric() else 0
                    timeSeconds = int(timeGroup['seconds']) if timeGroup['seconds'].isnumeric() else 0
                    durationLength = timeHours + timeMinutes + timeSeconds
                    affects.append(Affect(affectName, durationLength))

            return True, affects, (startIndex, endIndex)

        def parseAffectTime(self, text: str) -> float | None:
            match = Parser.ParseAffect.PATTERN.search(text)
            if not match:
                return None

            if match.lastgroup == 'affectName':
                return None

            hours = int(match.group("hours")) if match.group("hours") else 0
            minutes = int(match.group("minutes")) if match.group("minutes") else 0
            seconds = int(match.group("seconds")) if match.group("seconds") else 0

            return hours * 3600 + minutes * 60 + seconds



    ENCHANTMENT_NAMES = frozenset(e.lower() for e in ItemEnchantments._member_names_)

    CLOTH_MATERIAL_NAMES = frozenset(m.lower() for m in ItemMaterial_Cloth._member_names_)
    LEATHER_MATERIAL_NAMES = frozenset(m.lower() for m in ItemMaterial_Leather._member_names_)
    STUDDED_AND_PLATE_MATERIAL_NAMES = frozenset(m.lower() for m in ItemMaterial_Studded_And_Plate._member_names_)
    WOOD_MATERIAL_NAMES = frozenset(m.lower() for m in ItemMaterial_Wood._member_names_)
    MATERIAL_NAMES = frozenset(
        CLOTH_MATERIAL_NAMES
        | LEATHER_MATERIAL_NAMES
        | STUDDED_AND_PLATE_MATERIAL_NAMES
        | WOOD_MATERIAL_NAMES
    )

    ARTICLES = frozenset(["the", "an", "a"])

    @staticmethod
    def tokenizeItemText(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z'\-]+", text.lower())

    @staticmethod
    def consumeIf(tokens: deque[str], validSet: Iterable[str]) -> str | None:
        if tokens and tokens[0] in validSet:
            return tokens.popleft()
        return None

    @staticmethod
    def parseItem(text: str) -> Item | None:
        '''Parse text for an item.'''
        def addPrefixToRemainingTokens(prefix: str, remainingTokens: list[str]) -> list[str]:
            result = [prefix]
            result.extend(remainingTokens)
            return result

        enchantment = None
        material = None

        tokens = TokenStream(Parser.tokenizeItemText(text))

        if tokens.isEmpty():
            return None

        tokens.consume_if(Parser.ARTICLES)
        enchantment = tokens.consume_if(Parser.ENCHANTMENT_NAMES)

        potentialWyvern = tokens.peek()
        potentialScale = tokens.peek_n(1)
        if potentialScale is not None:
            assert potentialWyvern is not None
            potentialEnum = Item.resolve_material(potentialWyvern + "_" + potentialScale)
            if potentialEnum is not None:
                material = potentialEnum.name
                tokens.consume() # wyvern
                tokens.consume() # scale

        if not material: #was not a `wyvern scale` material
            material = tokens.consume_if(Parser.MATERIAL_NAMES)

        if not Item.is_valid_base_item_name(" ".join(tokens.remaining())):
            if material:
                materialThenRemainingTokens = addPrefixToRemainingTokens(material.lower().replace("_", " "), tokens.remaining())
                if not Item.is_valid_base_item_name(' '.join(materialThenRemainingTokens)):
                    return None # unlikely unless testing

                return Item(' '.join(materialThenRemainingTokens))

            if enchantment:
                if material:
                    enchantmentThenRemainingTokens = addPrefixToRemainingTokens(enchantment, materialThenRemainingTokens)
                else:
                    enchantmentThenRemainingTokens = addPrefixToRemainingTokens(enchantment, tokens.remaining())
                if Item.is_valid_base_item_name(' '.join(enchantmentThenRemainingTokens)):
                    return Item(' '.join(enchantmentThenRemainingTokens))

        if tokens.isEmpty():
            return None

        item = Item(text)

        item.Enchantment = Item.resolve_enchantment(enchantment) if enchantment is not None else None
        item.Material = Item.resolve_material(material) if material else None

        item.ParsedBaseItemName = " ".join(tokens.remaining())

        return item

    MOB_DROP_ITEM_PATTERN = re.compile(
rf"""
^
(?:A|An)\s+
(?P<mobName>{MOB_NAME_REGEX_TEXT})

\s+drops\s+

{r"(?P<itemName>.+)"}

\.
$
""", re.VERBOSE | re.IGNORECASE
)

    @staticmethod
    def parseMobDroppedItem(text: str) -> tuple[bool, Item | None]:
        '''Parses text for a dropped item.
- First Tuple Element: `bool` - `True` = text contains a dropped item, `False` = text does not contain a dropped item
- Second Tuple Element: `Item` - the Item object parsed from the text, or `None` if no dropped item is found.'''
        match = Parser.MOB_DROP_ITEM_PATTERN.search(text)

        if not match:
            return False, None

        if match.group("mobName") in Parser.SHAPESHIFTED_WEREWOLF_NAMES:
            return False, None

        item = Parser.parseItem(match.group("itemName"))

        if not item:
            return False, None

        return True, item

    class ConstitutionResisted(StrEnum):
        ConstitutionResistedDisease = "Disease starts to enter your system, but your constitution fights it off!"
        ConstitutionResistedPoison = "Poison starts to enter your system, but your constitution fights it off!"
        ConstitutionResistedBleed = "You start to bleed, but your constitution fights it off!"

    def parseConstitutionResisted(self, text: str) -> tuple[bool, ConstitutionResisted | None]:
        '''Parse text for constitution resisted messages.
- First Tuple Element: `bool` - `True` = text contains a constitution resisted message, `False` = text does not contain a constitution resisted related message.
- Second Tuple Element: `ConstitutionResisted` - the ConstitutionResisted value parsed from the text, or `None` if not constitution resisted related.
'''
        if not ', but your constitution fights it off!' in text:
            return (False, None)

        if self.ConstitutionResisted.ConstitutionResistedBleed.value in text:
            return (True, self.ConstitutionResisted.ConstitutionResistedBleed)

        if self.ConstitutionResisted.ConstitutionResistedDisease.value in text:
            return (True, self.ConstitutionResisted.ConstitutionResistedDisease)

        if self.ConstitutionResisted.ConstitutionResistedPoison.value in text:
            return (True, self.ConstitutionResisted.ConstitutionResistedPoison)

        return (False, None)

    class ParseBytes:
        @staticmethod
        def isLogout(text: bytes) -> bool:
            '''Parse bytes for logout message.'''
            return ConnectionPayloadBytes.Logout.value in text

        @staticmethod
        def isLogin(text: bytes) -> bool:
            '''Parse bytes for login message.'''
            return ConnectionPayloadBytes.Login.value in text

        @staticmethod
        def isBoatDocking(text: bytes) -> bool:
            return text.startswith(BoatNotificationBytes.DOCKED.value)

        @staticmethod
        def isBoatDeparting(text: bytes) -> bool:
            return text.startswith(BoatNotificationBytes.DEPARTED.value)
