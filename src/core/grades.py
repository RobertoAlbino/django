GRADE_SCALE = [
    ("A+", 97, 100),
    ("A", 93, 96),
    ("A-", 90, 92),
    ("B+", 87, 89),
    ("B", 83, 86),
    ("B-", 80, 82),
    ("C+", 77, 79),
    ("C", 73, 76),
    ("C-", 70, 72),
    ("D", 60, 69),
    ("F", 0, 59),
]

_LETTER_TO_MAX = {letter: max_val for letter, _, max_val in GRADE_SCALE}


def value_to_letter(value):
    for letter, min_val, max_val in GRADE_SCALE:
        if min_val <= value <= max_val:
            return letter
    raise ValueError(f"Grade value {value} out of range 0-100")


def letter_to_value(letter):
    if letter not in _LETTER_TO_MAX:
        raise ValueError(f"Unknown letter grade: {letter}")
    return _LETTER_TO_MAX[letter]
