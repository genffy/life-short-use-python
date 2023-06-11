import hashlib


def get_hash(string):
    return hashlib.sha256(string.encode("utf-8")).hexdigest()


def get_md5(string):
    return hashlib.md5(string.encode()).hexdigest()
