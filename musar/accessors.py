import io
import PIL.Image
import eyed3.id3.frames


class HashableImage:

    def __init__(self, image):
        self.image: PIL.Image.Image = image
        self.hash: int = hash(self.image.tobytes())

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.hash == other.hash


class Accessor:

    def __init__(self, config):
        self.memory = dict()
        self.config = config

    def _get(self, song):
        raise NotImplementedError()

    def get(self, song):
        if song is None:
            return None
        if song in self.memory:
            return self.memory[song]
        value = self._get(song)
        self.memory[song] = value
        return value

    def set(self, song, value):
        raise NotImplementedError()


class TagAccessor(Accessor):

    def __init__(self, config, tag_name):
        Accessor.__init__(self, config)
        self.tag_name = tag_name

    def _get(self, song):
        return getattr(song.tag, self.tag_name)

    def set(self, song, value):
        if song is not None:
            setattr(song.tag, self.tag_name, value)


class Title(TagAccessor):

    NAME = "title"

    def __init__(self, config):
        TagAccessor.__init__(self, config, "title")


class Album(TagAccessor):

    NAME = "album"

    def __init__(self, config=None):
        TagAccessor.__init__(self, config, "album")


class AlbumArtist(TagAccessor):

    NAME = "album_artist"

    def __init__(self, config=None):
        TagAccessor.__init__(self, config, "album_artist")


class Artist(TagAccessor):

    NAME = "artist"

    def __init__(self, config):
        TagAccessor.__init__(self, config, "artist")


class Composer(TagAccessor):

    NAME = "composer"

    def __init__(self, config):
        TagAccessor.__init__(self, config, "composer")


class NumberAccessor(TagAccessor):

    def _get(self, song):
        return getattr(song.tag, self.tag_name)[0]


class DiscNumber(NumberAccessor):

    NAME = "disc_num"

    def __init__(self, config=None):
        NumberAccessor.__init__(self, config, "disc_num")


class TrackNumber(NumberAccessor):

    NAME = "track_num"

    def __init__(self, config):
        NumberAccessor.__init__(self, config, "track_num")


class Genre(Accessor):

    NAME = "genre"

    def _get(self, song):
        if song.tag.genre is None:
            return None
        return song.tag.genre.name

    def set(self, song, value):
        song.tag.genre = value


class Year(Accessor):

    NAME = "year"

    def _get(self, song):
        if song.tag.best_release_date is None:
            return None
        return song.tag.best_release_date.year

    def set(self, song, value):
        song.tag.recording_date = value


class Cover(Accessor):

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

    NAME = "comment"

    def _get(self, song):
        if len(song.tag.comments) == 0:
            return None
        return song.tag.comments[0].text

    def set(self, song, value):
        song.tag.comments.set(value)


class Manager(dict):

    def __init__(self, config):
        super(Manager, self).__init__()
        classes = [Title, Album, AlbumArtist, Artist, Genre, Comment,
                   Cover, Year, Composer, DiscNumber, TrackNumber]
        for cls in classes:
            self[cls.NAME] = cls(config)
