import secrets
import string


def generate_temporary_password(length: int = 10) -> str:

    characters = (
        string.ascii_letters
        + string.digits
        + "!@#$%"
    )

    return "".join(
        secrets.choice(characters)
        for _ in range(length)
    )