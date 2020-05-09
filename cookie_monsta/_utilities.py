import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# TODO: do we need to go higher?
WORD_TO_NUM_DICT = {
    "mil": 1e6,
    "bil": 1e9,
    "tri": 1e12,
    "qua": 1e15,
    "qui": 1e18,
    "sex": 1e21,
    "sep": 1e24,
    "oct": 1e27,
    "non": 1e30
}

def cookie_count_text_to_float(cookie_text: str) -> float:
    """
    cookie_text: must only include number of cookies, no other text
    
    """
    try: 
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
            # just use the first 3 letters
            multiplier = multiplier[:3]

            return float(num_pre * WORD_TO_NUM_DICT[multiplier])
    except Exception as e:
        logger.error(f"Failed to parse cookie count: {segments}")
        raise e

@dataclass
class BuildingInfo:
    cost: float
    cps: float

class PurchaseStrategy(Enum):
    MIN_COST_PER_CPS = 1
    WEIGHTED_COST_PER_CPS = 2
    