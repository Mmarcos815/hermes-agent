"""Template-tap finder: crop CLAIM badge from a known shot, locate it live."""
import cv2
import numpy as np

# CLAIM badge approx region in 1080x2340 (top-left icon row)
X0, Y0, X1, Y1 = 120, 80, 330, 215

ref = cv2.imread("farm_3phones/fix01_home.png")
live = cv2.imread("farm_3phones/d3_home.png")
assert ref is not None and live is not None, "missing screenshots"

tpl = ref[Y0:Y1, X0:X1]
res = cv2.matchTemplate(live, tpl, cv2.TM_CCOEFF_NORMED)
_, score, _, loc = cv2.minMaxLoc(res)
cx, cy = loc[0] + (X1 - X0) // 2, loc[1] + (Y1 - Y0) // 2
print(f"score={score:.3f} tap=({cx},{cy})")
print("LOCKED" if score > 0.85 else "WEAK")
