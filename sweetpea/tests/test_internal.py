from sweetpea.internal import get_all_level_names
from sweetpea.primitives import Factor

def test_get_all_level_names():
    color = Factor("color", ["red", "blue"])
    text  = Factor("text",  ["red", "blue", "green"])

    assert get_all_level_names([color, text]) == [('color', 'red'),
                                                  ('color', 'blue'),
                                                  ('text', 'red'),
                                                  ('text', 'blue'),
                                                  ('text', 'green')]