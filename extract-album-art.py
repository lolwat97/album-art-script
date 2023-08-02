#!/usr/bin/env python3

# For parsing the commandline arguments
import argparse

import itertools

# System file handling stuff
from os.path import dirname, join
from os.path import exists as fileExists
from os.path import splitext as fileExtension

# Tag manipulating magic lib
from mutagen import File as MutagenFile
from mutagen.id3 import APIC, ID3
from mutagen.id3._util import ID3NoHeaderError
from mutagen.oggvorbis import OggVorbis

# from mutagen.flac import FLAC
from mutagen.flac import Picture as MutagenFLACPicture

# Needed for ogg album art
import base64

# For album art resizing
from PIL import Image as PILImage
from io import BytesIO

# Logging setup has been offloaded to a separate module, logger.py
# applogger is the logger to call, defined in logger.py
import logging
from logger import applogger


COMMON_ART_NAME_MAIN = [
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
]
COMMON_ART_NAME_EXT = ["jpg", "Jpg", "jpeg", "Jpeg", "JPG", "JPEG", "png", "Png", "PNG"]
COMMON_ART_NAMES = [
    ".".join(combo)
    for combo in itertools.product(COMMON_ART_NAME_MAIN, COMMON_ART_NAME_EXT)
]
DEFAULT_SAVE_NAME = "cover.jpg"

argparser = argparse.ArgumentParser()
argparser.add_argument("filename")
args = argparse.parse_args()

applogger.debug(f"Args are {args}")

songPath = args.filename
songDir = dirname(songPath)

applogger.debug(f"Got {songPath} to work with.")


def extractImageFromMP3(filename, saveName, saveDir):
    try:
        trackTags = ID3(filename)
    except ID3NoHeaderError:
        applogger.error("No ID3 tags in this file!")
        return None
    trackPicture = trackTags.get("APIC:").data
    if trackPicture is not None:
        image = PILImage.open(BytesIO(trackPicture))
        imageName = join(saveDir, saveName)
        image.save(imageName)
        return imageName
    else:
        applogger.error("No APIC tag in this file!")


def extractImageFromOGG(filename, saveName, saveDir):
    return None


def extractImageFromTrack(filename, saveName, saveDir):
    if fileExtension(filename).lower().strip(".") == "mp3":
        return extractImageFromMP3(filename, saveDir)
    return None


for commonName in COMMON_ART_NAMES:
    if not fileExists(join(songDir, commonName)):
        extractImageFromTrack(songPath, DEFAULT_SAVE_NAME, songDir)
