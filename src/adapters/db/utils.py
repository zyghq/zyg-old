import random
import string


def generate_id(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))
