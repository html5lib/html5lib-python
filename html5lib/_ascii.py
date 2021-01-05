from .constants import asciiUpper2Lower


def ascii_lower(s):
    return s.translate(asciiUpper2Lower)
