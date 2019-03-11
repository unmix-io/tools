#!/bin/bash

BASE='/srv/unmix-server/'
ARCHIVES=$BASE'0_archives/RockBand-GuitarHero/RB-Spreadsheet/'
SOURCES=$BASE'1_sources/RockBand-GuitarHero/RB-Spreadsheet/'

# Extract ZIP files
find "$ARCHIVES" -type f -iname '*.zip' | while read FILE; do
    filename=$(basename -- "$FILE")
    filename="${filename%.*}"

    DEST=$SOURCES$filename

    if [[ -d "$DEST" ]]; then
        echo "$DEST already exists - skip"
    else
        echo "Extracting $FILE to $DEST:"
        unzip -q "$FILE" -d "$DEST"
    fi

done

# Extract RAR files
find "$ARCHIVES" -type f -iname '*.rar' | while read FILE; do
    filename=$(basename -- "$FILE")
    filename="${filename%.*}"

    DEST=$SOURCES$filename

    if [[ -d "$DEST" ]]; then
        echo "$DEST already exists - skip"
    else
        mkdir "$DEST"
        echo "Extracting $FILE to $DEST"
        unrar x -inul "$FILE" "$DEST"
    fi

done

# Extract 7z files
find "$ARCHIVES" -type f -iname '*.7z' | while read FILE; do
    filename=$(basename -- "$FILE")
    filename="${filename%.*}"

    DEST=$SOURCES$filename

    if [[ -d "$DEST" ]]; then
        echo "$DEST already exists - skip"
    else
        mkdir "$DEST"
        echo "Extracting $FILE to $DEST"
        7z x -o"$DEST" "$FILE" > nul
    fi

done

# Copy mogg files
find "$ARCHIVES" -type f -iname '*.mogg' | while read FILE; do
    filename=$(basename -- "$FILE")
    filename="${filename%.*}"

    DEST=$SOURCES$filename

    if [[ -d "$DEST" ]]; then
        echo "$DEST already exists - skip"
    else
        mkdir "$DEST"
        echo "Copying $FILE to $DEST:"
        cp "$FILE" "$DEST"
    fi
    
done

# Remove unneeded __MACOSX directories
find . -name "__MACOSX" -type d -exec rm -r {} \;

# Normalize structure: If there are subdirectories in the song directories and no other files in root, flatten directory structure
#find "$SOURCES" -maxdepth 1 -mindepth 1 -type d | while read SONGDIR; do
#    DIRCOUNT=`find "$SONGDIR/" -maxdepth 1 -mindepth 1 -type d | wc -l`
#    ROOTFILECOUNT=`find "$SONGDIR/" -maxdepth 1 -mindepth 1 -type f | wc -l`

#    if [ $DIRCOUNT -eq  1 ] && [ $ROOTFILECOUNT  -eq 0 ]; then

#        DIR=`find "$SONGDIR/" -maxdepth 1 -mindepth 1 -type d | tail -1`
#        echo "Moving $DIR to $SOURCES and removing $SONGDIR"
#        mv "$DIR" "$SOURCES"
        #rmdir "$SONGDIR"

        #find "$SONGDIR" -mindepth 2 -type f -exec mv -i '{}' "$SONGDIR" ';'
        #DIR=`find "$SONGDIR/" -maxdepth 1 -mindepth 1 -type d | tail -1`
        #mv "$SONGDIR" "$SOURCES/"
#    fi
#done

# Correct file permissions (not readable by SAMBA share otherwise)
find "$SOURCES" -mindepth 1 -type d -exec chmod 775 {} \;
find "$SOURCES" -mindepth 1 -type d -exec chmod g+s {} \;
find "$SOURCES" -mindepth 1 -type f -exec chmod 664 {} \;