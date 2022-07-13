\* 2*2 *\
Minimize
OBJ: __dummy
Subject To
_C1: Color_0_0 + Color_1_0 = 1
_C10: - Color_0_0 + Crossing_0_0 - Text_0_0 >= -1
_C11: - Color_0_0 + 2 Crossing_0_1 - Text_1_0 <= 0
_C12: - Color_0_0 + Crossing_0_1 - Text_1_0 >= -1
_C13: - Color_1_0 + 2 Crossing_0_2 - Text_0_0 <= 0
_C14: - Color_1_0 + Crossing_0_2 - Text_0_0 >= -1
_C15: - Color_1_0 + 2 Crossing_0_3 - Text_1_0 <= 0
_C16: - Color_1_0 + Crossing_0_3 - Text_1_0 >= -1
_C17: Crossing_0_0 + Crossing_1_0 + Crossing_2_0 + Crossing_3_0 = 1
_C18: - Color_0_1 + 2 Crossing_1_0 - Text_0_1 <= 0
_C19: - Color_0_1 + Crossing_1_0 - Text_0_1 >= -1
_C2: Color_0_1 + Color_1_1 = 1
_C20: - Color_0_1 + 2 Crossing_1_1 - Text_1_1 <= 0
_C21: - Color_0_1 + Crossing_1_1 - Text_1_1 >= -1
_C22: - Color_1_1 + 2 Crossing_1_2 - Text_0_1 <= 0
_C23: - Color_1_1 + Crossing_1_2 - Text_0_1 >= -1
_C24: - Color_1_1 + 2 Crossing_1_3 - Text_1_1 <= 0
_C25: - Color_1_1 + Crossing_1_3 - Text_1_1 >= -1
_C26: Crossing_0_1 + Crossing_1_1 + Crossing_2_1 + Crossing_3_1 = 1
_C27: - Color_0_2 + 2 Crossing_2_0 - Text_0_2 <= 0
_C28: - Color_0_2 + Crossing_2_0 - Text_0_2 >= -1
_C29: - Color_0_2 + 2 Crossing_2_1 - Text_1_2 <= 0
_C3: Color_0_2 + Color_1_2 = 1
_C30: - Color_0_2 + Crossing_2_1 - Text_1_2 >= -1
_C31: - Color_1_2 + 2 Crossing_2_2 - Text_0_2 <= 0
_C32: - Color_1_2 + Crossing_2_2 - Text_0_2 >= -1
_C33: - Color_1_2 + 2 Crossing_2_3 - Text_1_2 <= 0
_C34: - Color_1_2 + Crossing_2_3 - Text_1_2 >= -1
_C35: Crossing_0_2 + Crossing_1_2 + Crossing_2_2 + Crossing_3_2 = 1
_C36: - Color_0_3 + 2 Crossing_3_0 - Text_0_3 <= 0
_C37: - Color_0_3 + Crossing_3_0 - Text_0_3 >= -1
_C38: - Color_0_3 + 2 Crossing_3_1 - Text_1_3 <= 0
_C39: - Color_0_3 + Crossing_3_1 - Text_1_3 >= -1
_C4: Color_0_3 + Color_1_3 = 1
_C40: - Color_1_3 + 2 Crossing_3_2 - Text_0_3 <= 0
_C41: - Color_1_3 + Crossing_3_2 - Text_0_3 >= -1
_C42: - Color_1_3 + 2 Crossing_3_3 - Text_1_3 <= 0
_C43: - Color_1_3 + Crossing_3_3 - Text_1_3 >= -1
_C44: Crossing_0_3 + Crossing_1_3 + Crossing_2_3 + Crossing_3_3 = 1
_C5: Text_0_0 + Text_1_0 = 1
_C6: Text_0_1 + Text_1_1 = 1
_C7: Text_0_2 + Text_1_2 = 1
_C8: Text_0_3 + Text_1_3 = 1
_C9: - Color_0_0 + 2 Crossing_0_0 - Text_0_0 <= 0
Bounds
 __dummy = 0
Binaries
Color_0_0
Color_0_1
Color_0_2
Color_0_3
Color_1_0
Color_1_1
Color_1_2
Color_1_3
Crossing_0_0
Crossing_0_1
Crossing_0_2
Crossing_0_3
Crossing_1_0
Crossing_1_1
Crossing_1_2
Crossing_1_3
Crossing_2_0
Crossing_2_1
Crossing_2_2
Crossing_2_3
Crossing_3_0
Crossing_3_1
Crossing_3_2
Crossing_3_3
Text_0_0
Text_0_1
Text_0_2
Text_0_3
Text_1_0
Text_1_1
Text_1_2
Text_1_3
End
