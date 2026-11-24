"""Statics and elastic response for a prismatic single-span beam."""

from dataclasses import dataclass
import math

from member_data import Member


@dataclass(frozen=True)
class PointLoad:
    magnitude: float  # kip; upward positive
    position: float   # ft from left/fixed end


@dataclass(frozen=True)
class UniformLoad:
    intensity: float  # kip/ft; upward positive
    start: float
    end: float


@dataclass
class Analysis:
    span: float
    cantilever: bool
    reaction_a: float
    reaction_b: float
    reaction_moment: float
    xs: list[float]
    shears: list[float]
    moments: list[float]
    deflections: list[float]
    max_shear: float
    shear_x: float
    max_moment: float
    moment_x: float
    max_deflection: float
    deflection_x: float
    deflection_down: bool
    limit: float
    bending_stress: float
    bending_pass: bool
    deflection_pass: bool


def _finite(value: float, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number.") from None
    if not math.isfinite(result):
        raise ValueError(f"{label} must be a finite number.")
    return result


def validate_inputs(span: float, points: list[PointLoad], uniforms: list[UniformLoad]) -> float:
    length = _finite(span, "Span")
    if length <= 0:
        raise ValueError("Enter a span greater than zero.")
    for load in points:
        p, x = _finite(load.magnitude, "Point load"), _finite(load.position, "Point-load position")
        if not 0 <= x <= length:
            raise ValueError("Point-load positions must lie within the span.")
    for load in uniforms:
        w = _finite(load.intensity, "Uniform-load intensity")
        a, b = _finite(load.start, "Uniform-load start"), _finite(load.end, "Uniform-load end")
        if a < 0 or b > length or b <= a:
            raise ValueError("Uniform loads need 0 ≤ start < end ≤ span.")
    return length


def analyze(span: float, cantilever: bool, points: list[PointLoad],
            uniforms: list[UniformLoad], member: Member) -> Analysis:
    length = validate_inputs(span, points, uniforms)
    resultant = sum(p.magnitude for p in points) + sum(u.intensity * (u.end-u.start) for u in uniforms)
    load_moment = sum(p.magnitude*p.position for p in points) + sum(
        u.intensity*(u.end-u.start)*(u.start+u.end)/2 for u in uniforms
    )
    if cantilever:
        ra, rb, support_moment = -resultant, 0.0, -load_moment
    else:
        rb = -load_moment / length
        ra = -resultant - rb
        support_moment = 0.0

    breakpoints = sorted({0.0, length, *(p.position for p in points),
                          *(u.start for u in uniforms), *(u.end for u in uniforms)})

    def shear(x: float, side: str = "right") -> float:
        value = ra + sum(p.magnitude for p in points if
                         (p.position < x - 1e-10 or (side == "right" and abs(p.position-x) <= 1e-10)))
        value += sum(u.intensity * max(0.0, min(x, u.end)-u.start) for u in uniforms)
        return value

    def moment(x: float) -> float:
        value = -support_moment + ra*x
        value += sum(p.magnitude*(x-p.position) for p in points if x > p.position)
        for u in uniforms:
            z = min(x, u.end)
            if z > u.start:
                value += u.intensity*(z-u.start)*(x-(u.start+z)/2)
        return value

    # Since shear is linear between load discontinuities, these roots locate
    # every interior moment extremum. Evaluate both sides of point-load jumps.
    shear_candidates = [(x, side) for x in breakpoints for side in ("left", "right")]
    max_v, x_v = max(((abs(shear(x, side)), x) for x, side in shear_candidates), default=(0.0, 0.0))
    moment_candidates = set(breakpoints)
    for a, b in zip(breakpoints, breakpoints[1:]):
        va, vb = shear(a, "right"), shear(b, "left")
        if abs(va-vb) > 1e-14:
            root = a - va*(b-a)/(vb-va)
            if a < root < b:
                moment_candidates.add(root)
    max_m, x_m = max(((abs(moment(x)), x) for x in moment_candidates), default=(0.0, 0.0))

    # Integrate y'' = -M/EI with x measured in feet and y in inches. The 1728
    # factor converts kip-ft/ksi-in^4 to inches per foot squared.
    n = max(1200, min(20000, int(100*length)))
    xs = sorted({*(length*i/n for i in range(n+1)), *breakpoints})
    dxs = [xs[i]-xs[i-1] for i in range(1, len(xs))]
    curvatures = [-moment(x)*1728.0/(member.elastic_modulus*member.inertia) for x in xs]
    slopes = [0.0]
    ys = [0.0]
    for i, dx in enumerate(dxs, 1):
        slopes.append(slopes[-1] + (curvatures[i-1]+curvatures[i])*dx/2)
        ys.append(ys[-1] + (slopes[-2]+slopes[-1])*dx/2)
    if not cantilever:
        slope_at_a = -ys[-1]/length
        ys = [y + slope_at_a*x for x, y in zip(xs, ys)]
    i_def = max(range(len(ys)), key=lambda i: abs(ys[i]))
    max_def, x_def = abs(ys[i_def]), xs[i_def]
    limit = length*12/360
    stress = max_m*12/member.section_modulus
    return Analysis(length, cantilever, ra, rb, support_moment, xs,
                    [shear(x) for x in xs], [moment(x) for x in xs], ys,
                    max_v, x_v, max_m, x_m, max_def, x_def, ys[i_def] >= 0,
                    limit, stress, stress <= member.allowable_bending,
                    max_def <= limit)
