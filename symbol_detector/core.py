from dataclasses import dataclass

import cv2.cv2 as cv2
import numpy as np

from symbol_detector.settings import Config


@dataclass
class FilterProperty:
    y_min: int
    y_max: int
    cb_min: int
    cb_max: int
    cr_min: int
    cr_max: int
    blur: int

    def load_from_settings(self, config: Config):
        for key in self.__dict__.keys():
            setattr(self, key, getattr(config, key))


async def compare_absolute_diff(gray_image, symbols, max_diff):
    """Absolute difference method"""
    diff_dict = {}
    for k in symbols.keys():
        for t in symbols[k]:
            im = t[0]
            sum_diff = float(np.sum(cv2.absdiff(im, gray_image)))
            rel_diff = 100.0 * sum_diff / max_diff
            diff_dict[rel_diff] = (k, im, rel_diff)
    diffs = list(diff_dict)
    diffs.sort()
    return diff_dict[diffs[0]]


async def compare_cos(gray_image, symbols):
    """Cosine method"""
    diff_dict = {}
    im0 = np.float32(gray_image)
    for k in symbols.keys():
        for t in symbols[k]:
            im1 = np.float32(t[0])
            rel_diff = 100.0 * (
                    1.0
                    - (
                            np.sum(im0 * im1)
                            / ((np.sum(im0 * im0) ** 0.5) * (np.sum(im1 * im1) ** 0.5))
                    )
            )
            diff_dict[rel_diff] = (k, t[0], rel_diff)
            # print((k, t[0], rel_diff))
    diffs = list(diff_dict)
    diffs.sort()
    print(diffs[0])
    return diff_dict[diffs[0]]


def my_contour(thresh):
    """ Returns those pixel's coordinates, which's value is not 0"""
    points = np.nonzero(thresh)
    positions = list()
    contours = list()
    for j in range(0, len(points[0])):
        y = int(points[0][j])
        x = int(points[1][j])
        positions.append(np.array([x, y]))
    positions_array = np.array(positions)
    contours.append(positions_array)
    return np.array(contours)


def resize_to_standard(thresh, size):
    contour = my_contour(thresh)
    x, y, w, h = cv2.boundingRect(contour)
    if w > h:
        d = int((w - h) / 2.0)
        im = np.zeros([w, w], np.uint8)
        im[d:h + d, :] = thresh[y: y + h, x: x + w]
    else:
        d = int((h - w) / 2.0)
        im = np.zeros([h, h], np.uint8)
        im[:, d:w + d] = thresh[y: y + h, x: x + w]
    return cv2.resize(im, (size, size), interpolation=cv2.INTER_LINEAR)


def ceil_blur(gray_image, b, cycles):
    """Applies maximum blur"""
    image = gray_image.copy()
    lookup_table = np.zeros(256, np.uint8)
    for i in range(cycles):
        image = cv2.blur(image, (b, b))
    maximum = 255.0 / np.amax(image)
    for i in range(256):
        lookup_table[i] = np.uint8(i * maximum)
    image = lookup_table[image]
    return image


async def filter_image(image, fp: FilterProperty):
    """Helps finding the pointer"""
    im = image.copy()
    im = cv2.blur(im, (fp.blur, fp.blur))
    im = cv2.cvtColor(im, cv2.COLOR_BGR2YCrCb)
    im = cv2.inRange(
        im,
        np.array([fp.y_min, fp.cr_min, fp.cb_min]),
        np.array([fp.y_max, fp.cr_max, fp.cb_max]),
    )
    mask = im > 0
    im = np.zeros([image.shape[0], image.shape[1], 1], np.uint8)
    im[:, :, 0] = 255 * mask
    im = cv2.blur(im, (7, 7))
    _, thresh = cv2.threshold(im, 10, 255, cv2.THRESH_BINARY)
    return cv2.flip(thresh, 1)


async def get_center(contour):
    (x, y), radius = cv2.minEnclosingCircle(contour)
    return [int(x), int(y)]


async def is_in_same_positions(points, n, max_distance):
    length = len(points)
    start = length - n
    for i in range(start, length):
        dist = await calc_dist_between_2_points(points[start], points[i])
        if dist > max_distance:
            return False
    return True


async def calc_dist_between_2_points(p0, p1):
    """ Calculates the distance between 2 points """
    x0 = float(p0[0])
    y0 = float(p0[1])
    x1 = float(p1[0])
    y1 = float(p1[1])
    return ((abs(x0 - x1)) ** 2 + (abs(y0 - y1)) ** 2) ** 0.5


def copy_drawing(thresh):
    cnt = my_contour(thresh)
    x, y, w, h = cv2.boundingRect(cnt)
    im = np.zeros([h, w], np.uint8)
    im[:, :] = thresh[y: y + h, x: x + w]
    return im


async def draw_lines(im, points, thickness):
    for i in range(0, len(points) - 1):
        cv2.line(im, tuple(points[i]), tuple(points[i + 1]), 255, thickness)
