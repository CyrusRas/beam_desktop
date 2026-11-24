"""Canvas rendering helpers for Beam Designer."""

FOREST = "#174d35"
GREEN = "#28754b"
GOLD = "#c9a227"
MUTED = "#526158"
PALE = "#eaf3ed"


def draw_beam(canvas, span, cantilever, points, uniforms):
    canvas.delete("all")
    width = max(canvas.winfo_width(), 500)
    left, right, y = 54, width-38, 70
    scale = (right-left)/span
    px = lambda x: left+x*scale
    canvas.create_line(left, y, right, y, fill=FOREST, width=10, capstyle="round")
    if cantilever:
        canvas.create_line(left-16, y-28, left-16, y+34, fill=FOREST, width=4)
        for yy in range(int(y-24), int(y+31), 12):
            canvas.create_line(left-16, yy, left-28, yy+8, fill=FOREST, width=2)
    else:
        canvas.create_polygon(left, y+7, left-18, y+34, left+18, y+34, fill=PALE, outline=FOREST, width=2)
        canvas.create_polygon(right, y+7, right-18, y+30, right+18, y+30, fill=PALE, outline=FOREST, width=2)
        canvas.create_oval(right+4, y+31, right+13, y+40, outline=FOREST, fill="white", width=2)
    for load in uniforms:
        xa, xb = px(load.start), px(load.end)
        canvas.create_line(xa, y-27, xb, y-27, fill=GREEN, width=2)
        for i in range(9):
            x = xa+(xb-xa)*i/8
            if load.intensity < 0:
                canvas.create_line(x, y-25, x, y-3, fill=GREEN, arrow="last", width=2)
            else:
                canvas.create_line(x, y+25, x, y+3, fill=GREEN, arrow="last", width=2)
        canvas.create_text((xa+xb)/2, y-39, text=f"{abs(load.intensity):g} kip/ft {'down' if load.intensity < 0 else 'up'}", fill=MUTED)
    for load in points:
        x = px(load.position)
        if load.magnitude < 0:
            canvas.create_line(x, y-39, x, y-5, fill=GREEN, arrow="last", width=3)
        else:
            canvas.create_line(x, y+39, x, y+5, fill=GREEN, arrow="last", width=3)
        canvas.create_text(x, y-50 if load.magnitude < 0 else y+50,
                           text=f"{abs(load.magnitude):g} kip {'down' if load.magnitude < 0 else 'up'}", fill=MUTED)
    canvas.create_text(left, y+53, text="0 ft", fill=MUTED, anchor="w")
    canvas.create_text(right, y+53, text=f"{span:g} ft", fill=MUTED, anchor="e")
    canvas.create_text((left+right)/2, y+53, text="x from left end / fixed end", fill=MUTED)


def draw_diagram(canvas, xs, values, span, units, positive_label, invert=False):
    canvas.delete("all")
    width, height = max(canvas.winfo_width(), 370), max(canvas.winfo_height(), 175)
    left, right, top, bottom = 45, width-18, 17, height-30
    largest = max((abs(v) for v in values), default=0.0)
    scale = (bottom-top)*0.42/max(largest, 0.05)
    zero = (top+bottom)/2
    coords = []
    for x, value in zip(xs, values):
        xx = left+x/span*(right-left)
        yy = zero + (1 if invert else -1)*value*scale
        coords.extend((xx, yy))
    canvas.create_line(left, zero, right, zero, fill="#9eaca2")
    canvas.create_line(left, top, left, bottom, fill="#9eaca2")
    if len(coords) >= 4:
        canvas.create_line(*coords, fill=GREEN, width=2.5, smooth=False)
        if not invert:
            polygon = [left, zero, *coords, right, zero]
            canvas.create_polygon(*polygon, fill=PALE, outline="")
            canvas.create_line(*coords, fill=GREEN, width=2.5)
    canvas.create_text(6, 12, text=units, fill=MUTED, anchor="w")
    canvas.create_text(left, height-8, text="0 ft", fill=MUTED, anchor="w")
    canvas.create_text(right, height-8, text=f"{span:g} ft", fill=MUTED, anchor="e")
    canvas.create_text(width-18, top, text=positive_label, fill=MUTED, anchor="ne")
