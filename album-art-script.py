#!/usr/bin/env python3

# For parsing the commandline arguments
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


COMMON_ART_NAMES = ["cover.jpg", "cover.png", "folder.jpg", "folder.png", "Cover.jpg", 'Cover.png', "Folder.jpg", "Folder.png", "album_art.jpg", "album_art.png"]
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

    songFile = ID3(songPath)

    with open(imagePath, "rb") as imageFile:
        # Encoding = 3 is Encoding.UTF8, type = 3 is PictureType.COVER_FRONT
        songFile["APIC"] = APIC(
            encoding=3, mime=imageMimeType, type=3, desc="Cover", data=imageFile.read()
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
    # For MP3 files TODO: This doesn't work for some reason, pls fix
    # album-art-script - DEBUG - Track full path is /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/10 Caramell - Caramelldansen (speedycake).mp3 (album-art-script.py:167)
    # album-art-script - DEBUG - Track dir is /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2 (album-art-script.py:168)
    # album-art-script - DEBUG - Opening /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/10 Caramell - Caramelldansen (speedycake).mp3 with Mutagen... (album-art-script.py:121)
    # album-art-script - DEBUG - Album art not found inside track /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/10 Caramell - Caramelldansen (speedycake).mp3 (album-art-script.py:135)
    # album-art-script - DEBUG - Checking for usual album art filenames (album-art-script.py:151)
    # album-art-script - DEBUG - Checking if /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/cover.jpg exists... (album-art-script.py:154)
    # album-art-script - DEBUG - Checking if /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/cover.png exists... (album-art-script.py:154)
    # album-art-script - DEBUG - Found it! /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/cover.png (album-art-script.py:156)
    # album-art-script - DEBUG - Seems like /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/cover.png exists, file ext is "png" (album-art-script.py:196)
    # album-art-script - DEBUG - Image file MIME type is image/png (album-art-script.py:203)
    # album-art-script - INFO - Adding album art to: /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/10 Caramell - Caramelldansen (speedycake).mp3 (album-art-script.py:209)
    # album-art-script - DEBUG - Adding image/png album art to MP3 file /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/10 Caramell - Caramelldansen (speedycake).mp3: /home/lw/Music/music_ogg/2ch ost/Vol 1/CD2/cover.png (album-art-script.py:55)

    if "APIC:" in song:
        return True

    # For OGG files TODO: Test if at least this works ffs
    if "metadata_block_picture" in song:
        return True

    # TODO: OPUS?
    # # For OPUS files
    # if hasattr(song, "pictures") and song.pictures:
    #     return True

    applogger.debug(f"Album art not found inside track {songPath}")
    return False


def parseArguments():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("filename")
    argparser.add_argument("--edit-all", "-a", action="store_true")
    argparser.add_argument("--copy-cover", "-c", action="store_true")
    argparser.add_argument("--delete-original-cover", action="store_true") # TODO: Implement this
    argparser.add_argument("--recursive", "-r", action="store_true") # TODO: implement recursive file processing
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


def runSingleFile():
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

        if imagePath == ():
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


runSingleFile()
