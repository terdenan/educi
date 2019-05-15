import random
import string

SYMBOLS_COUNT = 8


def random_temporary_dir(instance, filename):
    """Generates random path for storing submission sources before
    it can be moved to proper directory regarding its `id`
    """
    random_symbols = ''.join(random.choice(string.ascii_lowercase) for _ in range(SYMBOLS_COUNT))
    tmp_dir_path = f"tmp/tmp_{random_symbols}/{filename}"

    return tmp_dir_path
