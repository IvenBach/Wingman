from Wingman.core.ansi_code_stripper import remove_ANSI_color_codes

def test_clean_message_removes_ansi():
    # Log line with ANSI color codes (e.g., Red text for damage)
    dirty_input = "\x1b[31mA greater mummy attacks you!\x1b[0m"
    clean = remove_ANSI_color_codes(dirty_input)
    assert clean == "A greater mummy attacks you!", "ANSI codes were not stripped."

def test_clean_message_handles_partial_ansi():
    # Sometimes codes are malformed or stuck to text
    dirty_input = "You gain \x1b[1m100\x1b[0m experience."
    clean = remove_ANSI_color_codes(dirty_input)
    assert clean == "You gain 100 experience.", "Mid-string ANSI codes failed."