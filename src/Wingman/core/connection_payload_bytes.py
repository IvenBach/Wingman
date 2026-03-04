from enum import Enum

class ConnectionPayloadBytes(Enum):
    Login = b'MSP sounds have been disabled for this session.'
    Logout = b'\xff\xfa\xc9logoff null\xff\xf0'