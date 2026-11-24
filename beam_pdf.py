"""Create a self-contained vector PDF calculation sheet without dependencies."""

from datetime import date
from pathlib import Path
import unicodedata

from beam_csv import response_rows


PAGE_W, PAGE_H = 792.0, 612.0  # US Letter, landscape, points
MARGIN = 28.0
FOREST = "#174D35"
GREEN = "#28754B"
PALE = "#EAF3ED"
GOLD = "#C9A227"
INK = "#1E2A22"
MUTED = "#526158"
LINE = "#CBD8CE"
PASS = "#17613C"
FAIL = "#8D261F"


def _rgb(color):
    color = {"white": "#FFFFFF", "black": "#000000"}.get(color.lower(), color)
    color = color.lstrip("#")
    return tuple(int(color[i:i+2], 16)/255 for i in (0, 2, 4))


def _display_text(value):
    value = str(value).replace("×", "x").replace("·", " | ").replace("–", "-").replace("—", "-")
    value = value.replace("³", "3").replace("⁴", "4").replace("≤", "<=").replace("≥", ">=")
    return unicodedata.normalize("NFKD", value).encode("cp1252", "replace").decode("cp1252")


def _pdf_text(value):
    raw = _display_text(value).encode("cp1252", "replace")
    escaped = []
    for byte in raw:
        if byte in (40, 41, 92):
            escaped.append("\\" + chr(byte))
        elif 32 <= byte <= 126:
            escaped.append(chr(byte))
        else:
            escaped.append(f"\\{byte:03o}")
    return "".join(escaped)


def _fmt(value, decimals=2):
    return f"{value:.{decimals}f}"


class _Page:
    def __init__(self):
        self.ops = []

    def _stroke(self, color):
        r, g, b = _rgb(color)
        self.ops.append(f"{r:.4f} {g:.4f} {b:.4f} RG")

    def _fill(self, color):
        r, g, b = _rgb(color)
        self.ops.append(f"{r:.4f} {g:.4f} {b:.4f} rg")

    def line(self, x1, y1, x2, y2, color=LINE, width=0.7):
        self._stroke(color)
        self.ops.append(f"{width:.2f} w {x1:.2f} {PAGE_H-y1:.2f} m {x2:.2f} {PAGE_H-y2:.2f} l S")

    def rect(self, x, y, w, h, fill="white", stroke=LINE, width=0.7):
        if fill:
            self._fill(fill)
        if stroke:
            self._stroke(stroke)
        mode = "B" if fill and stroke else ("f" if fill else "S")
        self.ops.append(f"{width:.2f} w {x:.2f} {PAGE_H-y-h:.2f} {w:.2f} {h:.2f} re {mode}")

    def text(self, x, y, value, size=8, color=INK, bold=False, align="left"):
        display = _display_text(value)
        if align == "right":
            x -= len(display)*size*0.50
        elif align == "center":
            x -= len(display)*size*0.25
        value = _pdf_text(display)
        self._fill(color)
        font = "F2" if bold else "F1"
        baseline = PAGE_H-y-size
        self.ops.append(f"BT /{font} {size:.2f} Tf 1 0 0 1 {x:.2f} {baseline:.2f} Tm ({value}) Tj ET")

    def circle(self, x, y, radius, fill=GREEN, stroke=None, width=0.7):
        k = 0.55228475*radius
        cy = PAGE_H-y
        self._fill(fill) if fill else None
        self._stroke(stroke) if stroke else None
        mode = "B" if fill and stroke else ("f" if fill else "S")
        self.ops.append(
            f"{width:.2f} w {x+radius:.2f} {cy:.2f} m "
            f"{x+radius:.2f} {cy+k:.2f} {x+k:.2f} {cy+radius:.2f} {x:.2f} {cy+radius:.2f} c "
            f"{x-k:.2f} {cy+radius:.2f} {x-radius:.2f} {cy+k:.2f} {x-radius:.2f} {cy:.2f} c "
            f"{x-radius:.2f} {cy-k:.2f} {x-k:.2f} {cy-radius:.2f} {x:.2f} {cy-radius:.2f} c "
            f"{x+k:.2f} {cy-radius:.2f} {x+radius:.2f} {cy-k:.2f} {x+radius:.2f} {cy:.2f} c {mode}"
        )

    def polyline(self, points, color=GREEN, width=1.2):
        if len(points) < 2:
            return
        self._stroke(color)
        commands = [f"{width:.2f} w {points[0][0]:.2f} {PAGE_H-points[0][1]:.2f} m"]
        commands.extend(f"{x:.2f} {PAGE_H-y:.2f} l" for x, y in points[1:])
        commands.append("S")
        self.ops.append(" ".join(commands))

    def polygon(self, points, fill=PALE, stroke=None, width=0.7):
        if len(points) < 3:
            return
        self._fill(fill) if fill else None
        self._stroke(stroke) if stroke else None
        commands = [f"{width:.2f} w {points[0][0]:.2f} {PAGE_H-points[0][1]:.2f} m"]
        commands.extend(f"{x:.2f} {PAGE_H-y:.2f} l" for x, y in points[1:])
        commands.append("h")
        commands.append("B" if fill and stroke else ("f" if fill else "S"))
        self.ops.append(" ".join(commands))

    def bytes(self):
        return "\n".join(self.ops).encode("ascii")

