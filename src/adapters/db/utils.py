import random
import string


def id_generator(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))
