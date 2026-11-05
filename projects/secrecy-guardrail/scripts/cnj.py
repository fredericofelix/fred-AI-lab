"""Print a synthetic CNJ number with a valid check digit: python -m scripts.cnj 0001234 2025 8 13 0024"""

import sys

from guardrail.deterministic import check_digit

if __name__ == "__main__":
    n, year, segment, court, origin = sys.argv[1:6]
    print(f"{n}-{check_digit(n, year, segment, court, origin):02d}.{year}.{segment}.{court}.{origin}")
