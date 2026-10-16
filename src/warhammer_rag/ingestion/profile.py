"""Reviewed layout information for the supplied edition of Core Rules.

Coordinates use PDF points from the top-left corner. The parser checks the
source digest before applying these edition-specific transcriptions.
"""

SOURCE_SHA256 = "4d0e8019cbfddd6f46781d5b4ed31d46fb21eb2d0d10a0f6fabefac0ce054364"

SECTIONS = [
    (1, 2, "Cover"),
    (3, 4, "Introduction"),
    (5, 9, "Core concepts"),
    (10, 10, "Battle round"),
    (11, 12, "Command phase"),
    (13, 16, "Movement phase"),
    (17, 18, "Transports"),
    (19, 20, "Shooting phase"),
    (21, 24, "Making attacks"),
    (25, 28, "Weapon abilities"),
    (29, 31, "Charge phase"),
    (32, 36, "Fight phase"),
    (37, 38, "Datasheets"),
    (39, 40, "Unit abilities"),
    (41, 42, "Stratagems"),
    (43, 43, "Strategic reserves"),
    (44, 52, "Terrain"),
    (53, 54, "Aircraft"),
    (55, 56, "Muster your army"),
    (57, 58, "Missions and objectives"),
    (59, 60, "Only War mission"),
]

# Tables with graphic cells, or cells whose associations are lost in plain text.
TABLES = {
    9: (
        (306, 182, 529, 303),
        "Rolling a D3",
        ["D6 result", "D3 result"],
        [["1–2", "1"], ["3–4", "2"], ["5–6", "3"]],
    ),
    21: (
        (306, 490, 529, 686),
        "Wound roll",
        ["Strength (S) vs Toughness (T)", "Required roll"],
        [
            ["S ≥ 2T", "2+"],
            ["T < S < 2T", "3+"],
            ["S = T", "4+"],
            ["T/2 < S < T", "5+"],
            ["S ≤ T/2", "6+"],
        ],
    ),
    59: (
        (344, 240, 532, 314),
        "Battlefields",
        ["Battle size", "Minimum battlefield size"],
        [["Incursion/Strike Force", '44" × 60"'], ["Onslaught", '44" × 90"']],
    ),
}

# Text regions exclude the cost badge, which is recorded as a separate field.
CARDS = {
    41: [
        ("COMMAND RE-ROLL", 1, (179, 430, 337, 561)),
        ("COUNTER-OFFENSIVE", 2, (373, 430, 532, 555)),
        ("EPIC CHALLENGE", 1, (373, 563, 532, 687)),
    ],
    42: [
        ("INSANE BRAVERY", 1, (111, 61, 270, 203)),
        ("GRENADE", 1, (111, 211, 270, 353)),
        ("TANK SHOCK", 1, (111, 361, 270, 521)),
        ("RAPID INGRESS", 1, (111, 529, 270, 674)),
        ("FIRE OVERWATCH", 1, (305, 61, 465, 251)),
        ("GO TO GROUND", 1, (305, 259, 465, 392)),
        ("SMOKESCREEN", 1, (305, 400, 465, 533)),
        ("HEROIC INTERVENTION", 2, (305, 541, 465, 722)),
    ],
}

VISUAL_NOTES = {
    37: "Illustrative datasheet only; its example profiles are not live unit statistics.",
    60: (
        "Only War deployment diagram: opposing deployment zones end 12 inches "
        "from the battlefield centre line on each side, leaving a 24-inch gap."
    ),
}
