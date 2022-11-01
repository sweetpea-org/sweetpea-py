\* Example_ILP *\
Maximize
OBJ: __dummy
Subject To
_C1: Color_0_0 + Color_1_0 + Color_2_0 = 1
_C10: Text_0_0 + Text_1_0 + Text_2_0 = 1
_C100: - Color_0_1 - Color_2_2 + _hiddenTransition1_1_2 >= -1
_C101: Color_0_1 + Color_2_2 - 2 _hiddenTransition1_1_2 >= 0
_C102: - Color_0_2 - Color_1_1 + _hiddenTransition1_2_2 >= -1
_C103: Color_0_2 + Color_1_1 - 2 _hiddenTransition1_2_2 >= 0
_C104: - Color_1_1 - Color_2_2 + _hiddenTransition1_3_2 >= -1
_C105: Color_1_1 + Color_2_2 - 2 _hiddenTransition1_3_2 >= 0
_C106: - Color_0_2 - Color_2_1 + _hiddenTransition1_4_2 >= -1
_C107: Color_0_2 + Color_2_1 - 2 _hiddenTransition1_4_2 >= 0
_C108: - Color_1_2 - Color_2_1 + _hiddenTransition1_5_2 >= -1
_C109: Color_1_2 + Color_2_1 - 2 _hiddenTransition1_5_2 >= 0
_C11: Text_0_1 + Text_1_1 + Text_2_1 = 1
_C110: - _hiddenTransition1_0_2 - _hiddenTransition1_1_2
 - _hiddenTransition1_2_2 - _hiddenTransition1_3_2 - _hiddenTransition1_4_2
 - _hiddenTransition1_5_2 + 6 response_transition_1_2 >= 0
_C111: _hiddenTransition1_0_2 + _hiddenTransition1_1_2
 + _hiddenTransition1_2_2 + _hiddenTransition1_3_2 + _hiddenTransition1_4_2
 + _hiddenTransition1_5_2 - response_transition_1_2 >= 0
_C112: - Color_0_2 - Color_1_3 + _hiddenTransition1_0_3 >= -1
_C113: Color_0_2 + Color_1_3 - 2 _hiddenTransition1_0_3 >= 0
_C114: - Color_0_2 - Color_2_3 + _hiddenTransition1_1_3 >= -1
_C115: Color_0_2 + Color_2_3 - 2 _hiddenTransition1_1_3 >= 0
_C116: - Color_0_3 - Color_1_2 + _hiddenTransition1_2_3 >= -1
_C117: Color_0_3 + Color_1_2 - 2 _hiddenTransition1_2_3 >= 0
_C118: - Color_1_2 - Color_2_3 + _hiddenTransition1_3_3 >= -1
_C119: Color_1_2 + Color_2_3 - 2 _hiddenTransition1_3_3 >= 0
_C12: Text_0_2 + Text_1_2 + Text_2_2 = 1
_C120: - Color_0_3 - Color_2_2 + _hiddenTransition1_4_3 >= -1
_C121: Color_0_3 + Color_2_2 - 2 _hiddenTransition1_4_3 >= 0
_C122: - Color_1_3 - Color_2_2 + _hiddenTransition1_5_3 >= -1
_C123: Color_1_3 + Color_2_2 - 2 _hiddenTransition1_5_3 >= 0
_C124: - _hiddenTransition1_0_3 - _hiddenTransition1_1_3
 - _hiddenTransition1_2_3 - _hiddenTransition1_3_3 - _hiddenTransition1_4_3
 - _hiddenTransition1_5_3 + 6 response_transition_1_3 >= 0
_C125: _hiddenTransition1_0_3 + _hiddenTransition1_1_3
 + _hiddenTransition1_2_3 + _hiddenTransition1_3_3 + _hiddenTransition1_4_3
 + _hiddenTransition1_5_3 - response_transition_1_3 >= 0
_C126: - Color_0_3 - Color_1_4 + _hiddenTransition1_0_4 >= -1
_C127: Color_0_3 + Color_1_4 - 2 _hiddenTransition1_0_4 >= 0
_C128: - Color_0_3 - Color_2_4 + _hiddenTransition1_1_4 >= -1
_C129: Color_0_3 + Color_2_4 - 2 _hiddenTransition1_1_4 >= 0
_C13: Text_0_3 + Text_1_3 + Text_2_3 = 1
_C130: - Color_0_4 - Color_1_3 + _hiddenTransition1_2_4 >= -1
_C131: Color_0_4 + Color_1_3 - 2 _hiddenTransition1_2_4 >= 0
_C132: - Color_1_3 - Color_2_4 + _hiddenTransition1_3_4 >= -1
_C133: Color_1_3 + Color_2_4 - 2 _hiddenTransition1_3_4 >= 0
_C134: - Color_0_4 - Color_2_3 + _hiddenTransition1_4_4 >= -1
_C135: Color_0_4 + Color_2_3 - 2 _hiddenTransition1_4_4 >= 0
_C136: - Color_1_4 - Color_2_3 + _hiddenTransition1_5_4 >= -1
_C137: Color_1_4 + Color_2_3 - 2 _hiddenTransition1_5_4 >= 0
_C138: - _hiddenTransition1_0_4 - _hiddenTransition1_1_4
 - _hiddenTransition1_2_4 - _hiddenTransition1_3_4 - _hiddenTransition1_4_4
 - _hiddenTransition1_5_4 + 6 response_transition_1_4 >= 0
_C139: _hiddenTransition1_0_4 + _hiddenTransition1_1_4
 + _hiddenTransition1_2_4 + _hiddenTransition1_3_4 + _hiddenTransition1_4_4
 + _hiddenTransition1_5_4 - response_transition_1_4 >= 0
