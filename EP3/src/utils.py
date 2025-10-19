import math
import urllib.parse

from typing import List


def encode(value: str) -> str:
    return urllib.parse.quote(value)


def decode(value: str) -> str:
    return urllib.parse.unquote(value)


def draw_row(values: list[str | int], widths: list[int]) -> str:
    return " | ".join(f"{str(v):<{w}}" for v, w in zip(values, widths))


def standard_deviation(values: List[int]) -> float:
    n = len(values)
    if n == 0:
        return 0.0

    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = math.sqrt(variance)

    return std_dev
