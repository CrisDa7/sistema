"""Utilidades compartidas para pruebas de Active Gym."""

from itertools import count


def generate_valid_cedula(seed: int) -> str:
    """Genera una cédula ecuatoriana válida a partir de una semilla."""
    base_digits = f"17{seed:07d}"
    digits = [int(digit) for digit in base_digits[:9]]
    coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0

    for digit, coefficient in zip(digits, coefficients):
        result = digit * coefficient
        if result >= 10:
            result -= 9
        total += result

    verification_digit = (10 - total % 10) % 10
    return base_digits + str(verification_digit)


class CedulaGenerator:
    """Generador de cédulas únicas para pruebas."""

    def __init__(self, start_seed: int = 1000):
        self._counter = count(start_seed)
        self._generated = set()

    def next(self) -> str:
        """Genera la siguiente cédula única."""
        while True:
            seed = next(self._counter)
            cedula = generate_valid_cedula(seed)
            if cedula not in self._generated:
                self._generated.add(cedula)
                return cedula
