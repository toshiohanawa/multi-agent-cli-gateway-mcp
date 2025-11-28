"""
FizzBuzz implementation in Python.

Running this module will print the sequence from 1 to 100. The core logic is
exposed via `fizzbuzz` for reuse and testing.
"""

from typing import List


def fizzbuzz(limit: int = 100) -> List[str]:
    """
    Generate the FizzBuzz sequence from 1 to `limit`.

    - Multiples of 3 become "Fizz"
    - Multiples of 5 become "Buzz"
    - Multiples of both 3 and 5 become "FizzBuzz"
    - All other numbers are returned as their string form
    """
    result: List[str] = []

    # Avoids repeated modulo operations by tracking countdowns to the next hits.
    next_three, next_five = 3, 5

    for number in range(1, limit + 1):
        entry = ""
        next_three -= 1
        next_five -= 1

        if next_three == 0:
            entry += "Fizz"
            next_three = 3
        if next_five == 0:
            entry += "Buzz"
            next_five = 5

        if not entry:
            entry = str(number)

        result.append(entry)

    return result


if __name__ == "__main__":
    for item in fizzbuzz():
        print(item)
