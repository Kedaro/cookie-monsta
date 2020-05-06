
# TODO: do we need to go higher?
WORD_TO_NUM_DICT = {
    "million": 1e6,
    "billion": 1e9,
    "trillion": 1e12,
    "quadrillion": 1e15,
    "quintillion": 1e18,
    "sextillion": 1e21,
    "septillion": 1e24,
    "octillion": 1e27,
    "nonillion": 1e30
}

def cookie_count_text_to_float(cookie_text: str) -> float:
    """
    cookie_text: must only include number of cookies, no other text
    
    """
    segments = cookie_text.split()
    
    if len(segments) == 1:
        str_num = segments[0].replace(",", "")
        return float(str_num)
    else:
        assert (len(segments) == 2)
        # the first section is the number
        str_num = segments[0].replace(",", "")
        num_pre = float(str_num)
        # second section is the multiplier
        multiplier = segments[1].lower()
        assert multiplier in WORD_TO_NUM_DICT

        return float(num_pre * WORD_TO_NUM_DICT[multiplier])



