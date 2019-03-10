from sweetpea import fully_cross_block
from sweetpea.primitives import Factor


color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

design   = [color, text]
crossing = [color, text]
block    = fully_cross_block(design, crossing, [])

# ASSERT COUNT = 24
