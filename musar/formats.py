"""Wrapper for applying several cleaners on one accessor value.
"""

from . import scopes
from . import accessors


class Format:
    """Wrapper for applying several cleaners on one accessor value.

    Parameters
    ----------
    accessor : musar.accessors.Accessor
        Accessor on which applying the cleaners.
    *cleaners : List[musar.cleaners.Cleaner]
        Cleaners to apply.

    Attributes
    ----------
    cleaners : List[musar.cleaners.Cleaner]
    accessor : musar.accessors.Accessor

    """

    def __init__(self, accessor, *cleaners):
        self.accessor = accessor
        self.cleaners = cleaners

    def __repr__(self):
        return "Format<%s>[%s]" % (
            self.accessor.__class__.__name__,
            ", ".join(map(lambda c: c.__class__.__name__, self.cleaners))
        )

    def __str__(self):
        return "%s %s" % (
            self.accessor.NAME,
            " ".join(map(lambda c: c.NAME, self.cleaners))
        )

    def set(self, folder):
        """Set the tags of tracks after applying cleaners.

        Parameters
        ----------
        folder : musar.folder.Folder
            Folder with tracks on which applying the cleaners.

        """
        for track in folder:
            value = self.accessor.get(track)
            for cleaner in self.cleaners:
                value = cleaner.apply(value)
            self.accessor.set(track, value)

    def prepare(self, folder):
        """Prepare the accessors before clearing the tags. Sets the values in
        memories and compute `musar.accessors.NumberAccessor` total value.

        Parameters
        ----------
        folder : type
            Description of parameter `folder`.

        Returns
        -------
        type
            Description of returned object.

        """
        for track in folder:
            self.accessor.get(track)
        if isinstance(self.accessor, accessors.DiscNumber):
            total = max(self.accessor.memory.values())
            for track in folder:
                self.accessor.memory[track] = (
                    self.accessor.memory[track],
                    total
                )
        elif isinstance(self.accessor, accessors.TrackNumber):
            for tracks in scopes.Disc().iterate(folder):
                for track in tracks:
                    self.accessor.memory[track] = (
                        self.accessor.memory[track],
                        len(tracks)
                    )
