#!/usr/bin/env python3
import os

from PIL import Image

curdir = os.path.dirname(__file__)
patterns_dir = os.path.normpath(os.path.join(curdir, "../intranet/static/img/patterns"))


def make_dark(fname, out_fname):
    img = Image.open(fname)
    img = img.convert("RGB")

    pixels = list(img.getdata())

    for i in range(len(pixels)):
        r, g, b = pixels[i]

        r, g, b = map(lambda i: int(255 - i * 0.95), (r, g, b))

        pixels[i] = (r, g, b)

    img.putdata(pixels)
    img.save(out_fname, "PNG")


if __name__ == "__main__":
    for fname in os.listdir(patterns_dir):
        if os.path.isfile(os.path.join(patterns_dir, fname)) and fname.endswith(".png"):
            make_dark(os.path.join(patterns_dir, fname), os.path.join(patterns_dir, "dark", fname))
