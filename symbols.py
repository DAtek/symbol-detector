import os

import core as cm
from core import cv2

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_next_nr(symbol_name, symbols):
    symbol_numbers = list()
    try:
        for symbol in symbols[symbol_name]:
            file_name = symbol[1]
            i = file_name.find("-")
            if file_name[:i] == symbol_name:
                symbol_numbers.append(int(file_name[i + 1 : -4]))
        symbol_numbers.sort()
        return symbol_numbers[len(symbol_numbers) - 1] + 1
    except KeyError:
        return 1


def read_symbols(directory, size):
    symbols = {}
    encoded_files = os.listdir(directory.encode("utf-8"))
    files = [str(file, "utf-8") for file in encoded_files]
    for file in files:
        i = file.find("-")
        key = file[:i]
        im0 = cv2.imread(os.path.join(BASE_DIR, directory, file))
        im = cv2.cvtColor(im0, cv2.COLOR_BGR2GRAY)
        im = cm.resize_to_standard(im, size)
        im = cm.ceil_blur(im, 15, 3)
        if not symbols.get(key):
            symbols[key] = list()
        symbols[key].append((im, file))
    return symbols
