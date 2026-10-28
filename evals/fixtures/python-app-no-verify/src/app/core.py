from dataclasses import dataclass


@dataclass(frozen=True)
class Greeting:
    name: str
    text: str


def greet(name: str) -> Greeting:
    clean = name.strip()
    if not clean:
        msg = "name must not be empty"
        raise ValueError(msg)
    return Greeting(name=clean, text=f"Hello, {clean}")
