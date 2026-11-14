from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    name: str
    text: str


def _clean(name: str) -> str:
    clean = name.strip()
    if not clean:
        msg = "name must not be empty"
        raise ValueError(msg)
    return clean


def greet(name: str) -> Message:
    clean = _clean(name)
    return Message(name=clean, text=f"Hello, {clean}")


def farewell(name: str) -> Message:
    clean = _clean(name)
    return Message(name=clean, text=f"Goodbye, {clean}")
