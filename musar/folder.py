import os
import glob
import logging
import subprocess
import eyed3
import eyed3.mp3
import slugify
from .accessors import Manager as AccessorManager


def extract_most_common_value(key, items):
    values = dict()
    for item in items:
        value = item[key]
        values.setdefault(value, 0)
        values[value] += 1
    return max(values.items(), key=lambda x: x[1])[0]


class Folder:

    def __init__(self, path):
        self.path = path
        self.tracks = None

    def __iter__(self):
        if self.tracks is None:
            pass
        else:
            for track in self.tracks.values():
                yield track

    def load(self):
        self.tracks = dict()
        for filename in glob.glob(os.path.join(self.path, "*.mp3")):
            logging.debug("Load track at %s", os.path.realpath(filename))
            self.tracks[filename] = eyed3.load(filename)

    def create_hierarchy(self, mkdir):
        artist, album = None, None
        for track in self:
            if track.tag.album_artist is not None:
                artist = track.tag.album_artist
            if track.tag.album is not None:
                album = track.tag.album
            if artist is not None and album is not None:
                break
        base_folder = os.path.join(
            self.path,
            slugify.slugify(artist),
            slugify.slugify(album)
        )
        if mkdir:
            os.makedirs(base_folder, exist_ok=True)
        return base_folder

    def convert(self, config, remove_original):
        for extension in config.extensions:
            for filename in glob.glob(os.path.join(self.path, "*." + extension)):
                output_filename = os.path.splitext(filename)[0] + ".mp3"
                command = [
                    config.options.ffmpeg_path,
                    "-i",
                    filename,
                    output_filename,
                    "-y"
                ]
                process = subprocess.Popen(command)
                process.wait()
                if remove_original\
                    and os.path.isfile(output_filename)\
                    and os.path.getsize(output_filename) > 0:
                    try:
                        os.remove(filename)
                    except PermissionError:
                        logging.error(
                            "Could not delete %s",
                            os.path.realpath(filename)
                        )

    def index(self):
        index = {
            "path": self.path,
            "tracks": list(),
            "info": dict(),
        }
        mgr = AccessorManager(None)
        for path, track in self.tracks.items():
            item = {
                "path": path,
                "duration": track.info.time_secs
            }
            for name in ["title",
                         "album_artist",
                         "artist",
                         "album",
                         "track_num",
                         "disc_num",
                         "genre",
                         "year"]:
                item[name] = mgr[name].get(track)
            index["tracks"].append(item)
        for name in ["album_artist", "album", "genre", "year"]:
            index["info"][name] = extract_most_common_value(name, index["tracks"])
        index["info"]["duration"] = sum(map(lambda item: item["duration"], index["tracks"]))
        return index
