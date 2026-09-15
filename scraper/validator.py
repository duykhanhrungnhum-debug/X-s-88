from collections.abc import Mapping


# Basic structural validation only. Source-specific rules belong in adapters.
def validate_prizes(prizes: Mapping[str, list[str]]) -> bool:
    if not prizes:
        return False
    return all(
        isinstance(label, str)
        and isinstance(numbers, list)
        and bool(numbers)
        and all(isinstance(number, str) and number.isdigit() for number in numbers)
        for label, numbers in prizes.items()
    )
