#!/usr/bin/env python3

# For parsing the commandline arguements
import argparse

# System file handling stuff
from os.path import dirname, join
from os.path import exists as fileExists
from os.path import splitext as fileExtension

# For copying user-selected album art as a standard cover files
# For example, to not ask for future track files for this album
from shutil import copy as copyFile

# Only for the file dialog, basically
import tkinter as tk
from tkinter import filedialog as tkFileDialog

# Tag manipulating magic lib
from mutagen import File as MutagenFile
from mutagen.id3 import APIC, ID3
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.flac import Picture as MutagenFLACPicture

# Needed for ogg album art
import base64

# Logging setup has been offloaded to a separate module, logger.py
# applogger is the logger to call, defined in logger.py
from logger import applogger


COMMON_ART_NAMES = ["cover.jpg", "cover.png", "folder.jpg", "folder.png"]
MIME_TYPES = {"jpg": "image/jpg", "png": "image/png"}


def addAlbumArtToSong(songPath, imagePath, imageMimeType):
    songExt = fileExtension(songPath)[1].lower().strip(".")

    if songExt == "mp3":
        return addAlbumArtToMP3(songPath, imagePath, imageMimeType)
    elif songExt == "ogg":
        return addAlbumArtToOGG(songPath, imagePath, imageMimeType)
    # elif songExt == "flac":
    #     return addAlbumArtToFLAC(songPath, imagePath, imageMimeType)
    else:
        applogger.error(
            f"File type {songExt} is not supported for track {songPath}, exiting..."
        )
        return -1


def addAlbumArtToMP3(songPath, imagePath, imageMimeType):
    applogger.debug(
        f"Adding {imageMimeType} album art to MP3 file {songPath}: {imagePath}"
    )

    songFile = ID3("music_file.mp3")

    with open("img.jpg", "rb") as albumart:
        # Encoding = 3 is Encoding.UTF8, type = 3 is PictureType.COVER_FRONT
        songFile["APIC"] = APIC(
            encoding=3, mime=imageMimeType, type=3, desc="Cover", data=albumart.read()
        )

    songFile.save()
    return 0


def addAlbumArtToOGG(songPath, imagePath, imageMimeType):
    applogger.debug(
        f"Adding {imageMimeType} album art to OGG file {songPath}: {imagePath}"
    )

    songFile = OggVorbis(songPath)

    # Open the picture file and read the picture data
    with open(imagePath, "rb") as f:
        imageData = f.read()

    image = MutagenFLACPicture()
    image.data = imageData
    image.type = 3  # 3 is for album art
    image.mime = imageMimeType
    image.desc = "Cover"

    # Convert the picture to FLAC format and add it to the Ogg file's metadata
    songFile["metadata_block_picture"] = [
        base64.b64encode(image.write()).decode("ascii")
    ]

    # Save the Ogg file with the new metadata
    songFile.save()
    return 0


# TODO: implement FLAC, also see addAlbumArtToSong()
#
# def addAlbumArtToFLAC(songPath, imagePath, imageMimeType):
#     applogger.debug(
#         f"Adding {imageMimeType} album art to FLAC file {songPath}: {imagePath}"
#     )
#     audio = File(filename)

#     image = Picture()
#     image.type = 3
#     if albumart.endswith('png'):
#         mime = 'image/png'
#     else:
#         mime = 'image/jpeg'
#     image.desc = 'front cover'
#     with open(albumart, 'rb') as f:
#         image.data = f.read()

#     audio.add_picture(image)
#     audio.save()


def checkExistingAlbumArt(songPath):
    applogger.debug(f"Opening {songPath} with Mutagen...")
    song = MutagenFile(songPath)
    # For MP3 files
    if "APIC:" in song:
        return True

    # For OGG files
    if "metadata_block_picture" in song:
        return True

    # For OPUS files
    if hasattr(song, "pictures") and song.pictures:
        return True

    applogger.debug(f"Album art not found inside track {songPath}")
    return False


def parseArguments():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("filename")
    argparser.add_argument("--edit-all", "-a", action="store_true")
    argparser.add_argument("--copy-cover", "-c", action="store_true")
    args = argparser.parse_args()
    return args


def checkForCommonAlbumArtNames(songPath, albumArtNames=COMMON_ART_NAMES):
    applogger.debug("Checking for usual album art filenames")
    for commonName in albumArtNames:
        possibleName = join(dirname(songPath), commonName)
        applogger.debug(f"Checking if {possibleName} exists...")
        if fileExists(possibleName):
            applogger.debug(f"Found it! {possibleName}")
            return possibleName, True
    applogger.debug("Couldn't find anything.")
    return None, False


def app():
    args = parseArguments()

    songPath = args.filename
    songDir = dirname(songPath)
    applogger.debug(f"Track full path is {songPath}")
    applogger.debug(f"Track dir is {songDir}")

    if not fileExists(songPath):
        applogger.error(f"File does not exist: {songPath}, exiting...")
        return -1

    albumArtExistsInTrack = checkExistingAlbumArt(songPath)

    if (not albumArtExistsInTrack) or args.edit_all:
        imagePath, commonNameFoundFlag = checkForCommonAlbumArtNames(songPath)
        if imagePath is None:
            applogger.warning(
                f"Art for {songPath} not found automatically, calling tkFileDialog..."
            )

            tkRoot = tk.Tk()
            tkRoot.withdraw()
            imagePath = tkFileDialog.askopenfilename(initialdir=songDir)
            applogger.debug(f"Got {imagePath} from the user.")

        if imagePath is None:
            applogger.error(f"No art selected for {songPath}, exiting...")
            return -1
        if not fileExists(imagePath):
            applogger.error(f"Album art file does not exist: {imagePath}, exiting...")
            return -1

        imageExt = fileExtension(imagePath)[1].lower().strip(".")
        applogger.debug(f'Seems like {imagePath} exists, file ext is "{imageExt}"')

        if imageExt not in MIME_TYPES.keys():
            applogger.error(f"Image {imagePath} is not of supported type! Aborting...")
            return -1
        else:
            imageMimeType = MIME_TYPES[imageExt]
            applogger.debug(f"Image file MIME type is {imageMimeType}")

        if args.copy_cover and not commonNameFoundFlag:
            applogger.info(f"Copying {imagePath} to track dir as cover.{imageExt}")
            copyFile(imagePath, join(songDir, f"cover.{imageExt}"))

        applogger.info(
            f"Adding album art to: {songPath}"
            if not albumArtExistsInTrack
            else f"Changing album art for: {songPath}"
        )

        if addAlbumArtToSong(songPath, imagePath, imageMimeType):
            applogger.error(f"Something went wrong when adding art to file {songPath}")
            return -1

        return 0

    else:
        applogger.info(f"File already has an album art: {songPath}")
        return 0


app()
