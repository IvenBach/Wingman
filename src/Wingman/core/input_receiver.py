import re

class InputReceiver:
    last_received = None
    scrubbed_message = None
    stack = None

    stack_log_file = 'stack_log.txt'  # File to store stack logs

    def __init__(self, on_new_line_callback=None):
        self.last_received = ""
        self.stack = []
        self.on_new_line_callback = on_new_line_callback  # Optional callback function

        # Clear the log file when the instance is initialized
        with open(self.stack_log_file, 'w') as f:
            f.write('')  # Clear the contents of the file

    @staticmethod
    def clean_message(input_line):
        # UPDATED: Now includes \x1b to catch the Escape character too
        ansi_code_pattern = re.compile(r'\x1b\[\d+(?:;\d+)*m')
        return ansi_code_pattern.sub('', input_line)

    def receive(self, input_line):
        if not input_line.strip():
            return

        self.last_received = input_line
        cleaned_input = self.clean_message(input_line)
        self._add_to_stack(cleaned_input)
        # debugging line as needed print("receiver received " + cleaned_input)

    def _add_to_stack(self, cleaned_input):
        self.stack.append(cleaned_input)

    def remove_from_top(self):
        removed = self.stack.pop(0) if self.stack else None
        return removed

    def get_last_received(self):
        return self.last_received


if __name__ == "__main__":
    input_receiver_instance = InputReceiver()
