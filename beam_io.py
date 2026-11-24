"""Versioned JSON persistence for Beam Designer beam configurations."""

import json
import math
import os
from pathlib import Path

from beam_analysis import PointLoad, UniformLoad, validate_inputs
from member_data import get_member


FORMAT_NAME = "beam-designer"
FORMAT_VERSION = 1
DEFLECTION_LIMIT_DENOMINATOR = 360


def _number(value, label):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number.") from None
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite.")
    return number


def normalize_config(raw):
    """Validate a decoded configuration and return its canonical form."""
    if not isinstance(raw, dict):
        raise ValueError("The file must contain a JSON object.")
    if raw.get("format") != FORMAT_NAME:
        raise ValueError("This is not a Beam Designer file.")
    if raw.get("version") != FORMAT_VERSION:
        raise ValueError(f"Unsupported Beam Designer file version: {raw.get('version')}.")

    beam = raw.get("beam")
    if not isinstance(beam, dict):
        raise ValueError("The file is missing beam settings.")
    support = beam.get("support")
    if support not in ("Simply supported", "Cantilever"):
        raise ValueError("The file has an unsupported support condition.")
    span = _number(beam.get("span_ft"), "Span")
    if span <= 0:
        raise ValueError("Span must be greater than zero.")

    member = beam.get("member")
    if not isinstance(member, dict):
        raise ValueError("The file is missing member selection.")
    member_type = member.get("type")
    if member_type == "Steel W-shape":
        shape, grade = member.get("shape"), member.get("grade")
        try:
            get_member(member_type, shape, grade, "", "")
        except (KeyError, TypeError):
            raise ValueError("The file contains an unknown steel shape or grade.") from None
        normalized_member = {"type": member_type, "shape": shape, "grade": grade}
    elif member_type == "Lumber":
        species, size = member.get("species"), member.get("size")
        try:
            get_member(member_type, "", "", species, size)
        except (KeyError, TypeError):
            raise ValueError("The file contains an unknown lumber species or size.") from None
        normalized_member = {"type": member_type, "species": species, "size": size}
    else:
        raise ValueError("The file has an unsupported member type.")

    limit = beam.get("deflection_limit")
    if not isinstance(limit, dict) or limit.get("type") != "span_ratio":
        raise ValueError("The file has an unsupported deflection limit.")
    denominator = limit.get("denominator")
    if denominator != DEFLECTION_LIMIT_DENOMINATOR:
        raise ValueError("This app uses the fixed L/360 deflection limit.")

    loads = raw.get("loads")
    if not isinstance(loads, dict):
        raise ValueError("The file is missing load data.")
    point_data = loads.get("point")
    uniform_data = loads.get("uniform")
    if not isinstance(point_data, list) or not isinstance(uniform_data, list):
        raise ValueError("Point and uniform loads must be lists.")

    points, normalized_points = [], []
    for item in point_data:
        if not isinstance(item, dict):
            raise ValueError("Each point load must be an object.")
        magnitude = _number(item.get("magnitude_kip"), "Point-load magnitude")
        position = _number(item.get("position_ft"), "Point-load position")
        direction = item.get("direction")
        if magnitude < 0 or direction not in ("Up", "Down"):
            raise ValueError("Point loads need a nonnegative magnitude and Up or Down direction.")
        points.append(PointLoad(magnitude if direction == "Up" else -magnitude, position))
        normalized_points.append({"magnitude_kip": magnitude, "direction": direction, "position_ft": position})

    uniforms, normalized_uniforms = [], []
    for item in uniform_data:
        if not isinstance(item, dict):
            raise ValueError("Each uniform load must be an object.")
        intensity = _number(item.get("intensity_kip_per_ft"), "Uniform-load intensity")
        start = _number(item.get("start_ft"), "Uniform-load start")
        end = _number(item.get("end_ft"), "Uniform-load end")
        direction = item.get("direction")
        if intensity < 0 or direction not in ("Up", "Down"):
            raise ValueError("Uniform loads need a nonnegative intensity and Up or Down direction.")
        uniforms.append(UniformLoad(intensity if direction == "Up" else -intensity, start, end))
        normalized_uniforms.append({
            "intensity_kip_per_ft": intensity, "direction": direction,
            "start_ft": start, "end_ft": end,
        })

    validate_inputs(span, points, uniforms)
    return {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "beam": {
            "support": support,
            "span_ft": span,
            "member": normalized_member,
            "deflection_limit": {"type": "span_ratio", "denominator": DEFLECTION_LIMIT_DENOMINATOR},
        },
        "loads": {"point": normalized_points, "uniform": normalized_uniforms},
    }


def save_config(path, config):
    """Validate and atomically write a configuration as UTF-8 JSON."""
    destination = Path(path)
    normalized = normalize_config(config)
    temporary_path = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8", newline="\n") as stream:
            json.dump(normalized, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def load_config(path):
    """Read and validate a Beam Designer JSON file."""
    try:
        with Path(path).open("r", encoding="utf-8") as stream:
            raw = json.load(stream)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}.") from None
    return normalize_config(raw)
