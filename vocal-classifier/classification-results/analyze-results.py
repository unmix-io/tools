# Generate a csv file with all usable songs and their vocal tracks
# A song is treated usable if it has 2, 4, 6, or 8 vocal tracks
# which in pairs are beneath other (for example, track 7 and 8)

import csv
import re
import collections
import numpy as np
import os

allTracks = []

with open('vocal-classifications.log-prepared.csv', 'r', encoding='utf-8-sig') as csvfile:
    spamreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')

    for row in spamreader:
        allTracks.append({
            "Classification": float(row["Classification"]),
            "SongName": re.split(r"\/", row["Filename"])[2],
            "Track": re.split(r"\/", row["Filename"])[3],
            "TrackNr": int(re.sub("[^0-9]", "", re.split(r"\/", row["Filename"])[3]))
        })

grouped = collections.defaultdict(list)
for track in allTracks:
    grouped[track['SongName']].append(track)

qualitySongs = []
i = 0

for songName, tracks in grouped.items():
    vocalTracks = sorted([t for t in tracks if t["Classification"] > 0.5], key=lambda x: x["TrackNr"])
    
    usable = False
    if len(vocalTracks) == 2 and vocalTracks[0]["TrackNr"] - vocalTracks[1]["TrackNr"] == -1:
        usable = True
    elif len(vocalTracks) == 4 and vocalTracks[0]["TrackNr"] - vocalTracks[1]["TrackNr"] == -1 and vocalTracks[2]["TrackNr"] - vocalTracks[3]["TrackNr"] == -1:
        usable = True
    elif len(vocalTracks) == 6 and vocalTracks[0]["TrackNr"] - vocalTracks[1]["TrackNr"] == -1 and vocalTracks[2]["TrackNr"] - vocalTracks[3]["TrackNr"] == -1  and vocalTracks[4]["TrackNr"] - vocalTracks[5]["TrackNr"] == -1:
        usable = True

    if usable:
        i += 1
        song = {
            "SongName": songName,
            "VocalTracks": "|".join([str(v["TrackNr"]) for v in vocalTracks])
        }
        qualitySongs.append(song)

# Export to csv file
with open('usable-vocal-tracks.csv', 'w') as f:
    w = csv.DictWriter(f, qualitySongs[0].keys())
    w.writeheader()
    w.writerows(qualitySongs)

print("Amount of songs: " + str(len(grouped)))
print("Amount of songs with acceptable vocal tracks: " + str(i))

