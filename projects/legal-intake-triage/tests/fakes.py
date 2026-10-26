"""Fictional Brazilian identifiers with valid check digits, for tests only."""


def _digit(numbers: str, weights: list[int]) -> str:
    rest = sum(int(n) * w for n, w in zip(numbers, weights)) % 11
    return "0" if rest < 2 else str(11 - rest)


def cpf(base: str = "529982247") -> str:
    d1 = _digit(base, list(range(10, 1, -1)))
    d2 = _digit(base + d1, list(range(11, 1, -1)))
    n = base + d1 + d2
    return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"


def cnpj(base: str = "112223330001") -> str:
    d1 = _digit(base, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _digit(base + d1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    n = base + d1 + d2
    return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"
