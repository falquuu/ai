"""Поиск совершенных чисел в заданном диапазоне.

Совершенное число — натуральное число, равное сумме всех своих
положительных делителей, исключая само число (6 = 1 + 2 + 3).

Алгоритм: сегментное решето сумм собственных делителей. Для каждого
d от 2 до isqrt(end) и каждого кратного m = d*q (q >= d) в диапазоне
к сумме делителей числа m прибавляются d и q (если q == d — только один раз).
Делитель 1 учитывается начальным значением. Память — O(длина диапазона).
"""

from __future__ import annotations

from array import array
from math import isqrt

MIN_START = 1
MAX_END = 10**12
MAX_SPAN = 5_000_000  # максимальная длина диапазона (≈ 40 МБ памяти)


class RangeError(ValueError):
    """Недопустимый диапазон поиска."""


def validate_range(start: int, end: int) -> tuple[int, int]:
    """Проверяет границы диапазона и возвращает их же."""
    for name, value in (("начало", start), ("конец", end)):
        if isinstance(value, bool) or not isinstance(value, int):
            raise RangeError(f"Граница диапазона ({name}) должна быть целым числом.")
    if start < MIN_START:
        raise RangeError(f"Начало диапазона должно быть не меньше {MIN_START}.")
    if end < start:
        raise RangeError("Конец диапазона не может быть меньше начала.")
    if end > MAX_END:
        raise RangeError(f"Конец диапазона не должен превышать {MAX_END}.")
    if end - start + 1 > MAX_SPAN:
        raise RangeError(
            f"Длина диапазона не должна превышать {MAX_SPAN} чисел "
            f"(задано {end - start + 1})."
        )
    return start, end


def divisor_sum(n: int) -> int:
    """Сумма положительных делителей n, исключая само n (перебор до √n)."""
    if n < 2:
        return 0
    total = 1
    for d in range(2, isqrt(n) + 1):
        if n % d == 0:
            total += d
            q = n // d
            if q != d:
                total += q
    return total


def is_perfect(n: int) -> bool:
    """Проверка одного числа."""
    return n > 1 and divisor_sum(n) == n


def divisor_sums(start: int, end: int) -> array:
    """Суммы собственных делителей для всех n из [start, end] (сегментное решето)."""
    validate_range(start, end)
    length = end - start + 1
    sums = array("Q", [1]) * length  # делитель 1 есть у каждого n > 1
    if start == 1:
        sums[0] = 0  # у числа 1 нет собственных делителей
    for d in range(2, isqrt(end) + 1):
        first = max(d * d, -(-start // d) * d)
        if first > end:
            continue
        for m in range(first, end + 1, d):
            sums[m - start] += d + m // d
        if first == d * d:
            sums[first - start] -= d  # при m = d*d делитель d посчитан дважды
    return sums


def find_perfect_numbers(start: int, end: int) -> list[int]:
    """Все совершенные числа из диапазона [start, end] в порядке возрастания."""
    sums = divisor_sums(start, end)
    return [start + i for i, s in enumerate(sums) if s == start + i]


def analyze(start: int, end: int) -> dict:
    """Результат сканирования числовой оси: границы, количество и сами числа."""
    numbers = find_perfect_numbers(start, end)
    return {"start": start, "end": end, "count": len(numbers), "numbers": numbers}