def _write_pdf(path, pages):
    objects = [None, None,
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
               b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"]
    page_ids = []
    for page in pages:
        page_id = len(objects)+1
        content_id = page_id+1
        page_ids.append(page_id)
        stream = page.bytes()
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W:.0f} {PAGE_H:.0f}] "
            f"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {content_id} 0 R >>".encode("ascii")
        )
        objects.append(f"<< /Length {len(stream)} >>\nstream\n".encode("ascii")+stream+b"\nendstream")
    objects[0] = b"<< /Type /Catalog /Pages 2 0 R >>"
    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("ascii")

    output = bytearray(b"%PDF-1.4\n% Beam Designer\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode("ascii"))
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    Path(path).write_bytes(output)


def _header(page, page_no, page_count, subtitle="Preliminary beam analysis"):
    # Small original mountain mark, matching the application palette.
    page.polygon([(MARGIN, 39), (MARGIN+10, 21), (MARGIN+17, 33),
                  (MARGIN+23, 24), (MARGIN+34, 39)], fill=PALE)
    page.polyline([(MARGIN, 39), (MARGIN+10, 21), (MARGIN+17, 33),
                   (MARGIN+23, 24), (MARGIN+34, 39)], color=FOREST, width=1.2)
    page.line(MARGIN, 40, MARGIN+34, 40, color=FOREST, width=0.8)
    page.text(MARGIN+43, 19, "Beam Designer", 16, FOREST, True)
    page.text(MARGIN+43, 40, subtitle, 8, MUTED)
    page.text(PAGE_W-MARGIN, 21, f"PRELIMINARY CALCULATION SHEET  |  {date.today().isoformat()}", 7.2, MUTED, True, "right")
    page.line(MARGIN, 57, PAGE_W-MARGIN, 57, color=GOLD, width=1.4)
    page.text(PAGE_W-MARGIN, 42, f"Page {page_no} of {page_count}", 7.2, MUTED, align="right")


def _member_panel(page, result, member, y, height=48):
    x, w = MARGIN, PAGE_W-2*MARGIN
    page.rect(x, y, w, height, fill="white", stroke=LINE)
    page.rect(x, y, 4, height, fill=FOREST, stroke=None)
    page.text(x+12, y+5, "BEAM AND MEMBER INPUTS", 7.1, FOREST, True)
    support = "Cantilever (fixed to free)" if result.cantilever else "Simply supported"
    page.text(x+12, y+17, f"Span: {_fmt(result.span,2)} ft", 9, INK, True)
    page.text(x+188, y+17, f"Support: {support}", 9, INK, True)
    page.text(x+450, y+17, f"Member: {member.label}", 9, INK, True)
    page.text(x+12, y+33,
              f"S = {_fmt(member.section_modulus,2)} in3   |   I = {_fmt(member.inertia,1)} in4   |   E = {_fmt(member.elastic_modulus,0)} ksi   |   Fb allowable = {_fmt(member.allowable_bending,2)} ksi",
              7.6, MUTED)
    page.text(PAGE_W-MARGIN-9, y+33, f"Deflection limit: L/360 = {_fmt(result.limit,3)} in", 7.6, MUTED, align="right")


def _load_rows(points, uniforms):
    rows = []
    for index, load in enumerate(points, 1):
        direction = "Up" if load.magnitude > 0 else "Down"
        rows.append((f"P{index}  Point", f"{abs(load.magnitude):g} kip", direction,
                     f"x = {load.position:g} ft"))
    for index, load in enumerate(uniforms, 1):
        direction = "Up" if load.intensity > 0 else "Down"
        rows.append((f"U{index}  Uniform", f"{abs(load.intensity):g} kip/ft", direction,
                     f"{load.start:g} to {load.end:g} ft"))
    return rows


def _load_table(page, rows, y, height, title="APPLIED LOADS"):
    x, w = MARGIN, PAGE_W-2*MARGIN
    page.rect(x, y, w, height, fill="white", stroke=LINE)
    page.text(x+9, y+4, title, 7.1, FOREST, True)
    header_y = y+16
    page.rect(x+1, header_y, w-2, 11, fill=PALE, stroke=None)
    columns = (x+9, x+275, x+435, x+525)
    for cx, label in zip(columns, ("Load", "Magnitude", "Direction", "Position / interval")):
        page.text(cx, header_y+2, label, 6.7, MUTED, True)
    row_h = 11.5
    for i, row in enumerate(rows):
        ry = header_y+11+i*row_h
        if i % 2 == 1:
            page.rect(x+1, ry, w-2, row_h, fill="#FAFCFA", stroke=None)
        for col, value in zip(columns, row):
            page.text(col, ry+1.5, value, 7.0, INK)
        if i+1 < len(rows):
            page.line(x+7, ry+row_h, x+w-7, ry+row_h, color="#E7EDE8", width=0.35)
    if not rows:
        page.text(x+9, header_y+14, "No applied loads", 7.2, MUTED)
    return header_y+11+max(1, len(rows))*row_h


def _arrow(page, x, y_top, y_bottom, color=GREEN, width=1.0):
    page.line(x, y_top, x, y_bottom, color, width)
    direction = 1 if y_bottom > y_top else -1
    tip_y = y_bottom
    page.line(x, tip_y, x-2.7, tip_y-direction*4, color, width)
    page.line(x, tip_y, x+2.7, tip_y-direction*4, color, width)


def _beam_diagram(page, result, points, uniforms, y, height, labels=True):
    x, w = MARGIN, PAGE_W-2*MARGIN
    page.rect(x, y, w, height, fill="white", stroke=LINE)
    page.text(x+9, y+4, "BEAM AND LOADS", 7.1, FOREST, True)
    left, right = x+35, x+w-35
    beam_y = y+height*0.52
    scale = (right-left)/result.span
    px = lambda at: left+at*scale
    page.line(left, beam_y, right, beam_y, FOREST, 4.2)
    if result.cantilever:
        wall_x = left-9
        page.line(wall_x, beam_y-16, wall_x, beam_y+17, FOREST, 2.0)
        for k in range(5):
            yy = beam_y-14+k*7
            page.line(wall_x-6, yy-3, wall_x, yy, FOREST, 0.8)
    else:
        page.polygon([(left, beam_y+3), (left-9, beam_y+15), (left+9, beam_y+15)], fill=PALE, stroke=FOREST)
        page.polygon([(right, beam_y+3), (right-9, beam_y+15), (right+9, beam_y+15)], fill=PALE, stroke=FOREST)
        page.circle(right-3, beam_y+19, 2.2, fill="white", stroke=FOREST, width=0.8)
        page.circle(right+3, beam_y+19, 2.2, fill="white", stroke=FOREST, width=0.8)

    for index, load in enumerate(uniforms, 1):
        xa, xb = px(load.start), px(load.end)
        arrow_y = beam_y-12 if load.intensity < 0 else beam_y+12
        page.line(xa, arrow_y, xb, arrow_y, GREEN, 0.8)
        arrows = max(2, min(8, int((xb-xa)/36)+1))
        for j in range(arrows):
            xx = xa+(xb-xa)*(j/(arrows-1))
            if load.intensity < 0:
                _arrow(page, xx, arrow_y+1, beam_y-2, GREEN, 0.7)
            else:
                _arrow(page, xx, arrow_y-1, beam_y+2, GREEN, 0.7)
        if labels and len(points)+len(uniforms) == 1:
            page.text((xa+xb)/2, arrow_y-8 if load.intensity < 0 else arrow_y+2,
                      f"U{index}", 6.2, GREEN, True, "center")

    for index, load in enumerate(points, 1):
        xx = px(load.position)
        if load.magnitude < 0:
            _arrow(page, xx, beam_y-18, beam_y-3, GREEN, 0.9)
            if labels and len(points)+len(uniforms) == 1:
                page.text(xx+4, beam_y-22, f"P{index}", 6.2, GREEN, True)
        else:
            _arrow(page, xx, beam_y+19, beam_y+3, GREEN, 0.9)
            if labels and len(points)+len(uniforms) == 1:
                page.text(xx+4, beam_y+12, f"P{index}", 6.2, GREEN, True)
    page.text(left, y+height-8, "0 ft", 6.2, MUTED)
    page.text(right, y+height-8, f"{result.span:g} ft", 6.2, MUTED, align="right")
    page.text((left+right)/2, y+height-8, "x from left end / fixed end", 6.2, MUTED, align="center")
    if not labels:
        page.text(right-6, y+8, "Load IDs and magnitudes listed above", 6.0, MUTED, align="right")


def _chart(page, x, y, w, h, title, subtitle, xs, values, positive_down=False):
    page.rect(x, y, w, h, fill="white", stroke=LINE)
    page.text(x+8, y+4, title, 7.2, FOREST, True)
    page.text(x+w-8, y+5, subtitle, 6.2, MUTED, align="right")
    plot_left, plot_right = x+34, x+w-12
    plot_top, plot_bottom = y+20, y+h-15
    zero = (plot_top+plot_bottom)/2
    max_abs = max((abs(v) for v in values), default=0.0)
    extent = max(max_abs*1.12, 0.05)
    scale = (plot_bottom-plot_top)*0.44/extent
    page.line(plot_left, plot_top, plot_left, plot_bottom, color=LINE, width=0.55)
    page.line(plot_left, zero, plot_right, zero, color="#85948A", width=0.65)
    page.line(plot_left, plot_top, plot_right, plot_top, color="#E7EDE8", width=0.35)
    page.line(plot_left, plot_bottom, plot_right, plot_bottom, color="#E7EDE8", width=0.35)
    points = []
    span = xs[-1] if xs else 1.0
    for at, val in zip(xs, values):
        xx = plot_left + at/span*(plot_right-plot_left) if span else plot_left
        yy = zero + (val if positive_down else -val)*scale
        points.append((xx, yy))
    page.polyline(points, GREEN, 1.05)
    top_tick = -max_abs if positive_down else max_abs
    bottom_tick = max_abs if positive_down else -max_abs
    page.text(x+4, plot_top-1, _fmt(top_tick,1), 5.7, MUTED)
    page.text(x+7, zero-3, "0", 5.7, MUTED)
    page.text(x+4, plot_bottom-5, _fmt(bottom_tick,1), 5.7, MUTED)
    page.text(plot_left, y+h-10, "0", 5.8, MUTED)
    page.text(plot_right, y+h-10, f"{span:g} ft", 5.8, MUTED, align="right")


def _analysis_charts(page, result, points, uniforms, member, y_top, y_bottom,
                     labels=True, include_beam=True):
    if include_beam:
        beam_y = y_top
        beam_h = 59
        _beam_diagram(page, result, points, uniforms, beam_y, beam_h, labels)
        vm_y = beam_y+beam_h+7
    else:
        vm_y = y_top
    gutter = 8
    half_w = ((PAGE_W-2*MARGIN)-gutter)/2
    vm_h = 96
    shear_rows = list(response_rows(result, points))
    shear_xs = [row[0] for row in shear_rows]
    shear_values = [row[1] for row in shear_rows]
    _chart(page, MARGIN, vm_y, half_w, vm_h, "SHEAR  V (kip)", "+ upward on left face",
           shear_xs, shear_values)
    _chart(page, MARGIN+half_w+gutter, vm_y, half_w, vm_h, "MOMENT  M (kip-ft)", "+ sagging",
           result.xs, result.moments)
    defl_y = vm_y+vm_h+7
    defl_h = max(63.0, y_bottom-defl_y)
    _chart(page, MARGIN, defl_y, PAGE_W-2*MARGIN, defl_h, "DEFLECTION (in)", "downward positive",
           result.xs, result.deflections, positive_down=True)
    return defl_y+defl_h


def _results(page, result, member, y, h):
    x, w = MARGIN, PAGE_W-2*MARGIN
    page.rect(x, y, w, h, fill="white", stroke=LINE)
    page.rect(x, y, 4, h, fill=FOREST, stroke=None)
    page.text(x+10, y+5, "RESULTS AND CHECKS", 7.1, FOREST, True)
    if result.cantilever:
        reaction = (f"Fixed reaction: {abs(result.reaction_a):.2f} kip "
                    f"({'up' if result.reaction_a >= 0 else 'down'})   |   "
                    f"Fixed moment: {abs(result.reaction_moment):.2f} kip-ft "
                    f"({'CCW' if result.reaction_moment >= 0 else 'CW'})")
    else:
        reaction = (f"Reaction A: {abs(result.reaction_a):.2f} kip ({'up' if result.reaction_a >= 0 else 'down'})   |   "
                    f"Reaction B: {abs(result.reaction_b):.2f} kip ({'up' if result.reaction_b >= 0 else 'down'})")
    page.text(x+10, y+17, reaction, 7.2, INK, True)
    metrics = (
        f"Max |V| = {result.max_shear:.2f} kip at x={result.shear_x:.2f} ft",
        f"Max |M| = {result.max_moment:.2f} kip-ft at x={result.moment_x:.2f} ft",
        f"Max |deflection| = {result.max_deflection:.3f} in at x={result.deflection_x:.2f} ft ({'down' if result.deflection_down else 'up'})",
    )
    col_w = (w-20)/3
    for i, metric in enumerate(metrics):
        page.text(x+10+i*col_w, y+30, metric, 6.6, INK)
    check_y = y+42
    left_box_w = (w-30)/2
    page.rect(x+10, check_y, left_box_w, 17, fill="#EEF6F0" if result.bending_pass else "#FFF1EF", stroke=None)
    page.rect(x+20+left_box_w, check_y, left_box_w, 17, fill="#EEF6F0" if result.deflection_pass else "#FFF1EF", stroke=None)
    bend = f"BENDING  {'PASS' if result.bending_pass else 'FAIL'}  |  fb {result.bending_stress:.2f} / Fb {member.allowable_bending:.2f} ksi"
    defl = f"DEFLECTION  {'PASS' if result.deflection_pass else 'FAIL'}  |  {result.max_deflection:.3f} / L/360 {result.limit:.3f} in"
    page.text(x+16, check_y+4, bend, 6.7, PASS if result.bending_pass else FAIL, True)
    page.text(x+26+left_box_w, check_y+4, defl, 6.7, PASS if result.deflection_pass else FAIL, True)
    page.text(x+10, y+h-11,
              "Not checked: shear strength, bearing, buckling, lateral stability, or other complete design requirements.",
              6.2, MUTED)


def _footer(page):
    page.line(MARGIN, PAGE_H-24, PAGE_W-MARGIN, PAGE_H-24, color=LINE, width=0.5)
    page.text(MARGIN, PAGE_H-19,
              "Preliminary educational analysis. Self-weight is not added; no load factors/combinations. Shear, bearing, buckling, and lateral stability are not checked. Verify all design requirements.",
              6.2, MUTED)


def _single_page(result, points, uniforms, member, page_no, page_count):
    page = _Page()
    _header(page, page_no, page_count)
    _member_panel(page, result, member, 64, 47)
    rows = _load_rows(points, uniforms)
    table_end = _load_table(page, rows, 118, 28+max(1, len(rows))*11.5)
    beam_top = max(164, table_end+6)
    results_top = 480
    charts_bottom = results_top-7
    chart_end = _analysis_charts(page, result, points, uniforms, member, beam_top,
                                 charts_bottom, labels=True)
    _results(page, result, member, results_top, 88)
    _footer(page)
    return page


def _input_page(result, member, load_rows, page_no, page_count, continuation=False,
                points=(), uniforms=(), show_beam=False):
    page = _Page()
    _header(page, page_no, page_count, "Beam inputs and applied load schedule")
    _member_panel(page, result, member, 65, 48)
    title = "APPLIED LOADS (CONTINUED)" if continuation else "APPLIED LOADS"
    table_end = _load_table(page, load_rows, 123, 31+len(load_rows)*12, title)
    if show_beam:
        beam_y = table_end+8
        beam_h = max(90, PAGE_H-38-beam_y)
        _beam_diagram(page, result, points, uniforms, beam_y, beam_h, labels=False)
    _footer(page)
    return page


def _analysis_page(result, points, uniforms, member, page_no, page_count, input_pages,
                   include_beam=True):
    page = _Page()
    _header(page, page_no, page_count, "Diagrams and design checks")
    _member_panel(page, result, member, 64, 47)
    page_span = "page 1" if input_pages == 1 else f"pages 1-{input_pages}"
    page.text(MARGIN+4, 117,
              f"Applied loads are itemized on {page_span}.",
              6.8, MUTED)
    results_top = 480
    _analysis_charts(page, result, points, uniforms, member, 127, results_top-7,
                     labels=False, include_beam=include_beam)
    _results(page, result, member, results_top, 88)
    _footer(page)
    return page


def create_report(path, result, points, uniforms, member):
    """Write a concise one-page sheet, or paginate a longer load schedule."""
    all_rows = _load_rows(points, uniforms)
    if len(all_rows) <= 5:
        pages = [_single_page(result, points, uniforms, member, 1, 1)]
    else:
        rows_per_page = 34
        chunks = [all_rows[i:i+rows_per_page] for i in range(0, len(all_rows), rows_per_page)]
        input_page_count = len(chunks)
        total_pages = input_page_count+1
        input_has_beam = len(all_rows) <= 20 and input_page_count == 1
        pages = [
            _input_page(result, member, chunk, i+1, total_pages, continuation=(i>0),
                        points=points, uniforms=uniforms, show_beam=input_has_beam and i == 0)
            for i, chunk in enumerate(chunks)
        ]
        pages.append(_analysis_page(result, points, uniforms, member, total_pages,
                                    total_pages, input_page_count, include_beam=not input_has_beam))
    _write_pdf(path, pages)
    return Path(path)
