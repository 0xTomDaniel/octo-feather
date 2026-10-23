from dataclasses import dataclass


@dataclass(frozen=True)
class Greeting:
    name: str
    text: str


def greet(name: str, *, shout: bool = False) -> Greeting:
    clean = name.strip()
    if not clean:
        msg = "name must not be empty"
        raise ValueError(msg)
    text = f"Hello, {clean}"
    return Greeting(name=clean, text=f"{text.upper()}!" if shout else text)
