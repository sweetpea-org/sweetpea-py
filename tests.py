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
    assert fully_cross_size([color, color]) == 4
    assert fully_cross_size([color, color, color]) == 8
    assert fully_cross_size([size, text]) == 3
    assert fully_cross_size([size, color]) == 6
    assert fully_cross_size([text]) == 1

# needs more tests
def test_get_depxProduct():
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red", "blue"])
    conLevel  = DerivedLevel("con", WithinTrial(op.eq, [color, text]))
    assert get_dep_xProduct(conLevel) == [(('color', 'red'), ('text', 'red')),
                                          (('color', 'red'), ('text', 'blue')),
                                          (('color', 'blue'), ('text', 'red')),
                                          (('color', 'blue'), ('text', 'blue'))]

def test_etc():
    assert None == None
