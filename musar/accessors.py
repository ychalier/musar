"""Interface between eyed3 and musar.
"""
import io
import PIL.Image
import eyed3.id3.frames
from .misc import HashableImage


class Accessor:
    """Placeholder class for accessors.

    Parameters
    ----------
    config : musar.config.Config
        A reference for the config associated with the accessor.
        This is used for accessors that depend on configurable parameters.

    Attributes
    ----------
    memory : Dict[str, Union[int, str, musar.misc.HashableImage]]
        Memory buffer for the getter. Keys are track fullpaths and values are
        possible field values.
    config : musar.config.Config

    """

    NAME: str = None
    """
    Accessor name for identification in the config.
    """

    def __init__(self, config):
        self.memory = dict()
        self.config = config

    def _get(self, song):
        raise NotImplementedError()

    def get(self, song):
        """Basic value getter.

        Parameters
        ----------
        song : eyed3.mp3.Mp3AudioFile
            Song to read the value from.

        Returns
        -------
        Union[int, str, musar.misc.HashableImage]
            Read value.

        """
        if song is None:
            return None
        if song in self.memory:
            return self.memory[song]
        value = self._get(song)
        self.memory[song] = value
        return value

    def set(self, song, value):
        """Abstract value setter.

        Parameters
        ----------
        song : eyed3.mp3.Mp3AudioFile
            Track to set the value to.
        value : Union[int, str, musar.misc.HashableImage]
            Value to set.

        """
        raise NotImplementedError()


class TagAccessor(Accessor):
    """Base class for simple accessors reading and setting tags without any
    modification.

    Parameters
    ----------
    config : musar.config.Config
        Accessor config.
    tag_name : str
        Name of the `eyed3` tag involved.

    Attributes
    ----------
    tag_name : str

    """

    def __init__(self, config, tag_name):
        Accessor.__init__(self, config)
        self.tag_name = tag_name

    def _get(self, song):
        return getattr(song.tag, self.tag_name)

    def set(self, song, value):
        if song is not None:
            setattr(song.tag, self.tag_name, value)


class Title(TagAccessor):
    """Track title accessor.
    """

    NAME = "title"

    def __init__(self, config):
        TagAccessor.__init__(self, config, "title")


class Album(TagAccessor):
    """Track album accessor.
    """

    NAME = "album"

    def __init__(self, config=None):
        TagAccessor.__init__(self, config, "album")


class AlbumArtist(TagAccessor):
    """Track album artist accessor.
    """

    NAME = "album_artist"

    def __init__(self, config=None):
        TagAccessor.__init__(self, config, "album_artist")


class Artist(TagAccessor):
    """Track artist accessor.
    """

    NAME = "artist"

    def __init__(self, config):
        TagAccessor.__init__(self, config, "artist")


class Composer(TagAccessor):
    """Track composer accessor.
    """

    NAME = "composer"

    def __init__(self, config):
        TagAccessor.__init__(self, config, "composer")


class NumberAccessor(TagAccessor):
    """Accessor for numbering fields (track number and disc number). eyed3
    outputs value as a tuple: only the first element is considered.
    """

    def _get(self, song):
        return getattr(song.tag, self.tag_name)[0]


class DiscNumber(NumberAccessor):
    """Track disc number accessor.
    """

    NAME = "disc_num"

    def __init__(self, config=None):
        NumberAccessor.__init__(self, config, "disc_num")


class TrackNumber(NumberAccessor):
    """Track number accessor.
    """

    NAME = "track_num"

    def __init__(self, config):
        NumberAccessor.__init__(self, config, "track_num")


class Genre(Accessor):
    """Track genre accessor. Genre is represented by its surface string.
    """

    NAME = "genre"

    def _get(self, song):
        if song.tag.genre is None:
            return None
        return song.tag.genre.name

    def set(self, song, value):
        song.tag.genre = value


class Year(Accessor):
    """Track year accessor. eyed3 uses dates but only the year is extracted.
    """

    NAME = "year"

    def _get(self, song):
        if song.tag.best_release_date is None:
            return None
        return song.tag.best_release_date.year

    def set(self, song, value):
        song.tag.recording_date = value


class Cover(Accessor):
    """Track cover accessor.
    """

    NAME = "cover"

    def _get(self, song):
        if len(song.tag.images) == 0:
            return None
        return HashableImage(PIL.Image.open(io.BytesIO(song.tag.images[0].image_data)))

    def set(self, song, value):
        if value is None:
            return
        img_data = io.BytesIO()
        value.image\
            .convert(self.config.options.cover_target_encoding)\
            .save(img_data, format=self.config.options.cover_target_format)
        song.tag.images.set(
            eyed3.id3.frames.ImageFrame.FRONT_COVER,
            img_data.getvalue(),
            "image/%s" % self.config.options.cover_target_format
        )


class Comment(Accessor):
    """Track comment accessor.
    """

    NAME = "comment"

    def _get(self, song):
        if len(song.tag.comments) == 0:
            return None
        return song.tag.comments[0].text

    def set(self, song, value):
        song.tag.comments.set(value)


class Manager(dict):
    """Manager for accessing all the accessors.

    Parameters
    ----------
    config : musar.config.Config
        Configuration that will be shared to all accessors.

    Attributes
    ----------
    Keys are accessor names and values are accessor instances.

    """

    def __init__(self, config):
        super(Manager, self).__init__()
        classes = [Title, Album, AlbumArtist, Artist, Genre, Comment,
                   Cover, Year, Composer, DiscNumber, TrackNumber]
        for cls in classes:
            self[cls.NAME] = cls(config)
