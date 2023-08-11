from datetime import datetime
from pathlib import Path
from rich import print

# from random import randrange
# from time import sleep

from imutils.perspective import four_point_transform
import imutils
import cv2
from pathlib import Path

# import os
import numpy as np


def start_datetime(func):
    def wrapper(*args, **kwargs):
        d = datetime.now()
        print(f" *** Start:  {d}")
        return func(*args, **kwargs)

    return wrapper


def end_datetime(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        d = datetime.now()
        print(f" *** End:  {d}")
        return result

    return wrapper


def dur_datetime(func):
    def wrapper(*args, **kwargs):
        d1 = datetime.now()
        print(f"\n *** Start:  {d1}")
        result = func(*args, **kwargs)
        d2 = datetime.now()
        diff = d2 - d1
        print(f" *** End:  {d2}, duration: {diff}")
        return result

    return wrapper


def cv_gamma(image, gamma: int):
    inBlack = np.array([0, 0, 0], dtype=np.float32)
    inWhite = np.array([255, 255, 255], dtype=np.float32)
    inGamma = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    outBlack = np.array([0, 0, 0], dtype=np.float32)
    outWhite = np.array([255, 255, 255], dtype=np.float32)
    inGamma = 1 / gamma
    img_g = image.copy()
    img_g = np.clip((img_g - inBlack) / (inWhite - inBlack), 0, 255)
    img_g = (img_g ** (1 / inGamma)) * (outWhite - outBlack) + outBlack
    image = np.clip(img_g, 0, 255).astype(np.uint8)
    return image


def cv_processing(
    img_file: Path,
    output: Path,
    image_rate: float = 1.294,
    debug: bool = False,
):
    #################################################################
    # Load the Image
    #################################################################
    input_file: str = str(img_file)
    output_file: str = str(output.joinpath(img_file.name))

    height = 800
    width = 600
    green = (0, 255, 0)
    image_geometry_rate = image_rate
    image_height_for_detection = 500

    image = cv2.imread(input_file)

    orig_image = image.copy()

    image = imutils.resize(image, height=image_height_for_detection)
    # image = cv2.resize(image, (0, 0), fx=scale, fy=scale)

    image = cv_gamma(image, 7)

    #################################################################
    # Image Processing
    #################################################################

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # convert the image to gray scale
    blur = cv2.GaussianBlur(gray, (5, 5), 0)  # Add Gaussian blur
    edged = cv2.Canny(blur, 75, 200)  # Apply the Canny algorithm to find the edges

    # Show the image and the edges
    if debug:
        cv2.imshow("Original image:", imutils.resize(image, height=500))
        cv2.imshow("Edged:", imutils.resize(edged, height=500))
        cv2.waitKey(5000)
        cv2.destroyAllWindows()

    # exit()

    #################################################################
    # Use the Edges to Find all the Contours
    #################################################################

    # If you are using OpenCV v3, v4-pre, or v4-alpha
    # cv.findContours returns a tuple with 3 element instead of 2
    # where the `contours` is the second one
    # In the version OpenCV v2.4, v4-beta, and v4-official
    # the function returns a tuple with 2 element
    contours, _ = cv2.findContours(edged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    if debug:
        # Show the image and all the contours
        cv2.imshow("Image", imutils.resize(image, height=500))
        cv2.drawContours(image, contours, -1, green, 3)
        cv2.imshow("All contours", imutils.resize(image, height=500))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    #################################################################
    # Select Only the Edges of the Document
    #################################################################

    # go through each contour
    for contour in contours:
        # we approximate the contour
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.01 * peri, True)
        # if we found a countour with 4 points we break the for loop
        # (we can assume that we have found our document)
        if len(approx) == 4:
            doc_cnts = approx
            break

    #################################################################
    # Apply Warp Perspective to Get the Top-Down View of the Document
    #################################################################
    coef_y = orig_image.shape[0] / image.shape[0]
    coef_x = orig_image.shape[1] / image.shape[1]

    for contour in doc_cnts:
        contour[:, 0] = contour[:, 0] * coef_y
        contour[:, 1] = contour[:, 1] * coef_x

    # We draw the contours on the original image not the modified one

    orig_image_c = cv2.drawContours(orig_image.copy(), [doc_cnts], -1, green, 30)

    if debug:
        cv2.imshow("Contours of the document", imutils.resize(orig_image_c, height=500))
        # apply warp perspective to get the top-down view

    warped = four_point_transform(orig_image, doc_cnts.reshape(4, 2))

    w = int(warped.shape[1])
    h = int(warped.shape[0])

    h = int(image_geometry_rate * w)

    warped = cv2.resize(warped, (w, h))

    # convert the warped image to grayscale
    # warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    print(f"Original image dimension: {orig_image.shape[1]} x {orig_image.shape[0]} ")
    print(f"Result   image dimension: {warped.shape[1]} x {warped.shape[0]} ")

    if debug:
        # cv2.imwrite("output" + "/" + os.path.basename(img_file), warped)
        cv2.imshow("Scanned", imutils.resize(warped, height=750))
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    cv2.imwrite(output_file, warped)


@dur_datetime
def im_scan(file_path: Path, output: Path, debug: bool = False):
    print(f"STILL FAKE. Just print :) {__package__}, im_scan {file_path}")
    size = file_path.stat().st_size
    modified = str(datetime.fromtimestamp(file_path.stat().st_mtime))
    print(f"{size=} bytes, {modified=}")
    cv_processing(file_path, output, debug=debug)
    # sleep(randrange(5, 40) / 10.0)
