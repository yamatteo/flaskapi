from dataclasses import dataclass
import re


@dataclass
class Pseudo:
    name: str  # Original name
    relevance: dict[str, int]  # Relevance of chars occuring in the name
    major: str  # First char of the pseudo
    minor: str  # Second char of the pseudo
    avoid: set  # Excluded chars to avoid collision, used during construction

    def __init__(self, name, avoid=None):
        self.name = name = name.strip()
        self.relevance = get_relevance(name)
        self.avoid = set() if avoid is None else avoid
        if name[0].isalpha():
            self.major = name[0].upper()
            # Take the minor with the best (the lowest) relevance avoiding chars in collisions.
            self.minor, _ = min(
                [
                    (char, value)
                    for char, value in self.relevance.items()
                    if char not in self.avoid and value > 0
                ],
                key=lambda t: t[1],
                default=("@", 70),
            )
        else:
            self.major = "#"  # Generic major when the procedure fails
            self.minor = "@"  # Placeholder to be replaced with a number

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"{self.name} >> {self.major}{self.minor} (avoiding {self.avoid})"

    def avoiding(self, minors: set[str]) -> "Pseudo":
        return Pseudo(self.name, avoid=self.avoid | minors)

class BiDict(dict):
    def __init__(self, data: dict):
        self.update(data)
        self.inverse = {value: key for (key, value) in self.items()}
    
    def invget(self, value):
        return self.inverse.get(value)

def split_on_whitespace_and_case(text: str) -> list[str]:
    """Split text into words based on uppercase and lowercase letters."""
    pattern = r"""
        [A-Z](?![A-Z])         # Match a single uppercase letter
        (?:[a-z]+)?            # Optionally match one or more lowercase letters
        |                      # OR
        [A-Z]+                 # Match one or more consecutive uppercase letters
        (?=[A-Z]|$)            # Followed by either another uppercase letter or end of string
        |                      # OR
        [a-z]+                 # Match one or more consecutive lowercase letters
        (?=[A-Z]|$)            # Followed by either an uppercase letter or end of string
        |                      # OR
        [\w]+                  # Match one or more word characters (letters, digits, or underscores)
    """
    return re.findall(pattern, text, re.VERBOSE)


def get_relevance(name: str) -> dict[str, int]:
    parts = [part.capitalize() for part in split_on_whitespace_and_case(name)]
    chars = {char for part in parts for char in part}
    return {
        char: min(
            (
                i + part.index(char) + int(char.islower())
                for i, part in enumerate(parts)
                if char in part and (i + part.index(char) > 0)
                # This exclude the major, giving it relevance 777 by default
            ),
            default=777,
        )
        for char in chars
    }


def generate_pseudos(usernames: list[str]) -> dict[str, str]:
    pseudos = {Pseudo(name) for name in usernames}
    majors = {ps.major for ps in pseudos}
    groups = [
        avoid_collisions({ps for ps in pseudos if ps.major == major})
        for major in majors
    ]
    data = fix_undefined_minors({ps for group in groups for ps in group})
    return BiDict(data)


def avoid_collisions(group: set[Pseudo]) -> set[Pseudo]:
    avoiding = set()
    collisions = True
    while collisions:
        # print(group)
        collisions = False
        used_minors = {ps.minor for ps in group}
        subgroups = {
            minor: {ps for ps in group if ps.minor == minor} for minor in used_minors
        }
        group = set()
        for minor, subgroup in subgroups.items():
            if len(subgroup) > 1 and minor != "@":
                # print("Collision in", subgroup)
                collisions = True
                avoiding.add(minor)
                group = group | {ps.avoiding(used_minors | avoiding) for ps in subgroup}
            else:
                group = group | subgroup
    return group


def fix_undefined_minors(group: set[Pseudo]) -> dict[str, str]:
    pseudos = dict()
    for i, ps in enumerate(group):
        if ps.minor == "@":
            pseudos[ps.name] = ps.major + str(i + 1)
        else:
            pseudos[ps.name] = ps.major + ps.minor
    return pseudos


def test_pseudos():
    usernames = [
        "Marco",
        "Matteo",
        "Martina",
        "Andrea",
        "John Adams",
        "MacArthur",
        "Carlo Carli",
    ]
    assert generate_pseudos(usernames) == {
        "Marco": "Mc",
        "Matteo": "Mt",
        "Martina": "Mi",
        "Andrea": "An",
        "John Adams": "JA",
        "MacArthur": "MA",
        "Carlo Carli": "CC",
    }
    assert generate_pseudos(usernames).invget("Mt") == "Matteo"


def test_split():
    assert split_on_whitespace_and_case("John") == ["John"]
    assert split_on_whitespace_and_case("John Miller") == ["John", "Miller"]
    assert split_on_whitespace_and_case("JohnAdams") == ["John", "Adams"]
    assert split_on_whitespace_and_case("JohnJONES") == ["John", "JONES"]
    assert split_on_whitespace_and_case("BadNAMEJohn36") == [
        "Bad",
        "NAME",
        "John",
        "36",
    ]
    assert split_on_whitespace_and_case("EdgarAPoe") == ["Edgar", "A", "Poe"]
