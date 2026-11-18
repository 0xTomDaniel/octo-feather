from dataclasses import dataclass


@dataclass(frozen=True)
class Greeting:
    name: str
    text: str


SHOUT_SUFFIX = "!"


def greet(name: str, *, shout: bool = False) -> Greeting:
    clean = name.strip()
    if not clean:
        msg = "name must not be empty"
        raise ValueError(msg)
    text = f"Hello, {clean}"
    if shout:
        text = text.upper() + SHOUT_SUFFIX
    return Greeting(name=clean, text=text)
