# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#          yay, testing! run: `pytest tests.py`
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from FrontEnd import *
import operator as op


 
# done
def test_fullycrosssize():
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red"])
    size  = Factor("size",  ["big", "small", "tiny"])
    assert fullyCrossSize([color, color]) == 4
    assert fullyCrossSize([color, color, color]) == 8
    assert fullyCrossSize([size, text]) == 3
    assert fullyCrossSize([size, color]) == 6
    assert fullyCrossSize([text]) == 1
    
# needs more tests  
def test_get_depxProduct():
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red", "blue"])
    conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
    assert get_dep_xProduct(conLevel) == [('red', 'red'), ('red', 'blue'), ('blue', 'red'), ('blue', 'blue')]
    
def test_etc():
    assert None == None