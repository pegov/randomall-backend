import random
from string import ascii_lowercase, digits


def create_random_string(n: int) -> str:
    """
    lowercase ascii and digits
    """
    letters = "".join([ascii_lowercase, digits])
    return "".join([random.choice(letters) for _ in range(n)])
