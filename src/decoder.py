""" Decoding functions """

from datetime import datetime


def datetime_decoder(dct: dict):
    """Convert all datetime values in a dict to a string"""
    for key, value in dct.items():
        if isinstance(value, str):
            try:
                dct[key] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            except ValueError:
                pass
    return dct