_C14: Text_0_4 + Text_1_4 + Text_2_4 = 1
_C140: - Color_0_4 - Color_1_5 + _hiddenTransition1_0_5 >= -1
_C141: Color_0_4 + Color_1_5 - 2 _hiddenTransition1_0_5 >= 0
_C142: - Color_0_4 - Color_2_5 + _hiddenTransition1_1_5 >= -1
_C143: Color_0_4 + Color_2_5 - 2 _hiddenTransition1_1_5 >= 0
_C144: - Color_0_5 - Color_1_4 + _hiddenTransition1_2_5 >= -1
_C145: Color_0_5 + Color_1_4 - 2 _hiddenTransition1_2_5 >= 0
_C146: - Color_1_4 - Color_2_5 + _hiddenTransition1_3_5 >= -1
_C147: Color_1_4 + Color_2_5 - 2 _hiddenTransition1_3_5 >= 0
_C148: - Color_0_5 - Color_2_4 + _hiddenTransition1_4_5 >= -1
_C149: Color_0_5 + Color_2_4 - 2 _hiddenTransition1_4_5 >= 0
_C15: Text_0_5 + Text_1_5 + Text_2_5 = 1
_C150: - Color_1_5 - Color_2_4 + _hiddenTransition1_5_5 >= -1
_C151: Color_1_5 + Color_2_4 - 2 _hiddenTransition1_5_5 >= 0
_C152: - _hiddenTransition1_0_5 - _hiddenTransition1_1_5
 - _hiddenTransition1_2_5 - _hiddenTransition1_3_5 - _hiddenTransition1_4_5
 - _hiddenTransition1_5_5 + 6 response_transition_1_5 >= 0
_C153: _hiddenTransition1_0_5 + _hiddenTransition1_1_5
 + _hiddenTransition1_2_5 + _hiddenTransition1_3_5 + _hiddenTransition1_4_5
 + _hiddenTransition1_5_5 - response_transition_1_5 >= 0
_C154: - Color_0_5 - Color_1_6 + _hiddenTransition1_0_6 >= -1
_C155: Color_0_5 + Color_1_6 - 2 _hiddenTransition1_0_6 >= 0
_C156: - Color_0_5 - Color_2_6 + _hiddenTransition1_1_6 >= -1
_C157: Color_0_5 + Color_2_6 - 2 _hiddenTransition1_1_6 >= 0
_C158: - Color_0_6 - Color_1_5 + _hiddenTransition1_2_6 >= -1
_C159: Color_0_6 + Color_1_5 - 2 _hiddenTransition1_2_6 >= 0
_C16: Text_0_6 + Text_1_6 + Text_2_6 = 1
_C160: - Color_1_5 - Color_2_6 + _hiddenTransition1_3_6 >= -1
_C161: Color_1_5 + Color_2_6 - 2 _hiddenTransition1_3_6 >= 0
_C162: - Color_0_6 - Color_2_5 + _hiddenTransition1_4_6 >= -1
_C163: Color_0_6 + Color_2_5 - 2 _hiddenTransition1_4_6 >= 0
_C164: - Color_1_6 - Color_2_5 + _hiddenTransition1_5_6 >= -1
_C165: Color_1_6 + Color_2_5 - 2 _hiddenTransition1_5_6 >= 0
_C166: - _hiddenTransition1_0_6 - _hiddenTransition1_1_6
 - _hiddenTransition1_2_6 - _hiddenTransition1_3_6 - _hiddenTransition1_4_6
 - _hiddenTransition1_5_6 + 6 response_transition_1_6 >= 0
_C167: _hiddenTransition1_0_6 + _hiddenTransition1_1_6
 + _hiddenTransition1_2_6 + _hiddenTransition1_3_6 + _hiddenTransition1_4_6
 + _hiddenTransition1_5_6 - response_transition_1_6 >= 0
_C168: - Color_0_6 - Color_1_7 + _hiddenTransition1_0_7 >= -1
_C169: Color_0_6 + Color_1_7 - 2 _hiddenTransition1_0_7 >= 0
_C17: Text_0_7 + Text_1_7 + Text_2_7 = 1
_C170: - Color_0_6 - Color_2_7 + _hiddenTransition1_1_7 >= -1
_C171: Color_0_6 + Color_2_7 - 2 _hiddenTransition1_1_7 >= 0
_C172: - Color_0_7 - Color_1_6 + _hiddenTransition1_2_7 >= -1
_C173: Color_0_7 + Color_1_6 - 2 _hiddenTransition1_2_7 >= 0
_C174: - Color_1_6 - Color_2_7 + _hiddenTransition1_3_7 >= -1
_C175: Color_1_6 + Color_2_7 - 2 _hiddenTransition1_3_7 >= 0
_C176: - Color_0_7 - Color_2_6 + _hiddenTransition1_4_7 >= -1
_C177: Color_0_7 + Color_2_6 - 2 _hiddenTransition1_4_7 >= 0
_C178: - Color_1_7 - Color_2_6 + _hiddenTransition1_5_7 >= -1
_C179: Color_1_7 + Color_2_6 - 2 _hiddenTransition1_5_7 >= 0
_C18: Text_0_8 + Text_1_8 + Text_2_8 = 1
_C180: - _hiddenTransition1_0_7 - _hiddenTransition1_1_7
 - _hiddenTransition1_2_7 - _hiddenTransition1_3_7 - _hiddenTransition1_4_7
 - _hiddenTransition1_5_7 + 6 response_transition_1_7 >= 0
_C181: _hiddenTransition1_0_7 + _hiddenTransition1_1_7
 + _hiddenTransition1_2_7 + _hiddenTransition1_3_7 + _hiddenTransition1_4_7
 + _hiddenTransition1_5_7 - response_transition_1_7 >= 0
_C182: - Color_0_7 - Color_1_8 + _hiddenTransition1_0_8 >= -1
_C183: Color_0_7 + Color_1_8 - 2 _hiddenTransition1_0_8 >= 0
_C184: - Color_0_7 - Color_2_8 + _hiddenTransition1_1_8 >= -1
_C185: Color_0_7 + Color_2_8 - 2 _hiddenTransition1_1_8 >= 0
_C186: - Color_0_8 - Color_1_7 + _hiddenTransition1_2_8 >= -1
_C187: Color_0_8 + Color_1_7 - 2 _hiddenTransition1_2_8 >= 0
_C188: - Color_1_7 - Color_2_8 + _hiddenTransition1_3_8 >= -1
_C189: Color_1_7 + Color_2_8 - 2 _hiddenTransition1_3_8 >= 0
_C19: - Color_0_0 - Color_0_1 + _hiddenTransition0_0_1 >= -1
_C190: - Color_0_8 - Color_2_7 + _hiddenTransition1_4_8 >= -1
_C191: Color_0_8 + Color_2_7 - 2 _hiddenTransition1_4_8 >= 0
_C192: - Color_1_8 - Color_2_7 + _hiddenTransition1_5_8 >= -1
_C193: Color_1_8 + Color_2_7 - 2 _hiddenTransition1_5_8 >= 0
_C194: - _hiddenTransition1_0_8 - _hiddenTransition1_1_8
 - _hiddenTransition1_2_8 - _hiddenTransition1_3_8 - _hiddenTransition1_4_8
 - _hiddenTransition1_5_8 + 6 response_transition_1_8 >= 0
