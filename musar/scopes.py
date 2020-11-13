"""Scopes for grouping album tracks over some criteria.
"""

from . import accessors


class Scope:
    """Placeholder class for scopes.
    """

    NAME: str = None
    """
    Scope name for identification in the config.
    """

    def iterate(self, folder):
        """Iterate over the groups of tracks in a folder.

        Parameters
        ----------
        folder : musar.folder.Folder
            Target folder.

        Returns
        -------
        Iterator[List[eyed3.mp3.Mp3AudioFile]]
            Iterator over the grouped tracks.

        """
        raise NotImplementedError()


class Album(Scope):
    """Album scope, all tracks are grouped together.
    """

    NAME = "album"

    def iterate(self, folder):
        yield list(folder)


class Disc(Scope):
    """Disc scope, tracks are grouped by disc.
    """

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
    """Track scope, tracks are each in a single group.
    """

    NAME = "track"

    def iterate(self, folder):
        for track in folder:
            yield [track]


class Manager(dict):
    """Manager for accessing all the scopes.

    Attributes
    ----------
    Keys are scope names and values are scope instances.

    """

    def __init__(self):
        super(Manager, self).__init__()
        classes = [Album, Disc, Track]
        for cls in classes:
            self[cls.NAME] = cls()
