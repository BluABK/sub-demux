from subprocess import check_output, CalledProcessError
import re
import os


__author__ = 'BluABK <abk@blucoders.net>'

class Track:
    index = -1
    codec = 'unset codec'
    media = 'unset media'

    def __init__(self, index, codec, media):
        self.index = index
        self.codec = codec
        self.media = media

    def about_me(self):
        return "Track(index=%s, codec=%s, media=%s)" % (self.index, self.codec, self.media)
    
class Attachment:
    index  = -1
    media = 'unset media'
    size = -1 # in bytes
    filename = 'unset filename'

    def __init__(self, index, media, size, filename):
        self.index = index
        self.media = media
        self.size = size
        self.filename = filename

    def about_me(self):
        return "Attachment(index=%s, media=\"%s\", size=%s, filename=\"%s\")" % (self.index, self.media, self.size, self.filename)

class Episode:
    filename = 'unset filename'
    tracks = []
    attachments = []
    #subtitles = {}
    chapters = -1

    def __init__(self, filename, tracks, attachments, chapters):
        self.filename = filename
        self.tracks = tracks
        self.attachments = attachments
        self.chapters = chapters

    def get_tracks(self):
        return self.tracks

    def get_attachments(self):
        return self.attachments

    def get_chapters(self):
        return self.chapters
    
    def about_me(self):
        print("%s (%s chapters):" % (self.filename, self.chapters))
        for t in self.tracks:
            print("\t%s" % t.about_me())
        for a in self.attachments:
            print("\t%s" % a.about_me())

def iterate_videos():
    cwd = os.getcwd()
    files = []
    for filename in os.listdir(cwd):
        if filename.endswith(".mkv"):
            #print(os.path.join(cwd, filename))
            files.append(filename)
            #continue
        else:
            #print("SKIP: %s" % filename)
            continue
    return sorted(files)


def iterate_episodes(files):
    episodes = []
    for ep in files:
        mkvinfo = check_output("mkvmerge -i \'%s\'" % ep, shell=True).decode("utf-8") # Decode bytes into str
        filename = ''
        tracks = []
        attachments = []
        chapters = -1
        for line in mkvinfo.split('\n'):
            if len(line) > 0:
                if "File" in line.split()[0]:
                    filename = line.split("'")[1]

                elif "Track" in line.split()[0]:
                    t_index = line.split()[2].strip(':')
                    t_codec = line.split()[4][1:-1]
                    t_media = line.split()[3]
                    
                    #tracks[t_index] = Track(t_index, t_codec, t_media)
                    tracks.append(Track(t_index, t_codec, t_media))

                elif "Attachment" in line.split()[0]:
                    a_index = line.split()[2].strip(':')
                    a_media = line.split()[4][1:-2]
                    a_size = line.split()[6]
                    a_filename = line.split()[-1].strip("'")
                    
                    #attachments[a_index] = Attachment(a_index, a_media, a_size, a_filename)
                    attachments.append(Attachment(a_index, a_media, a_size, a_filename))

                elif "Chapters" in line.split()[0]:
                    chapters = int(line.split()[-2])

                else:
                    print("Unhandled mkvinfo type: %s" % line)
        episodes.append(Episode(filename, tracks, attachments, chapters))
        if debug: print("Added Episode: %s… (%s tracks, %s attachments and %s chapters)" % (filename[0:30], len(tracks), len(attachments), chapters))

    return episodes

def map_attachments(episode):
    mapped_str = ""
    first_iteration = True
    for a in episode.attachments:
        if first_iteration:
            first_iteration = False
        else:
            mapped_str += " " 
        mapped_str += a.index + ":" + "subs" + os.sep + "'" + a.filename + "'"
    return mapped_str

def extract_subs(episode):
    extension = "srt"
    for t in episode.tracks:
        if "subtitles" in t.media:
            if "SubStationAlpha" in t.codec: extension = "ass"
            check_output("mkdir -p subs", shell=True)
            if len(episode.attachments) > 0:
                # Extract subs and attachments
                attachment_map = map_attachments(episode)
                check_output("mkvextract -v \'%s\' tracks %s:subs%s\'%s\'.%s attachments %s" % (episode.filename, t.index, os.sep, episode.filename.split('.')[-2], extension, attachment_map), shell=True)
            else:
                if debug: print("extract_subs(): No attachments detected, extracting only subtitles.")
                # Only extract subs (no attachments found)
                check_output("mkvextract -v \'%s\' tracks %s:subs%s\'%s\'.%s" % (episode.filename, t.index, os.sep, extension), shell=True)

# Main()
if __name__ == "__main__":
    debug = True
    episode_files = iterate_videos() 
    episodes = iterate_episodes(episode_files)
    
    print ("\n")
    for ep in episodes:
        #ep.about_me()
        extract_subs(ep)

    #print(map_attachments(episodes[-1]))
    #extract_subs(episodes[0])
