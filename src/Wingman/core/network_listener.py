import threading
import re
from scapy.all import sniff, IP, TCP
from Wingman.core.input_receiver import InputReceiver
from Wingman.core.parser import Parser
from Wingman.core.mobs_in_room import MobsInRoom


class NetworkListener:
    def __init__(self, input_receiver: InputReceiver, controller):
        from Wingman.core.controller import Controller # Avoid circular import issues by importing here
        assert isinstance(controller, Controller)

        self.receiver = input_receiver
        # Update this if your game server IP changes
        self.target_ip = '18.119.153.121'
        self.target_port = 4000
        self.is_running = False

        # Persistent buffer to hold split packet data
        self._buffer = ""

        self.controller = controller

    def packet_callback(self, packet):
        predeterminedChunkMobList = []
        mobsInRoom: MobsInRoom | None = None
        if IP in packet and TCP in packet:
            if packet[IP].src == self.target_ip and packet[TCP].sport == self.target_port:
                if len(packet[TCP].payload) <= 0:
                    return 
                
                try:
                    payload_bytes = bytes(packet[TCP].payload)

                    # Decode and append to buffer immediately
                    chunk = payload_bytes.decode('utf-8', errors='replace')
                    if Parser().ParseMobs().hasAnsiColorCodedMobs(chunk, predeterminedChunkMobList):
                        mobsInRoom = MobsInRoom(predeterminedChunkMobList)

                    isBuffOrShieldRefreshing, whatIsRefreshing_StartText = Parser().parseBuffOrShieldIsRefreshing(chunk)
                    if isBuffOrShieldRefreshing:
                        assert whatIsRefreshing_StartText is not None
                        endText = Parser().getEndBuffOrShieldValueFromStartValue(whatIsRefreshing_StartText)
                        indexBeforeEndText = chunk.find(endText.value)
                        indexAfterStartTextAndNewlineCharacter = chunk.find(whatIsRefreshing_StartText.value) + len(whatIsRefreshing_StartText.value) + 1

                        chunk = chunk[:indexBeforeEndText] + chunk[indexAfterStartTextAndNewlineCharacter:] #Discard between end spell text to start spell text, inclusive of both.

                    self._buffer += self.receiver.remove_ANSI_color_codes(chunk)

                    # Process buffer: extract complete lines only
                    while '\n' in self._buffer:
                        # Split at the first newline
                        line, self._buffer = self._buffer.split('\n', 1)

                        # Clean up carriage returns common in MUDs
                        line = line.replace('\r', '')
                        self.receiver.receive(line)

                    if mobsInRoom is not None:
                        self.receiver.receive(mobsInRoom)
                        mobsInRoom = None

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