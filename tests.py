# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#          yay, testing! run: `pytest tests.py`
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from FrontEnd import *


 

def test_fullycrosssize():
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red"])
    size  = Factor("size",  ["big", "small", "tiny"])
    assert fullyCrossSize([color, color]) == 4
    assert fullyCrossSize([color, color, color]) == 8
    assert fullyCrossSize([size, text]) == 3
    assert fullyCrossSize([size, color]) == 6
    assert fullyCrossSize([text]) == 1
    
    
    
def test_etc():
    assert None == None