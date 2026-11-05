"""Test doubles shared across test files."""

from privacyseed_lgpd.entity import Entity, Result


def entity(text: str, sub: str, label: str) -> Entity:
    start = text.index(sub)
    return Entity(label, sub, start, start + len(sub), 0.9, "fake", "personal")


class FakeDetector:
    """Returns canned entities for whatever text it gets; records the inputs."""

    def __init__(self, entities_for=lambda text: ()):
        self.entities_for = entities_for
        self.inputs: list[str] = []

    def analyze(self, text: str) -> Result:
        self.inputs.append(text)
        return Result(anonymized="", entities=tuple(self.entities_for(text)))
