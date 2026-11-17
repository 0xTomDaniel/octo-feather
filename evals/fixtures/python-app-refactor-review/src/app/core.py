from dataclasses import dataclass


@dataclass(frozen=True)
class Greeting:
    name: str
    text: str


@dataclass(frozen=True)
class Farewell:
    name: str
    text: str


def greet(name: str) -> Greeting:
    clean = name.strip()
    if not clean:
        msg = "name must not be empty"
        raise ValueError(msg)
    return Greeting(name=clean, text=f"Hello, {clean}")


def farewell(name: str) -> Farewell:
    trimmed = name.strip()
    if len(trimmed) == 0:
        error = "name must not be empty"
        raise ValueError(error)
    text = "Goodbye, " + trimmed
    return Farewell(name=trimmed, text=text)
