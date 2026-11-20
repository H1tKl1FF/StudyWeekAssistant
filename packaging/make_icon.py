"""Draw the Windows icon (app_icon.ico) in the app's own colours: deep blue and amber."""
import os
from PIL import Image, ImageDraw

DEEP_BLUE = "#0C447C"
AMBER = "#EF9F27"
LIGHT_BLUE = "#B5D4F4"
SIZE = 256


def draw_icon():
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    pen = ImageDraw.Draw(image)
    pen.rounded_rectangle((8, 8, SIZE - 8, SIZE - 8), radius=48, fill=DEEP_BLUE)
    # a small calendar: header bar, two rings and a 3x2 grid with one amber day
    pen.rounded_rectangle((52, 70, 204, 196), radius=16, fill="white")
    pen.rectangle((52, 70, 204, 104), fill=LIGHT_BLUE)
    for x in (92, 164):
        pen.rounded_rectangle((x - 7, 52, x + 7, 86), radius=7, fill=AMBER)
    for row in range(2):
        for col in range(3):
            left, top = 70 + col * 42, 118 + row * 38
            colour = AMBER if (row, col) == (1, 2) else DEEP_BLUE
            pen.rounded_rectangle((left, top, left + 30, top + 26), radius=6, fill=colour)
    return image


if __name__ == "__main__":
    target = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico")
    draw_icon().save(target, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Saved", target)