_C195: _hiddenTransition1_0_8 + _hiddenTransition1_1_8
 + _hiddenTransition1_2_8 + _hiddenTransition1_3_8 + _hiddenTransition1_4_8
 + _hiddenTransition1_5_8 - response_transition_1_8 >= 0
_C196: response_transition_1_0 = 0
_C197: response_transition_0_1 + response_transition_1_1 = 1
_C198: response_transition_0_2 + response_transition_1_2 = 1
_C199: response_transition_0_3 + response_transition_1_3 = 1
_C2: Color_0_1 + Color_1_1 + Color_2_1 = 1
_C20: Color_0_0 + Color_0_1 - 2 _hiddenTransition0_0_1 >= 0
_C200: response_transition_0_4 + response_transition_1_4 = 1
_C201: response_transition_0_5 + response_transition_1_5 = 1
_C202: response_transition_0_6 + response_transition_1_6 = 1
_C203: response_transition_0_7 + response_transition_1_7 = 1
_C204: response_transition_0_8 + response_transition_1_8 = 1
_C205: - Color_0_0 + Crossing_0_0 - Text_0_0 - response_transition_0_0 >= -2
_C206: Color_0_0 - 3 Crossing_0_0 + Text_0_0 + response_transition_0_0 >= 0
_C207: - Color_0_0 + Crossing_0_1 - Text_0_0 - response_transition_1_0 >= -2
_C208: Color_0_0 - 3 Crossing_0_1 + Text_0_0 + response_transition_1_0 >= 0
_C209: - Color_0_0 + Crossing_0_2 - Text_1_0 - response_transition_0_0 >= -2
_C21: - Color_1_0 - Color_1_1 + _hiddenTransition0_1_1 >= -1
_C210: Color_0_0 - 3 Crossing_0_2 + Text_1_0 + response_transition_0_0 >= 0
_C211: - Color_0_0 + Crossing_0_3 - Text_1_0 - response_transition_1_0 >= -2
_C212: Color_0_0 - 3 Crossing_0_3 + Text_1_0 + response_transition_1_0 >= 0
_C213: - Color_0_0 + Crossing_0_4 - Text_2_0 - response_transition_0_0 >= -2
_C214: Color_0_0 - 3 Crossing_0_4 + Text_2_0 + response_transition_0_0 >= 0
_C215: - Color_0_0 + Crossing_0_5 - Text_2_0 - response_transition_1_0 >= -2
_C216: Color_0_0 - 3 Crossing_0_5 + Text_2_0 + response_transition_1_0 >= 0
_C217: - Color_1_0 + Crossing_0_6 - Text_0_0 - response_transition_0_0 >= -2
_C218: Color_1_0 - 3 Crossing_0_6 + Text_0_0 + response_transition_0_0 >= 0
_C219: - Color_1_0 + Crossing_0_7 - Text_0_0 - response_transition_1_0 >= -2
_C22: Color_1_0 + Color_1_1 - 2 _hiddenTransition0_1_1 >= 0
_C220: Color_1_0 - 3 Crossing_0_7 + Text_0_0 + response_transition_1_0 >= 0
_C221: - Color_1_0 + Crossing_0_8 - Text_1_0 - response_transition_0_0 >= -2
_C222: Color_1_0 - 3 Crossing_0_8 + Text_1_0 + response_transition_0_0 >= 0
_C223: Crossing_0_0 + Crossing_1_0 + Crossing_2_0 + Crossing_3_0
 + Crossing_4_0 + Crossing_5_0 + Crossing_6_0 + Crossing_7_0 + Crossing_8_0
 = 1
_C224: - Color_0_1 + Crossing_1_0 - Text_0_1 - response_transition_0_1 >= -2
_C225: Color_0_1 - 3 Crossing_1_0 + Text_0_1 + response_transition_0_1 >= 0
_C226: - Color_0_1 + Crossing_1_1 - Text_0_1 - response_transition_1_1 >= -2
_C227: Color_0_1 - 3 Crossing_1_1 + Text_0_1 + response_transition_1_1 >= 0
_C228: - Color_0_1 + Crossing_1_2 - Text_1_1 - response_transition_0_1 >= -2
_C229: Color_0_1 - 3 Crossing_1_2 + Text_1_1 + response_transition_0_1 >= 0
_C23: - Color_2_0 - Color_2_1 + _hiddenTransition0_2_1 >= -1
_C230: - Color_0_1 + Crossing_1_3 - Text_1_1 - response_transition_1_1 >= -2
_C231: Color_0_1 - 3 Crossing_1_3 + Text_1_1 + response_transition_1_1 >= 0
_C232: - Color_0_1 + Crossing_1_4 - Text_2_1 - response_transition_0_1 >= -2
_C233: Color_0_1 - 3 Crossing_1_4 + Text_2_1 + response_transition_0_1 >= 0
_C234: - Color_0_1 + Crossing_1_5 - Text_2_1 - response_transition_1_1 >= -2
_C235: Color_0_1 - 3 Crossing_1_5 + Text_2_1 + response_transition_1_1 >= 0
_C236: - Color_1_1 + Crossing_1_6 - Text_0_1 - response_transition_0_1 >= -2
_C237: Color_1_1 - 3 Crossing_1_6 + Text_0_1 + response_transition_0_1 >= 0
_C238: - Color_1_1 + Crossing_1_7 - Text_0_1 - response_transition_1_1 >= -2
_C239: Color_1_1 - 3 Crossing_1_7 + Text_0_1 + response_transition_1_1 >= 0
_C24: Color_2_0 + Color_2_1 - 2 _hiddenTransition0_2_1 >= 0
_C240: - Color_1_1 + Crossing_1_8 - Text_1_1 - response_transition_0_1 >= -2
_C241: Color_1_1 - 3 Crossing_1_8 + Text_1_1 + response_transition_0_1 >= 0
_C242: Crossing_0_1 + Crossing_1_1 + Crossing_2_1 + Crossing_3_1
 + Crossing_4_1 + Crossing_5_1 + Crossing_6_1 + Crossing_7_1 + Crossing_8_1
 = 1
