"""CSV export for sampled beam response values."""

import csv
from pathlib import Path


HEADERS = (
    "x (ft)",
    "V (kip)",
    "M (kip-ft)",
    "Deflection (in, downward +)",
    "Shear side at point load",
)


def _number(value):
    return format(value, ".10g")


def response_rows(analysis, points):
    """Yield sample rows, including both shear limits at interior point loads."""
    point_jumps = {}
    for load in points:
        point_jumps[load.position] = point_jumps.get(load.position, 0.0) + load.magnitude

    for i, x in enumerate(analysis.xs):
        jump = point_jumps.get(x, 0.0)
        shear_right = analysis.shears[i]
        if abs(jump) <= 1e-12:
            yield (x, shear_right, analysis.moments[i], analysis.deflections[i], "")
        elif x == 0.0:
            # At the left boundary, only the in-span right side is meaningful.
            yield (x, shear_right, analysis.moments[i], analysis.deflections[i], "right")
        elif x == analysis.span:
            # At the right boundary, the in-span value is the left limit.
            yield (x, shear_right-jump, analysis.moments[i], analysis.deflections[i], "left")
        else:
            yield (x, shear_right-jump, analysis.moments[i], analysis.deflections[i], "left")
            yield (x, shear_right, analysis.moments[i], analysis.deflections[i], "right")


def export_csv(path, analysis, points):
    """Write sampled x, V, M and deflection values as Excel-friendly UTF-8 CSV."""
    destination = Path(path)
    with destination.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(HEADERS)
        for x, shear, moment, deflection, side in response_rows(analysis, points):
            writer.writerow((_number(x), _number(shear), _number(moment), _number(deflection), side))
    return destination
