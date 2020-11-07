from . import scopes
from . import accessors


class Format:

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
        for track in folder:
            value = self.accessor.get(track)
            for cleaner in self.cleaners:
                value = cleaner.apply(value)
            self.accessor.set(track, value)

    def prepare(self, folder):
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