_C243: - Color_0_2 + Crossing_2_0 - Text_0_2 - response_transition_0_2 >= -2
_C244: Color_0_2 - 3 Crossing_2_0 + Text_0_2 + response_transition_0_2 >= 0
_C245: - Color_0_2 + Crossing_2_1 - Text_0_2 - response_transition_1_2 >= -2
_C246: Color_0_2 - 3 Crossing_2_1 + Text_0_2 + response_transition_1_2 >= 0
_C247: - Color_0_2 + Crossing_2_2 - Text_1_2 - response_transition_0_2 >= -2
_C248: Color_0_2 - 3 Crossing_2_2 + Text_1_2 + response_transition_0_2 >= 0
_C249: - Color_0_2 + Crossing_2_3 - Text_1_2 - response_transition_1_2 >= -2
_C25: - _hiddenTransition0_0_1 - _hiddenTransition0_1_1
 - _hiddenTransition0_2_1 + 3 response_transition_0_1 >= 0
_C250: Color_0_2 - 3 Crossing_2_3 + Text_1_2 + response_transition_1_2 >= 0
_C251: - Color_0_2 + Crossing_2_4 - Text_2_2 - response_transition_0_2 >= -2
_C252: Color_0_2 - 3 Crossing_2_4 + Text_2_2 + response_transition_0_2 >= 0
_C253: - Color_0_2 + Crossing_2_5 - Text_2_2 - response_transition_1_2 >= -2
_C254: Color_0_2 - 3 Crossing_2_5 + Text_2_2 + response_transition_1_2 >= 0
_C255: - Color_1_2 + Crossing_2_6 - Text_0_2 - response_transition_0_2 >= -2
_C256: Color_1_2 - 3 Crossing_2_6 + Text_0_2 + response_transition_0_2 >= 0
_C257: - Color_1_2 + Crossing_2_7 - Text_0_2 - response_transition_1_2 >= -2
_C258: Color_1_2 - 3 Crossing_2_7 + Text_0_2 + response_transition_1_2 >= 0
_C259: - Color_1_2 + Crossing_2_8 - Text_1_2 - response_transition_0_2 >= -2
_C26: _hiddenTransition0_0_1 + _hiddenTransition0_1_1 + _hiddenTransition0_2_1
 - response_transition_0_1 >= 0
_C260: Color_1_2 - 3 Crossing_2_8 + Text_1_2 + response_transition_0_2 >= 0
_C261: Crossing_0_2 + Crossing_1_2 + Crossing_2_2 + Crossing_3_2
 + Crossing_4_2 + Crossing_5_2 + Crossing_6_2 + Crossing_7_2 + Crossing_8_2
 = 1
_C262: - Color_0_3 + Crossing_3_0 - Text_0_3 - response_transition_0_3 >= -2
_C263: Color_0_3 - 3 Crossing_3_0 + Text_0_3 + response_transition_0_3 >= 0
_C264: - Color_0_3 + Crossing_3_1 - Text_0_3 - response_transition_1_3 >= -2
_C265: Color_0_3 - 3 Crossing_3_1 + Text_0_3 + response_transition_1_3 >= 0
_C266: - Color_0_3 + Crossing_3_2 - Text_1_3 - response_transition_0_3 >= -2
_C267: Color_0_3 - 3 Crossing_3_2 + Text_1_3 + response_transition_0_3 >= 0
_C268: - Color_0_3 + Crossing_3_3 - Text_1_3 - response_transition_1_3 >= -2
_C269: Color_0_3 - 3 Crossing_3_3 + Text_1_3 + response_transition_1_3 >= 0
_C27: - Color_0_1 - Color_0_2 + _hiddenTransition0_0_2 >= -1
_C270: - Color_0_3 + Crossing_3_4 - Text_2_3 - response_transition_0_3 >= -2
_C271: Color_0_3 - 3 Crossing_3_4 + Text_2_3 + response_transition_0_3 >= 0
_C272: - Color_0_3 + Crossing_3_5 - Text_2_3 - response_transition_1_3 >= -2
_C273: Color_0_3 - 3 Crossing_3_5 + Text_2_3 + response_transition_1_3 >= 0
_C274: - Color_1_3 + Crossing_3_6 - Text_0_3 - response_transition_0_3 >= -2
_C275: Color_1_3 - 3 Crossing_3_6 + Text_0_3 + response_transition_0_3 >= 0
_C276: - Color_1_3 + Crossing_3_7 - Text_0_3 - response_transition_1_3 >= -2
_C277: Color_1_3 - 3 Crossing_3_7 + Text_0_3 + response_transition_1_3 >= 0
_C278: - Color_1_3 + Crossing_3_8 - Text_1_3 - response_transition_0_3 >= -2
_C279: Color_1_3 - 3 Crossing_3_8 + Text_1_3 + response_transition_0_3 >= 0
_C28: Color_0_1 + Color_0_2 - 2 _hiddenTransition0_0_2 >= 0
_C280: Crossing_0_3 + Crossing_1_3 + Crossing_2_3 + Crossing_3_3
 + Crossing_4_3 + Crossing_5_3 + Crossing_6_3 + Crossing_7_3 + Crossing_8_3
 = 1
