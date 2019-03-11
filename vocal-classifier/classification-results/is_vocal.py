import csv

songs = []

with open('usable-vocal-tracks.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
    for row in reader:
        songs.append(row)


# This method returns true if a track has been classified as a vocal track
def is_vocal(songName, trackName):
    foundSongs = [s for s in songs if s["SongName"] == songName]

    if not len(foundSongs) == 1:
        return False

    vocalTracks = foundSongs[0]["VocalTracks"]
    vocalTracks = vocalTracks.split("|")

    trackNr = trackName.replace(".wav", "")
    if trackNr in vocalTracks:
        return True
    else:
        return False