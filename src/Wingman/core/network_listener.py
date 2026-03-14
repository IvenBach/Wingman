import threading
from scapy.all import sniff, IP, TCP
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.parsing.parser import MobEnteringReasons, Parser
from Wingman.core.mobs_in_room import MobsInRoom
from Wingman.core.ansi_code_stripper import remove_ANSI_color_codes
from Wingman.core.mobs_chasing_you import MobsChasingYou

class NetworkListener:
    def __init__(self, input_receiver: InputReceiver, controller, target_ip, target_port):
        from Wingman.core.controller import Controller # Avoid circular import issues by importing here
        assert isinstance(controller, Controller)

        self.receiver = input_receiver
        # Update this if your game server IP changes
        self.target_ip = target_ip
        self.target_port = target_port
        self.is_running = False

        # Persistent buffer to hold split packet data
        self._buffer = ""

        self.controller = controller

    def packet_callback(self, packet):
        predeterminedChunkMobList = []
        mobsInRoom: MobsInRoom | None = None
        isBeingChased: list[str] | None = None
        if IP in packet and TCP in packet:
            if packet[IP].src == self.target_ip and packet[TCP].sport == self.target_port:
                if len(packet[TCP].payload) <= 0:
                    return

                try:
                    payload_bytes = bytes(packet[TCP].payload)

                    if Parser.ParseBytes().isLogin(payload_bytes):
                        self.controller.view.apply_pause(False)

                    if Parser.ParseBytes().isLogout(payload_bytes):
                        self.controller.view.apply_pause(True)
                        self.controller.disbandGroup()

                    # Decode and append to buffer immediately
                    chunk = payload_bytes.decode('utf-8', errors='replace')

                    inventory = Parser().parseInventory(remove_ANSI_color_codes(chunk))
                    if inventory is not None:
                        self.receiver.receive(inventory)
                        return

                    eg = Parser().parseEquippedGear(remove_ANSI_color_codes(chunk))
                    if eg is not None:
                        self.receiver.receive(eg)
                        return

                    if Parser.ParseMobs().hasAnsiColorCodedMobs(chunk, predeterminedChunkMobList):
                        mobsInRoom = MobsInRoom(predeterminedChunkMobList)

                    mobMovements, movementIndices = Parser.ParseMovement.parseMobMovements(chunk)
                    if mobMovements:
                        isBeingChased = [movementEvent.mobName for movementEvent in mobMovements if movementEvent.movementReason == MobEnteringReasons.CHASES and movementEvent.isChasingYou]

                        movementIndices.reverse()
                        # Work from back to front removing mob movement related text from chunk.
                        # Keep from maintaining a shift index/counter.
                        for startIndex, endIndex in movementIndices:
                            chunk = chunk[:startIndex] + chunk[endIndex:]
                        # Permit remaining chunk to continue, it may have room description text.

                    isAffect, affects, affectIndices = Parser.ParseAffect().parseAffects(chunk)
                    if isAffect:
                        self.receiver.receive(affects)
                        chunk = chunk[:affectIndices[0]] + chunk[affectIndices[1]:]

                    isBuffOrShieldRefreshing, whatIsRefreshing_StartText = Parser().parseBuffOrShieldIsRefreshing(chunk)
                    if isBuffOrShieldRefreshing:
                        assert whatIsRefreshing_StartText is not None
                        endMember = Parser.ParseBuffOrShieldText.mapOfStartingToEndingEnumMembers()[whatIsRefreshing_StartText]

                        indexBeforeEndText = chunk.find(endMember.value)
                        indexAfterStartTextAndNewlineCharacter = chunk.find(whatIsRefreshing_StartText.value) + len(whatIsRefreshing_StartText.value) + 1

                        chunk = chunk[:indexBeforeEndText] + chunk[indexAfterStartTextAndNewlineCharacter:] #Discard between end spell text to start spell text, inclusive of both.

                    isMeditationRelated, meditationState = Parser().parseMeditation(chunk)
                    if not isMeditationRelated is None and meditationState is not None:
                        self.receiver.receive(meditationState)
                        chunk = chunk.replace(meditationState.value, '')

                    self._buffer += remove_ANSI_color_codes(chunk)

                    # Process buffer: extract complete lines only
                    while '\n' in self._buffer:
                        # Split at the first newline
                        line, self._buffer = self._buffer.split('\n', 1)

                        # Clean up carriage returns common in MUDs
                        line = line.replace('\r', '').strip()
                        if line: # Don't send empty lines to the receiver
                            self.receiver.receive(line)

                    if mobsInRoom is not None:
                        self.receiver.receive(mobsInRoom)
                        mobsInRoom = None

                    if isBeingChased:
                        self.receiver.receive(MobsChasingYou(isBeingChased))
                        isBeingChased = None

                except Exception as e:
                    print(f"Error decoding packet: {e}")

    def start(self):
        self.is_running = True
        print(f"Listening for traffic from {self.target_ip}:{self.target_port}...")
        t = threading.Thread(target=self._sniff_thread, daemon=True)
        t.start()

    def _sniff_thread(self):
        # store=0 prevents memory leaks from keeping packet history
        sniff(prn=self.packet_callback, filter="tcp", store=0)