_C281: - Color_0_4 + Crossing_4_0 - Text_0_4 - response_transition_0_4 >= -2
_C282: Color_0_4 - 3 Crossing_4_0 + Text_0_4 + response_transition_0_4 >= 0
_C283: - Color_0_4 + Crossing_4_1 - Text_0_4 - response_transition_1_4 >= -2
_C284: Color_0_4 - 3 Crossing_4_1 + Text_0_4 + response_transition_1_4 >= 0
_C285: - Color_0_4 + Crossing_4_2 - Text_1_4 - response_transition_0_4 >= -2
_C286: Color_0_4 - 3 Crossing_4_2 + Text_1_4 + response_transition_0_4 >= 0
_C287: - Color_0_4 + Crossing_4_3 - Text_1_4 - response_transition_1_4 >= -2
_C288: Color_0_4 - 3 Crossing_4_3 + Text_1_4 + response_transition_1_4 >= 0
_C289: - Color_0_4 + Crossing_4_4 - Text_2_4 - response_transition_0_4 >= -2
_C29: - Color_1_1 - Color_1_2 + _hiddenTransition0_1_2 >= -1
_C290: Color_0_4 - 3 Crossing_4_4 + Text_2_4 + response_transition_0_4 >= 0
_C291: - Color_0_4 + Crossing_4_5 - Text_2_4 - response_transition_1_4 >= -2
_C292: Color_0_4 - 3 Crossing_4_5 + Text_2_4 + response_transition_1_4 >= 0
_C293: - Color_1_4 + Crossing_4_6 - Text_0_4 - response_transition_0_4 >= -2
_C294: Color_1_4 - 3 Crossing_4_6 + Text_0_4 + response_transition_0_4 >= 0
_C295: - Color_1_4 + Crossing_4_7 - Text_0_4 - response_transition_1_4 >= -2
_C296: Color_1_4 - 3 Crossing_4_7 + Text_0_4 + response_transition_1_4 >= 0
_C297: - Color_1_4 + Crossing_4_8 - Text_1_4 - response_transition_0_4 >= -2
_C298: Color_1_4 - 3 Crossing_4_8 + Text_1_4 + response_transition_0_4 >= 0
_C299: Crossing_0_4 + Crossing_1_4 + Crossing_2_4 + Crossing_3_4
 + Crossing_4_4 + Crossing_5_4 + Crossing_6_4 + Crossing_7_4 + Crossing_8_4
 = 1
_C3: Color_0_2 + Color_1_2 + Color_2_2 = 1
_C30: Color_1_1 + Color_1_2 - 2 _hiddenTransition0_1_2 >= 0
_C300: - Color_0_5 + Crossing_5_0 - Text_0_5 - response_transition_0_5 >= -2
_C301: Color_0_5 - 3 Crossing_5_0 + Text_0_5 + response_transition_0_5 >= 0
_C302: - Color_0_5 + Crossing_5_1 - Text_0_5 - response_transition_1_5 >= -2
_C303: Color_0_5 - 3 Crossing_5_1 + Text_0_5 + response_transition_1_5 >= 0
_C304: - Color_0_5 + Crossing_5_2 - Text_1_5 - response_transition_0_5 >= -2
_C305: Color_0_5 - 3 Crossing_5_2 + Text_1_5 + response_transition_0_5 >= 0
_C306: - Color_0_5 + Crossing_5_3 - Text_1_5 - response_transition_1_5 >= -2
_C307: Color_0_5 - 3 Crossing_5_3 + Text_1_5 + response_transition_1_5 >= 0
_C308: - Color_0_5 + Crossing_5_4 - Text_2_5 - response_transition_0_5 >= -2
_C309: Color_0_5 - 3 Crossing_5_4 + Text_2_5 + response_transition_0_5 >= 0
_C31: - Color_2_1 - Color_2_2 + _hiddenTransition0_2_2 >= -1
_C310: - Color_0_5 + Crossing_5_5 - Text_2_5 - response_transition_1_5 >= -2
_C311: Color_0_5 - 3 Crossing_5_5 + Text_2_5 + response_transition_1_5 >= 0
_C312: - Color_1_5 + Crossing_5_6 - Text_0_5 - response_transition_0_5 >= -2
_C313: Color_1_5 - 3 Crossing_5_6 + Text_0_5 + response_transition_0_5 >= 0
_C314: - Color_1_5 + Crossing_5_7 - Text_0_5 - response_transition_1_5 >= -2
_C315: Color_1_5 - 3 Crossing_5_7 + Text_0_5 + response_transition_1_5 >= 0
_C316: - Color_1_5 + Crossing_5_8 - Text_1_5 - response_transition_0_5 >= -2
_C317: Color_1_5 - 3 Crossing_5_8 + Text_1_5 + response_transition_0_5 >= 0
_C318: Crossing_0_5 + Crossing_1_5 + Crossing_2_5 + Crossing_3_5
 + Crossing_4_5 + Crossing_5_5 + Crossing_6_5 + Crossing_7_5 + Crossing_8_5
 = 1
_C319: - Color_0_6 + Crossing_6_0 - Text_0_6 - response_transition_0_6 >= -2
_C32: Color_2_1 + Color_2_2 - 2 _hiddenTransition0_2_2 >= 0
_C320: Color_0_6 - 3 Crossing_6_0 + Text_0_6 + response_transition_0_6 >= 0
_C321: - Color_0_6 + Crossing_6_1 - Text_0_6 - response_transition_1_6 >= -2
_C322: Color_0_6 - 3 Crossing_6_1 + Text_0_6 + response_transition_1_6 >= 0
_C323: - Color_0_6 + Crossing_6_2 - Text_1_6 - response_transition_0_6 >= -2
_C324: Color_0_6 - 3 Crossing_6_2 + Text_1_6 + response_transition_0_6 >= 0
_C325: - Color_0_6 + Crossing_6_3 - Text_1_6 - response_transition_1_6 >= -2
_C326: Color_0_6 - 3 Crossing_6_3 + Text_1_6 + response_transition_1_6 >= 0
_C327: - Color_0_6 + Crossing_6_4 - Text_2_6 - response_transition_0_6 >= -2
_C328: Color_0_6 - 3 Crossing_6_4 + Text_2_6 + response_transition_0_6 >= 0
_C329: - Color_0_6 + Crossing_6_5 - Text_2_6 - response_transition_1_6 >= -2
_C33: - _hiddenTransition0_0_2 - _hiddenTransition0_1_2
 - _hiddenTransition0_2_2 + 3 response_transition_0_2 >= 0
_C330: Color_0_6 - 3 Crossing_6_5 + Text_2_6 + response_transition_1_6 >= 0
_C331: - Color_1_6 + Crossing_6_6 - Text_0_6 - response_transition_0_6 >= -2
_C332: Color_1_6 - 3 Crossing_6_6 + Text_0_6 + response_transition_0_6 >= 0
_C333: - Color_1_6 + Crossing_6_7 - Text_0_6 - response_transition_1_6 >= -2
_C334: Color_1_6 - 3 Crossing_6_7 + Text_0_6 + response_transition_1_6 >= 0
_C335: - Color_1_6 + Crossing_6_8 - Text_1_6 - response_transition_0_6 >= -2
_C336: Color_1_6 - 3 Crossing_6_8 + Text_1_6 + response_transition_0_6 >= 0
_C337: Crossing_0_6 + Crossing_1_6 + Crossing_2_6 + Crossing_3_6
 + Crossing_4_6 + Crossing_5_6 + Crossing_6_6 + Crossing_7_6 + Crossing_8_6
 = 1
