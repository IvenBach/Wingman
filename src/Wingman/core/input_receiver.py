import re
from collections import deque

class InputReceiver:
    '''Accepts input lines and queues them for processing.'''
    stack_log_file = 'stack_log.txt'  # File to store stack logs

    def __init__(self, on_new_line_callback=None):
        self.last_received = ""
        self._queue: deque[str | None] = deque()
        self.on_new_line_callback = on_new_line_callback  # Optional callback function

        # Clear the log file when the instance is initialized
        with open(self.stack_log_file, 'w') as f:
            f.write('')  # Clear the contents of the file

    @staticmethod
    def remove_ANSI_color_codes(input_line: str) -> str:
        '''
        Cleans the input string by removing ANSI color codes.
        
        :param input_line: line of text including ANSI color codes
        :return: line free of ANSI color codes
        :rtype: str
        '''
        # UPDATED: Now includes \x1b to catch the Escape character too
        ansi_code_pattern = re.compile(r'\x1b\[\d+(?:;\d+)*m')
        return ansi_code_pattern.sub('', input_line)

    def receive(self, input_line: str):
        '''
        Receives an input line, cleans it, and adds it to the processing queue.
        '''
        if not input_line.strip():
            return

        self.last_received = input_line
        cleaned_input = self.remove_ANSI_color_codes(input_line)
        self._add_to_queue(cleaned_input)
        # debugging line as needed print("receiver received " + cleaned_input)

    def _add_to_queue(self, cleaned_input: str):
        self._queue.append(cleaned_input)

    def dequeue(self) -> str | None:
        removed = self._queue.popleft() if self._queue else None
        return removed

    def get_last_received(self) -> str:
        return self.last_received


if __name__ == "__main__":
    input_receiver_instance = InputReceiver()
