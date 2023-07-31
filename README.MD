# album-art-script
A script to easily add album art to songs I wrote for myself.
Work is still in progress.

## Notes
This script implies that you have all albums stored in separate directores, one album in a dir.
ogg vorbis and mp3 files for now

## TODO
- Fix existing art detection for MP3 files
- Different writings of default names (like cover.JPG - stuff like that) (also add jacker.ext)
- option to just show artless file
- Check for very large covers (jesus, it just crams the 50 meg file inside a 5 meg song, wow)
- - Auto resize?
- - If not square, choose side?
- Add some API or something, to get covers from the net?
- Add directory/recursive processing (e.g. like `find . -type f -name "*.mp3" -exec script.py {} \;` etc etc)
- - Ability to skip dirs?
- Mods to file dialog:
- - Title
- - refresh to select newly added art
- - preview? and option to not show previews?
- if file not auto-found: locate, skip file, skip dir, try again, preview? (skip dir if recursive mode)