_C338: - Color_0_7 + Crossing_7_0 - Text_0_7 - response_transition_0_7 >= -2
_C339: Color_0_7 - 3 Crossing_7_0 + Text_0_7 + response_transition_0_7 >= 0
_C34: _hiddenTransition0_0_2 + _hiddenTransition0_1_2 + _hiddenTransition0_2_2
 - response_transition_0_2 >= 0
_C340: - Color_0_7 + Crossing_7_1 - Text_0_7 - response_transition_1_7 >= -2
_C341: Color_0_7 - 3 Crossing_7_1 + Text_0_7 + response_transition_1_7 >= 0
_C342: - Color_0_7 + Crossing_7_2 - Text_1_7 - response_transition_0_7 >= -2
_C343: Color_0_7 - 3 Crossing_7_2 + Text_1_7 + response_transition_0_7 >= 0
_C344: - Color_0_7 + Crossing_7_3 - Text_1_7 - response_transition_1_7 >= -2
_C345: Color_0_7 - 3 Crossing_7_3 + Text_1_7 + response_transition_1_7 >= 0
_C346: - Color_0_7 + Crossing_7_4 - Text_2_7 - response_transition_0_7 >= -2
_C347: Color_0_7 - 3 Crossing_7_4 + Text_2_7 + response_transition_0_7 >= 0
_C348: - Color_0_7 + Crossing_7_5 - Text_2_7 - response_transition_1_7 >= -2
_C349: Color_0_7 - 3 Crossing_7_5 + Text_2_7 + response_transition_1_7 >= 0
_C35: - Color_0_2 - Color_0_3 + _hiddenTransition0_0_3 >= -1
_C350: - Color_1_7 + Crossing_7_6 - Text_0_7 - response_transition_0_7 >= -2
_C351: Color_1_7 - 3 Crossing_7_6 + Text_0_7 + response_transition_0_7 >= 0
_C352: - Color_1_7 + Crossing_7_7 - Text_0_7 - response_transition_1_7 >= -2
_C353: Color_1_7 - 3 Crossing_7_7 + Text_0_7 + response_transition_1_7 >= 0
_C354: - Color_1_7 + Crossing_7_8 - Text_1_7 - response_transition_0_7 >= -2
_C355: Color_1_7 - 3 Crossing_7_8 + Text_1_7 + response_transition_0_7 >= 0
_C356: Crossing_0_7 + Crossing_1_7 + Crossing_2_7 + Crossing_3_7
 + Crossing_4_7 + Crossing_5_7 + Crossing_6_7 + Crossing_7_7 + Crossing_8_7
 = 1
_C357: - Color_0_8 + Crossing_8_0 - Text_0_8 - response_transition_0_8 >= -2
_C358: Color_0_8 - 3 Crossing_8_0 + Text_0_8 + response_transition_0_8 >= 0
_C359: - Color_0_8 + Crossing_8_1 - Text_0_8 - response_transition_1_8 >= -2
_C36: Color_0_2 + Color_0_3 - 2 _hiddenTransition0_0_3 >= 0
_C360: Color_0_8 - 3 Crossing_8_1 + Text_0_8 + response_transition_1_8 >= 0
_C361: - Color_0_8 + Crossing_8_2 - Text_1_8 - response_transition_0_8 >= -2
_C362: Color_0_8 - 3 Crossing_8_2 + Text_1_8 + response_transition_0_8 >= 0
_C363: - Color_0_8 + Crossing_8_3 - Text_1_8 - response_transition_1_8 >= -2
_C364: Color_0_8 - 3 Crossing_8_3 + Text_1_8 + response_transition_1_8 >= 0
_C365: - Color_0_8 + Crossing_8_4 - Text_2_8 - response_transition_0_8 >= -2
_C366: Color_0_8 - 3 Crossing_8_4 + Text_2_8 + response_transition_0_8 >= 0
_C367: - Color_0_8 + Crossing_8_5 - Text_2_8 - response_transition_1_8 >= -2
_C368: Color_0_8 - 3 Crossing_8_5 + Text_2_8 + response_transition_1_8 >= 0
_C369: - Color_1_8 + Crossing_8_6 - Text_0_8 - response_transition_0_8 >= -2
_C37: - Color_1_2 - Color_1_3 + _hiddenTransition0_1_3 >= -1
_C370: Color_1_8 - 3 Crossing_8_6 + Text_0_8 + response_transition_0_8 >= 0
_C371: - Color_1_8 + Crossing_8_7 - Text_0_8 - response_transition_1_8 >= -2
_C372: Color_1_8 - 3 Crossing_8_7 + Text_0_8 + response_transition_1_8 >= 0
_C373: - Color_1_8 + Crossing_8_8 - Text_1_8 - response_transition_0_8 >= -2
_C374: Color_1_8 - 3 Crossing_8_8 + Text_1_8 + response_transition_0_8 >= 0
_C375: Crossing_0_8 + Crossing_1_8 + Crossing_2_8 + Crossing_3_8
 + Crossing_4_8 + Crossing_5_8 + Crossing_6_8 + Crossing_7_8 + Crossing_8_8
 = 1
_C38: Color_1_2 + Color_1_3 - 2 _hiddenTransition0_1_3 >= 0
_C39: - Color_2_2 - Color_2_3 + _hiddenTransition0_2_3 >= -1
_C4: Color_0_3 + Color_1_3 + Color_2_3 = 1
_C40: Color_2_2 + Color_2_3 - 2 _hiddenTransition0_2_3 >= 0
_C41: - _hiddenTransition0_0_3 - _hiddenTransition0_1_3
 - _hiddenTransition0_2_3 + 3 response_transition_0_3 >= 0
_C42: _hiddenTransition0_0_3 + _hiddenTransition0_1_3 + _hiddenTransition0_2_3
 - response_transition_0_3 >= 0
