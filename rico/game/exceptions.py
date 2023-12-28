class RuleError(Exception):
    """Error to signal a violation of the game's rules."""


def enforce(condition: bool, violation: str = "Some rule violation."):
    if not condition:
        raise RuleError(violation)
