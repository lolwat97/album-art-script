#!/usr/bin/env python3

# For parsing the commandline arguments
import argparse

import itertools

# System file handling stuff
from os.path import dirname, join, getsize
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
from mutagen.id3._util import ID3NoHeaderError
from mutagen.oggvorbis import OggVorbis

# from mutagen.flac import FLAC
from mutagen.flac import Picture as MutagenFLACPicture

# Needed for ogg album art
import base64

# For album art resizing
from PIL import Image as PILImage

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
MIME_TYPES = {"jpg": "image/jpg", "png": "image/png", "jpeg": "image/jpg"}
DEFAULT_RESIZE_DIM = 1024
DEFAULT_SAVE_NAME = "cover"
DEFAULT_RESIZED_SAVE_NAME = "cover_resized"
DEFAULT_SAVE_EXT = "jpg"


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
    applogger.debug(f"Checking for existing album art in {songPath}")
    songExt = fileExtension(songPath)[1].lower().strip(".")
    if songExt == "mp3":
        return checkExistingAlbumArtMP3(songPath)
    elif songExt == "ogg":
        return checkExistingAlbumArtOGG(songPath)
    applogger.debug(f"Album art not found inside track {songPath}")
    return False


def checkExistingAlbumArtOGG(songPath):
    songFile = MutagenFile(songPath)
    if "metadata_block_picture" in songFile:
        applogger.debug(f"Album art found inside OGG track {songPath}!")
        return True
    applogger.debug(f"Album art not found inside OGG track {songPath}")
    return False


def checkExistingAlbumArtMP3(songPath):
    try:
        audio = ID3(songPath)
        for key in audio.keys():
            if key.startswith("APIC:"):
                applogger.debug(f"Album art found inside MP3 track {songPath}!")
                return True
        applogger.debug(f"Album art not found inside MP3 track {songPath}")
        return False
    except ID3NoHeaderError:
        applogger.warning(f"No ID3 tags at all in file {songPath}")
        return False


def parseArguments():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("filename")
    argparser.add_argument("--verbose", "-v", action="store_true")
    argparser.add_argument("--very-verbose", "-vv", action="store_true")
    argparser.add_argument("--edit-all", "-a", action="store_true")
    argparser.add_argument("--copy-cover", "-c", action="store_true")
    argparser.add_argument("--copy-cover-name", default=DEFAULT_SAVE_NAME)
    argparser.add_argument("--cover-save-extension", default=DEFAULT_SAVE_EXT)
    argparser.add_argument("--max-cover-size", "-s", type=float)
    argparser.add_argument(
        "--cover-resize-dimensions", type=int, default=DEFAULT_RESIZE_DIM
    )
    argparser.add_argument("--cover-resize-name", default=DEFAULT_RESIZED_SAVE_NAME)
    argparser.add_argument(
        "--textlog", action="store_true"
    )  # TODO: This doesn't affect file logging right now, fix
    argparser.add_argument(
        "--delete-original-cover", action="store_true"
    )  # TODO: Implement this
    argparser.add_argument(
        "--recursive", "-r", action="store_true"
    )  # TODO: implement recursive file processing
    args = argparser.parse_args()
    applogger.debug(f"Arguments are {args}")

    if args.max_cover_size and not args.copy_cover:
        applogger.error("--max-cover-size is only possible with --copy-cover!")
        return None

    if args.verbose:
        applogger.setLevel(logging.INFO)
    elif args.very_verbose:
        applogger.setLevel(logging.DEBUG)

    if args.textlog:
        applogger

    return args


def checkForCommonAlbumArtNames(
    songPath,
    albumArtNames=COMMON_ART_NAMES,
    saveName=DEFAULT_SAVE_NAME,
    resizedName=DEFAULT_RESIZED_SAVE_NAME,
    saveExt=DEFAULT_SAVE_EXT,
):
    applogger.debug("Checking for usual album art filenames")
    # TODO: this doesn't check if the cover file has been copied with the default name, but non-default extension
    # but fuck it, we ball
    defaultName = f"{saveName}.{saveExt}"
    applogger.debug(f"Adding a default image to check for: {defaultName}")
    albumArtNames.insert(0, defaultName)
    # Resized image to be checked first, since we do want the resized image to be added instead of a fucking 50 meg file
    resizedName = f"{resizedName}.{saveExt}"
    applogger.debug(f"Adding a resized image to check for: {resizedName}")
    albumArtNames.insert(0, resizedName)
    # albumArtNames now should be [resizedName, defaultName, (all generated names, see COMMON_ART_NAMES)]
    for commonName in albumArtNames:
        possibleName = join(dirname(songPath), commonName)
        applogger.debug(f"Checking if {possibleName} exists...")
        if fileExists(possibleName):
            applogger.debug(f"Found it! {possibleName}")
            return possibleName, True
    applogger.debug("Couldn't find anything.")
    return None, False


def resizeImageAndSave(
    imagePath,
    saveDir,
    resizeDim=DEFAULT_RESIZE_DIM,
    resizeName=DEFAULT_RESIZED_SAVE_NAME,
    resizeExt=DEFAULT_SAVE_EXT,
):
    image = PILImage.open(imagePath)
    image.thumbnail((resizeDim, resizeDim))
    fileName = join(saveDir, f"{resizeName}.{resizeExt}")
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
    applogger.debug(f"Resized {imagePath} to {image.size} and saved as {fileName}.")
    return fileName


def runSingleFile():
    args = parseArguments()
    if args is None:
        applogger.error("Invalid arguments, exiting...")
        return -1

    songPath = args.filename
    songDir = dirname(songPath)
    applogger.debug(f"Track full path is {songPath}")
    applogger.debug(f"Track dir is {songDir}")

    if not fileExists(songPath):
        applogger.error(f"File does not exist: {songPath}, exiting...")
        return -1

    albumArtExistsInTrack = checkExistingAlbumArt(songPath)

    if (not albumArtExistsInTrack) or args.edit_all:
        imagePath, commonNameFoundFlag = checkForCommonAlbumArtNames(
            songPath,
            COMMON_ART_NAMES,
            args.copy_cover_name,
            args.cover_resize_name,
            args.cover_save_extension,
        )
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

        if args.max_cover_size is not None:
            # Get size in MB, since the commandline parameter is in MB
            coverSize = getsize(imagePath) / 1024 / 1024
            applogger.debug(
                f"MAX_COVER_SIZE is set to {args.max_cover_size} MB, file size is {coverSize} MB"
            )
            if coverSize > args.max_cover_size:
                applogger.info(
                    "Cover is bigger than the size specified, shrinking it down and saving as cover.jpg..."
                )
                imagePath = resizeImageAndSave(
                    imagePath,
                    songDir,
                    args.cover_resize_dimensions,
                    args.cover_resize_name,
                    args.cover_save_extension,
                )
                imageExt = args.cover_save_extension
                imageMimeType = MIME_TYPES[imageExt]
            else:
                applogger.debug(
                    "Cover is within the specified size, continuing as normal..."
                )
                if not commonNameFoundFlag:
                    applogger.info(
                        f"Copying {imagePath} to track dir as cover.{imageExt}"
                    )
                    copyFile(
                        imagePath, join(songDir, f"{args.copy_cover_name}.{imageExt}")
                    )
        elif args.copy_cover and not commonNameFoundFlag:
            applogger.info(f"Copying {imagePath} to track dir as cover.{imageExt}")
            copyFile(imagePath, join(songDir, f"{args.copy_cover_name}.{imageExt}"))

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
