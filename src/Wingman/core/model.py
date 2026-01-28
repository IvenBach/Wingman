from Wingman.core.parser import Parser
class Model:
    def __init__(self, parser: Parser):
        self.parser = parser
        self.isAfk: bool | None = False