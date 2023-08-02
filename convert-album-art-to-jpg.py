#!/usr/bin/env python3

# For parsing the commandline arguments
import argparse

import itertools

from shutil import copy as copyFile

# System file handling stuff
from os.path import dirname, join
from os.path import exists as fileExists

from PIL import Image as PILImage

import logging
from logger import applogger

WANTED_NAME = "cover"
WANTED_EXT = "jpg"
WANTED_FILENAME = f"{WANTED_NAME}.{WANTED_EXT}"

COMMON_ART_NAMES = [
    WANTED_NAME,
    "cover",
    "Cover",
    "COVER",
    "cover0",
    "folder",
    "Folder",
    "FOLDER",
    "album_art",
    "Album_art",
    "ALBUM_ART",
    "albumart",
    "Albumart",
    "AlbumArt",
    "ALBUMART",
    "jacket",
    "Jacket",
    "JACKET",
]
COMMON_ART_EXT = [
    WANTED_EXT,
    "jpg",
    "Jpg",
    "JPG",
    "jpeg",
    "JPEG",
    "Jpeg" "png",
    "Png",
    "PNG",
    "tif",
    "TIF",
    "Tif",
    "Tiff",
    "tiff",
    "TIFF",
    "bmp",
    "Bmp",
    "BMP",
]

ART_NAMES = [
    ".".join(combo) for combo in itertools.product(COMMON_ART_NAMES, COMMON_ART_EXT)
]

DEFAULT_RESIZE_DIM = 512


def resizeImageAndSave(
    imagePath,
    convertedName,
    saveDir,
    resizeDim=DEFAULT_RESIZE_DIM,
):
    image = PILImage.open(imagePath)
    image.thumbnail((resizeDim, resizeDim))
    fileName = join(saveDir, convertedName)
    applogger.debug("Trying to save the resized image...")
    try:
        image.save(fileName)
    # This is actually a KeyError that causes OSError
    except OSError as e:
        # This is probably because some art has transparency in it, and we're saving as JPG
        # Solution is: convert to without-transparency format
        # TODO: see how it converts, does it represent alpha as white?
        # if not, that's kinda shitty lol
        applogger.debug(f"Image mode is {image.mode}")
        if image.mode in ("RGBA", "P"):
            applogger.debug(
                "Image move is with transparency, trying to convert to RGB and save..."
            )
            image = image.convert("RGB")
            image.save(fileName)
        else:
            # If not alpha, that's something different, throw an error out
            applogger.error(
                f"Unhandled exception occured while saving the resized album art: {e}"
            )
            return None
    applogger.debug(f"Resized {imagePath} to {image.size} and saved as {fileName}.")
    return fileName


argparser = argparse.ArgumentParser()
argparser.add_argument("filename")
args = argparser.parse_args()
songPath = args.filename
songDir = dirname(songPath)
fullwantedname = join(songDir, WANTED_FILENAME)

applogger.debug(f"Got track {songPath} to work with.")

applogger.info("Checking if wanted name exists already...")
if fileExists(join(songDir, f"{WANTED_FILENAME}")):
    filenameBackup = f"{WANTED_NAME}-original.{WANTED_EXT}"
    applogger.info(
        f"{WANTED_FILENAME} already exists in {songDir}, copying to {filenameBackup}"
    )
    copyFile(fullwantedname, join(songDir, filenameBackup))

applogger.info("Checking for existing files...")
for filename in ART_NAMES:
    fullname = join(songDir, filename)
    if fileExists(fullname):
        applogger.info(f"Found it! {fullname}, converting to {fullwantedname}")
        if resizeImageAndSave(fullname, fullwantedname, songDir) is not None:
            applogger.info("Converted successfully!")
            exit(0)
        else:
            applogger.error("Something went wrong when converting file.")
            exit(-1)

logging.error("No suitable files found for conversion or copying.")
exit(-1)
