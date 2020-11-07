import os
import glob
import logging
import eyed3
import eyed3.mp3
import slugify


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
