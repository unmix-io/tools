import subprocess
from pydub import AudioSegment
import globals

#requirement: pip install pydub

def normalize(file, destination, db = "-20.0"):
    def match_target_amplitude(sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    sound = AudioSegment.from_file(file, "wav")
    normalized_sound = match_target_amplitude(sound, -20.0)
    normalized_sound.export(destination, format="wav")

def mixdown(sourcesWithVolume, destination):
    inpArgs = ""
    filterComplex = ""
    chain = ""

    for (i,w) in enumerate(sourcesWithVolume):
        volume = w[1]
        file = w[0]
        inpArgs += "-i \"" + file + "\" "

        char =  charCodeForNumber(i)

        filterComplex += "[" + str(i) + "]adelay=0|0,volume=" + str(volume) + ",agate=threshold=0.01:ratio=2:attack=0.1:release=200.0[" + char + "];"
        chain += "[" + char + "]"

    cmd = "ffmpeg -vn " + inpArgs + " -filter_complex \"" + filterComplex + chain + "amix=inputs=" + str(len(sourcesWithVolume)) + ":dropout_transition=0\" -q:a 1 -y -ar 44100 \"" + destination + "\""

    print(cmd)

    try:
        subprocess.check_call(cmd, shell=True) #cwd = cwd
        globals.log_file.write("Successful" + destination)
    except:
        globals.log_file.write("FAILED" + destination)


def charCodeForNumber(i):
    """ Returns a for 0, b for 1, etc. """
    char = ""
    while(i > 25):
        char += chr(97 + (i % 25))
        i = i - 25
    char += chr(97 + i)
    return char # 97 = a