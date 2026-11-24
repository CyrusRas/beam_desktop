"""Reference member properties for the preliminary Beam Designer model.

Properties use US customary units: S in in^3, I in in^4, E and Fb in ksi.
Wood values are unadjusted reference values; this app does not apply NDS
adjustment factors. Steel bending allowables use the stated educational ASD
approximation Fb = 0.66 Fy and are not a complete AISC design check.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Member:
    label: str
    section_modulus: float
    inertia: float
    elastic_modulus: float
    allowable_bending: float
    note: str


STEEL = {
    "W12x26": {"S": 33.4, "I": 204.0},
    "W10x22": {"S": 23.2, "I": 118.0},
    "W14x30": {"S": 42.0, "I": 291.0},
}
STEEL_GRADES = {"ASTM A992": 50.0, "ASTM A36": 36.0}

# Actual dressed dimensions in inches. Values are section geometry only.
LUMBER_SIZES = {"2x10": (1.5, 9.25), "2x12": (1.5, 11.25), "4x8": (3.5, 7.25)}

# Reference No. 2 values, ksi, used as educational baseline values for each
# listed species. They are not size-adjusted for the selected lumber width;
# duration, wet-service, and other NDS adjustments are outside this app.
# Steel section properties are from the
# AISC Shapes Database v16.0; wood values refer to AWC NDS Supplement tables
# for visually graded dimension lumber (Table 4A/4B). The included values are
# a compact reference subset, not a full reproduction of either database.
WOOD = {
    "Douglas Fir-Larch No. 2": {"Fb": 0.90, "E": 1600.0},
    "Southern Pine No. 2": {"Fb": 1.10, "E": 1400.0},
}


def get_member(kind: str, shape: str, grade: str, species: str, size: str) -> Member:
    if kind == "Steel W-shape":
        props = STEEL[shape]
        fy = STEEL_GRADES[grade]
        return Member(
            f"{shape} steel · {grade}", props["S"], props["I"], 29000.0,
            0.66 * fy,
            f"AISC section properties; Fb = 0.66 Fy educational approximation (Fy = {fy:g} ksi)",
        )
    b, d = LUMBER_SIZES[size]
    props = WOOD[species]
    return Member(
        f"{size} {species}", b * d**2 / 6.0, b * d**3 / 12.0,
        props["E"], props["Fb"],
        f"Actual dimensions {b:g} × {d:g} in; baseline No. 2 Fb and E (no size adjustment)",
    )