_C43: - Color_0_3 - Color_0_4 + _hiddenTransition0_0_4 >= -1
_C44: Color_0_3 + Color_0_4 - 2 _hiddenTransition0_0_4 >= 0
_C45: - Color_1_3 - Color_1_4 + _hiddenTransition0_1_4 >= -1
_C46: Color_1_3 + Color_1_4 - 2 _hiddenTransition0_1_4 >= 0
_C47: - Color_2_3 - Color_2_4 + _hiddenTransition0_2_4 >= -1
_C48: Color_2_3 + Color_2_4 - 2 _hiddenTransition0_2_4 >= 0
_C49: - _hiddenTransition0_0_4 - _hiddenTransition0_1_4
 - _hiddenTransition0_2_4 + 3 response_transition_0_4 >= 0
_C5: Color_0_4 + Color_1_4 + Color_2_4 = 1
_C50: _hiddenTransition0_0_4 + _hiddenTransition0_1_4 + _hiddenTransition0_2_4
 - response_transition_0_4 >= 0
_C51: - Color_0_4 - Color_0_5 + _hiddenTransition0_0_5 >= -1
_C52: Color_0_4 + Color_0_5 - 2 _hiddenTransition0_0_5 >= 0
_C53: - Color_1_4 - Color_1_5 + _hiddenTransition0_1_5 >= -1
_C54: Color_1_4 + Color_1_5 - 2 _hiddenTransition0_1_5 >= 0
_C55: - Color_2_4 - Color_2_5 + _hiddenTransition0_2_5 >= -1
_C56: Color_2_4 + Color_2_5 - 2 _hiddenTransition0_2_5 >= 0
_C57: - _hiddenTransition0_0_5 - _hiddenTransition0_1_5
 - _hiddenTransition0_2_5 + 3 response_transition_0_5 >= 0
_C58: _hiddenTransition0_0_5 + _hiddenTransition0_1_5 + _hiddenTransition0_2_5
 - response_transition_0_5 >= 0
_C59: - Color_0_5 - Color_0_6 + _hiddenTransition0_0_6 >= -1
_C6: Color_0_5 + Color_1_5 + Color_2_5 = 1
_C60: Color_0_5 + Color_0_6 - 2 _hiddenTransition0_0_6 >= 0
_C61: - Color_1_5 - Color_1_6 + _hiddenTransition0_1_6 >= -1
_C62: Color_1_5 + Color_1_6 - 2 _hiddenTransition0_1_6 >= 0
_C63: - Color_2_5 - Color_2_6 + _hiddenTransition0_2_6 >= -1
_C64: Color_2_5 + Color_2_6 - 2 _hiddenTransition0_2_6 >= 0
_C65: - _hiddenTransition0_0_6 - _hiddenTransition0_1_6
 - _hiddenTransition0_2_6 + 3 response_transition_0_6 >= 0
_C66: _hiddenTransition0_0_6 + _hiddenTransition0_1_6 + _hiddenTransition0_2_6
 - response_transition_0_6 >= 0
_C67: - Color_0_6 - Color_0_7 + _hiddenTransition0_0_7 >= -1
_C68: Color_0_6 + Color_0_7 - 2 _hiddenTransition0_0_7 >= 0
_C69: - Color_1_6 - Color_1_7 + _hiddenTransition0_1_7 >= -1
_C7: Color_0_6 + Color_1_6 + Color_2_6 = 1
_C70: Color_1_6 + Color_1_7 - 2 _hiddenTransition0_1_7 >= 0
_C71: - Color_2_6 - Color_2_7 + _hiddenTransition0_2_7 >= -1
_C72: Color_2_6 + Color_2_7 - 2 _hiddenTransition0_2_7 >= 0
_C73: - _hiddenTransition0_0_7 - _hiddenTransition0_1_7
 - _hiddenTransition0_2_7 + 3 response_transition_0_7 >= 0
_C74: _hiddenTransition0_0_7 + _hiddenTransition0_1_7 + _hiddenTransition0_2_7
 - response_transition_0_7 >= 0
_C75: - Color_0_7 - Color_0_8 + _hiddenTransition0_0_8 >= -1
_C76: Color_0_7 + Color_0_8 - 2 _hiddenTransition0_0_8 >= 0
_C77: - Color_1_7 - Color_1_8 + _hiddenTransition0_1_8 >= -1
_C78: Color_1_7 + Color_1_8 - 2 _hiddenTransition0_1_8 >= 0
_C79: - Color_2_7 - Color_2_8 + _hiddenTransition0_2_8 >= -1
_C8: Color_0_7 + Color_1_7 + Color_2_7 = 1
_C80: Color_2_7 + Color_2_8 - 2 _hiddenTransition0_2_8 >= 0
_C81: - _hiddenTransition0_0_8 - _hiddenTransition0_1_8
 - _hiddenTransition0_2_8 + 3 response_transition_0_8 >= 0
_C82: _hiddenTransition0_0_8 + _hiddenTransition0_1_8 + _hiddenTransition0_2_8
 - response_transition_0_8 >= 0
_C83: response_transition_0_0 = 0
_C84: - Color_0_0 - Color_1_1 + _hiddenTransition1_0_1 >= -1
_C85: Color_0_0 + Color_1_1 - 2 _hiddenTransition1_0_1 >= 0
_C86: - Color_0_0 - Color_2_1 + _hiddenTransition1_1_1 >= -1
_C87: Color_0_0 + Color_2_1 - 2 _hiddenTransition1_1_1 >= 0
_C88: - Color_0_1 - Color_1_0 + _hiddenTransition1_2_1 >= -1
_C89: Color_0_1 + Color_1_0 - 2 _hiddenTransition1_2_1 >= 0
_C9: Color_0_8 + Color_1_8 + Color_2_8 = 1
_C90: - Color_1_0 - Color_2_1 + _hiddenTransition1_3_1 >= -1
_C91: Color_1_0 + Color_2_1 - 2 _hiddenTransition1_3_1 >= 0
_C92: - Color_0_1 - Color_2_0 + _hiddenTransition1_4_1 >= -1
_C93: Color_0_1 + Color_2_0 - 2 _hiddenTransition1_4_1 >= 0
_C94: - Color_1_1 - Color_2_0 + _hiddenTransition1_5_1 >= -1
_C95: Color_1_1 + Color_2_0 - 2 _hiddenTransition1_5_1 >= 0
_C96: - _hiddenTransition1_0_1 - _hiddenTransition1_1_1
 - _hiddenTransition1_2_1 - _hiddenTransition1_3_1 - _hiddenTransition1_4_1
 - _hiddenTransition1_5_1 + 6 response_transition_1_1 >= 0
