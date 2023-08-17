from dataclasses import dataclass
import re


@dataclass
class Pseudo:
    full_name: str
    relevance: dict
    major: str
    minor: str
    avoid: set

    def __init__(self, full_name, avoid=set()):
        self.full_name = full_name.strip()
        full_name = str(' ').join(split_on_whitespace_and_case(full_name))
        self.relevance = get_relevance(full_name)
        self.avoid = avoid
        if self.full_name[0].isalpha():
            self.major = self.full_name[0].upper()
            self.minor, _ = min(
                [
                    (char, value)
                    for char, value in self.relevance.items()
                    if char not in self.avoid and value > 0
                ],
                key=lambda t: t[1],
                default=("@", 70)
            )
        else:
            self.major = "#"
            self.minor = "@"
    
    def __hash__(self):
        return hash(self.full_name)

    def __repr__(self):
        return f"{self.full_name} >> {self.major}{self.minor} (avoiding {self.avoid})"

    def avoiding(self, minors: set[str]) -> "Pseudo":
        return Pseudo(self.full_name, avoid = self.avoid | minors)

def split_on_whitespace_and_case(text):
    return re.findall(r'[A-Z](?:[a-z]+)?|[A-Z]+(?=[A-Z]|$)|[a-z]+(?=[A-Z]|$)|[\w]+', text)

def get_relevance(name: str) -> dict[str, int]:
    relevance_dict = {}
    for i, part in enumerate(split_on_whitespace_and_case(name)):
        for j, char in enumerate(part.capitalize()):
            if char.isalpha():
                relevance_dict[char] = min(
                    i + j + int(char.islower()), relevance_dict.get(char, 77)
                )
    return relevance_dict


def generate_pseudos(usernames: list[str]) -> dict[str, Pseudo]:
    pseudos = {name: Pseudo(name) for name in usernames}
    groups = dict()
    for ps in pseudos.values():
        major = ps.major
        if major in groups:
            groups[major].add(ps)
        else:
            groups[major] = {ps}
    distinct_groups = [(stage_two(group) if len(group) > 1 else group) for group in groups.values()]
    pseudos = stage_three({ps for group in distinct_groups for ps in group})

    return pseudos

def stage_two(group: set[Pseudo]) -> set[Pseudo]:
    avoiding = set()
    collisions = True
    while collisions:
        print(group)
        collisions = False
        used_minors = {ps.minor for ps in group}
        subgroups = { minor: {ps for ps in group if ps.minor == minor} for minor in used_minors}
        group = set()
        for minor, subgroup in subgroups.items():
            if len(subgroup) > 1 and minor != "@":
                print("Collision in", subgroup)
                collisions = True
                avoiding.add(minor)
                group = group | { ps.avoiding(used_minors | avoiding) for ps in subgroup}
            else:
                group = group | subgroup
    return group

def stage_three(group: set[Pseudo]) -> set[Pseudo]:
    pseudos = dict()
    for i, ps in enumerate(group):
        if ps.minor == "@":
            pseudos[ps.full_name] = ps.major + str(i+1)
        else:
            pseudos[ps.full_name] = ps.major + ps.minor
    return pseudos


if __name__ == "__main__":
    # Example usage:
    usernames = [
        "Marco",
        "Matteo",
        "Martina",
        "Andrea",
        "John Adams",
    ]
    print(generate_pseudos(usernames))
