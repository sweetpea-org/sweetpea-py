from sweetpea import CrossBlock, Factor


color = Factor("color", ["red", "blue"])
text  = Factor("text",  ["red", "blue"])

design   = [color, text]
crossing = [color, text]
block    = CrossBlock(design, crossing, [])

# ASSERT COUNT = 24
