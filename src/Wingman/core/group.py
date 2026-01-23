from Wingman.core.character import Character
from typing import List, overload

class Group:
    '''
    Character group management class.
    '''
    def __init__(self, members: List[Character] = []) -> None:
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
    
    @property
    def DisplayHealingIcon(self) -> bool:
        for member in self._members:
            if member.Hp.Current == 1:
                return True
        
        return False