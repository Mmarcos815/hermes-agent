from PIL import Image
img = Image.open('farm_3phones/trace_finder.png')
w, h = img.size
for y in range(h):
    green = 0
    for x in range(0, w, 4):
        r, g, b = img.getpixel((x, y))[:3]
        if g > 200 and r < 100 and b < 100:
            green += 1
    if green > w // 8:
        print(f"y={y}: {green} green pixels")