_C97: _hiddenTransition1_0_1 + _hiddenTransition1_1_1 + _hiddenTransition1_2_1
 + _hiddenTransition1_3_1 + _hiddenTransition1_4_1 + _hiddenTransition1_5_1
 - response_transition_1_1 >= 0
_C98: - Color_0_1 - Color_1_2 + _hiddenTransition1_0_2 >= -1
_C99: Color_0_1 + Color_1_2 - 2 _hiddenTransition1_0_2 >= 0
Bounds
 __dummy = 0
Binaries
Color_0_0
Color_0_1
Color_0_2
Color_0_3
Color_0_4
Color_0_5
Color_0_6
Color_0_7
Color_0_8
Color_1_0
Color_1_1
Color_1_2
Color_1_3
Color_1_4
Color_1_5
Color_1_6
Color_1_7
Color_1_8
Color_2_0
Color_2_1
Color_2_2
Color_2_3
Color_2_4
Color_2_5
Color_2_6
Color_2_7
Color_2_8
Crossing_0_0
Crossing_0_1
Crossing_0_2
Crossing_0_3
Crossing_0_4
Crossing_0_5
Crossing_0_6
Crossing_0_7
Crossing_0_8
Crossing_1_0
Crossing_1_1
Crossing_1_2
Crossing_1_3
Crossing_1_4
Crossing_1_5
Crossing_1_6
Crossing_1_7
Crossing_1_8
Crossing_2_0
Crossing_2_1
Crossing_2_2
Crossing_2_3
Crossing_2_4
Crossing_2_5
Crossing_2_6
Crossing_2_7
Crossing_2_8
Crossing_3_0
Crossing_3_1
Crossing_3_2
Crossing_3_3
Crossing_3_4
Crossing_3_5
Crossing_3_6
Crossing_3_7
Crossing_3_8
Crossing_4_0
Crossing_4_1
Crossing_4_2
Crossing_4_3
Crossing_4_4
Crossing_4_5
Crossing_4_6
Crossing_4_7
Crossing_4_8
Crossing_5_0
Crossing_5_1
Crossing_5_2
Crossing_5_3
Crossing_5_4
Crossing_5_5
Crossing_5_6
Crossing_5_7
Crossing_5_8
Crossing_6_0
Crossing_6_1
Crossing_6_2
Crossing_6_3
Crossing_6_4
Crossing_6_5
Crossing_6_6
Crossing_6_7
Crossing_6_8
Crossing_7_0
Crossing_7_1
Crossing_7_2
Crossing_7_3
Crossing_7_4
Crossing_7_5
Crossing_7_6
Crossing_7_7
Crossing_7_8
Crossing_8_0
Crossing_8_1
Crossing_8_2
Crossing_8_3
Crossing_8_4
Crossing_8_5
Crossing_8_6
Crossing_8_7
Crossing_8_8
Text_0_0
Text_0_1
Text_0_2
Text_0_3
Text_0_4
Text_0_5
Text_0_6
Text_0_7
Text_0_8
Text_1_0
Text_1_1
Text_1_2
Text_1_3
Text_1_4
Text_1_5
Text_1_6
Text_1_7
Text_1_8
Text_2_0
Text_2_1
Text_2_2
Text_2_3
Text_2_4
Text_2_5
Text_2_6
Text_2_7
Text_2_8
_hiddenTransition0_0_1
_hiddenTransition0_0_2
_hiddenTransition0_0_3
_hiddenTransition0_0_4
_hiddenTransition0_0_5
_hiddenTransition0_0_6
_hiddenTransition0_0_7
_hiddenTransition0_0_8
_hiddenTransition0_1_1
_hiddenTransition0_1_2
_hiddenTransition0_1_3
_hiddenTransition0_1_4
_hiddenTransition0_1_5
_hiddenTransition0_1_6
_hiddenTransition0_1_7
_hiddenTransition0_1_8
_hiddenTransition0_2_1
_hiddenTransition0_2_2
_hiddenTransition0_2_3
_hiddenTransition0_2_4
_hiddenTransition0_2_5
_hiddenTransition0_2_6
_hiddenTransition0_2_7
_hiddenTransition0_2_8
_hiddenTransition1_0_1
_hiddenTransition1_0_2
_hiddenTransition1_0_3
_hiddenTransition1_0_4
_hiddenTransition1_0_5
_hiddenTransition1_0_6
_hiddenTransition1_0_7
_hiddenTransition1_0_8
_hiddenTransition1_1_1
_hiddenTransition1_1_2
_hiddenTransition1_1_3
_hiddenTransition1_1_4
_hiddenTransition1_1_5
_hiddenTransition1_1_6
_hiddenTransition1_1_7
_hiddenTransition1_1_8
_hiddenTransition1_2_1
_hiddenTransition1_2_2
_hiddenTransition1_2_3
_hiddenTransition1_2_4
_hiddenTransition1_2_5
_hiddenTransition1_2_6
_hiddenTransition1_2_7
_hiddenTransition1_2_8
_hiddenTransition1_3_1
_hiddenTransition1_3_2
_hiddenTransition1_3_3
_hiddenTransition1_3_4
_hiddenTransition1_3_5
_hiddenTransition1_3_6
_hiddenTransition1_3_7
_hiddenTransition1_3_8
_hiddenTransition1_4_1
_hiddenTransition1_4_2
_hiddenTransition1_4_3
_hiddenTransition1_4_4
_hiddenTransition1_4_5
_hiddenTransition1_4_6
_hiddenTransition1_4_7
_hiddenTransition1_4_8
_hiddenTransition1_5_1
_hiddenTransition1_5_2
_hiddenTransition1_5_3
_hiddenTransition1_5_4
_hiddenTransition1_5_5
_hiddenTransition1_5_6
_hiddenTransition1_5_7
_hiddenTransition1_5_8
response_transition_0_0
response_transition_0_1
response_transition_0_2
response_transition_0_3
response_transition_0_4
response_transition_0_5
response_transition_0_6
response_transition_0_7
response_transition_0_8
response_transition_1_0
response_transition_1_1
response_transition_1_2
response_transition_1_3
response_transition_1_4
response_transition_1_5
response_transition_1_6
response_transition_1_7
response_transition_1_8
End
