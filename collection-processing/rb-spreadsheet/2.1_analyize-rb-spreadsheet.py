
from os import listdir, chdir
from os.path import isfile, join, isdir

# Format specs

# Format 0: ogg, several tracks, including one named "vocals.ogg"
c_0_ogg = 0

sourceFolder = "/srv/unmix-server/1_sources/RockBand-GuitarHero/rb-spreadsheet/"

sourceFolders = [f for f in listdir(sourceFolder) if isdir(join(sourceFolder, f))]

def handle_fodler(folder):
    print(folder)

    files = [f for f in listdir(folder) if isfile(join(folder, f))]

    if(len([f for f in files if f.__contains__(".ogg")]) > 1):
        print("ogg found")
        #c_0_ogg = c_0_ogg + 1
    
    folders = [f for f in listdir(folder) if isdir(join(folder, f))]
    for fold in folders:
        handle_fodler(join(folder, fold))




for f in sourceFolders:
    folder = join(sourceFolder, f)
    handle_fodler(folder)
    #chdir(folder)
    


print("Ogg files: " + str(c_0_ogg))