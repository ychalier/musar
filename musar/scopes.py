from . import accessors


class Scope:

    def iterate(self, folder):
        raise NotImplementedError()


class Album(Scope):

    NAME = "album"

    def iterate(self, folder):
        yield list(folder)


class Disc(Scope):

    NAME = "disc"

    def iterate(self, folder):
        disc_num_accessor = accessors.DiscNumber()
        tracks = folder.tracks.values()
        groups = dict()
        for track in tracks:
            disc_num = disc_num_accessor.get(track)
            groups.setdefault(disc_num, list())
            groups[disc_num].append(track)
        for tracks in groups.values():
            yield tracks


class Track(Scope):

    NAME = "track"

    def iterate(self, folder):
        for track in folder:
            yield [track]


class Manager(dict):

    def __init__(self):
        super(Manager, self).__init__()
        classes = [Album, Disc, Track]
        for cls in classes:
            self[cls.NAME] = cls()
