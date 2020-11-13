"""Wrapper for configurable options and parameters.
"""
import re
import logging
from . import accessors
from . import constraints
from . import scopes
from . import rules
from . import cleaners
from . import formats
from .misc import TextEditor


class Options:
    """Namespace for simple parameters.

    Attributes
    ----------
    cover_target_size : Tuple[int, int]
        Size covers will be resized to in `musar.cleaners.Resize`.
    cover_target_format : str
        Image file format for the cover (in Pillow).
        See `musar.accessors.Cover`.
    cover_target_encoding : str
        Color format for the cover (in Pillow).
        See `musar.accessors.Cover`.
    youtube_dl_path : str
        Path to the *youtube-dl* executable.
    mp3tag_path : str
        Path to the *Mp3tag* executable.
    download_folder : str
        Root folder for downloaded files.
    ffmpeg_path : str
        Path to the *FFmpeg* executable.

    """

    def __init__(self):
        self.cover_target_size = 600, 600
        self.cover_target_format = "jpeg"
        self.cover_target_encoding = "RBG"
        self.youtube_dl_path = "youtube-dl"
        self.mp3tag_path = "Mp3tag.exe"
        self.download_folder = "downloads"
        self.ffmpeg_path = "ffmpeg"

    def __str__(self):
        return "\n".join([
            "cover_target_size=%d,%d" % self.cover_target_size,
            "cover_target_format=%s" % self.cover_target_format,
            "cover_target_encoding=%s" % self.cover_target_encoding,
            "youtube_dl_path=%s" % self.youtube_dl_path,
            "mp3tag_path=%s" % self.mp3tag_path,
            "download_folder=%s" % self.download_folder,
            "ffmpeg_path=%s" % self.ffmpeg_path
        ])

    def load(self, line):
        """Load a configuration file line.

        Parameters
        ----------
        line : str
            Line to parse.

        """
        split = line.strip().split("=")
        if len(split) != 2:
            return
        key, value = tuple(map(lambda s: s.strip(), split))
        if key not in self.__dict__:
            return
        if key == "cover_target_size":
            value = tuple(map(lambda s: int(s.strip()), value.split(",")))
        setattr(self, key, value)


class Config:  # pylint: disable=R0902
    """Global configuration.

    Attributes
    ----------
    rules : List[musar.rules.Rule]
        Rules that tracks should follow.
    formats : List[musar.formats.Format]
        Formats for cleaning the tag values.
    options : musar.config.Options
        General parameters.
    extensions : Set[str]
        Set of extensions for `musar.action_convert`.
    accessor_mgr : musar.accessors.Manager
        Accessors manager.
    constraint_mgr : musar.constraints.Manager
        Constraints manager.
    scope_mgr : musar.scopes.Manager
        Scopes manager.
    cleaner_mgr : musar.cleaners.Manager
        Cleaners manager.

    """

    def __init__(self):
        self.rules = list()
        self.formats = list()
        self.options = Options()
        self.extensions = set()
        self.accessor_mgr = accessors.Manager(self)
        self.constraint_mgr = constraints.Manager()
        self.scope_mgr = scopes.Manager()
        self.cleaner_mgr = cleaners.Manager(self)

    def __str__(self):
        return "[RULES]\n" + "\n".join(map(str, self.rules))\
            + "\n\n[FORMATS]\n" + "\n".join(map(str, self.formats))\
            + "\n\n[OPTIONS]\n" + str(self.options)\
            + "\n\n[EXTENSIONS]\n" + "\n".join(self.extensions)

    @classmethod
    def from_file(cls, path):
        """Create a `Config` object from a text file.

        Parameters
        ----------
        cls : type
            Class to create.
        path : str
            Path to the text file to parse.

        Returns
        -------
        musar.config.Config
            Created config

        """
        config = Config()
        config.load(path)
        return config

    def _load_rule(self, line):
        split = line.strip().split(" ")
        if len(split) != 3:
            return
        accessor_name, constraint_name, scope_name = split
        if accessor_name not in self.accessor_mgr:
            return
        if constraint_name not in self.constraint_mgr:
            return
        if scope_name not in self.scope_mgr:
            return
        self.rules.append(rules.Rule(
            self.accessor_mgr[accessor_name],
            self.constraint_mgr[constraint_name],
            self.scope_mgr[scope_name]
        ))

    def _load_format(self, line):
        split = line.strip().split(" ")
        if len(split) == 0:
            return
        if split[0] not in self.accessor_mgr:
            return
        cleaners_ = list()
        for cleaner_name in split[1:]:
            if cleaner_name not in self.cleaner_mgr:
                continue
            cleaners_.append(self.cleaner_mgr[cleaner_name])
        self.formats.append(formats.Format(
            self.accessor_mgr[split[0]],
            *cleaners_
        ))

    def _load_extension(self, line):
        self.extensions.add(line.strip())

    def _load_text(self, text):
        current_category = None
        for line in text.split("\n"):
            if line.strip() == "" or line.strip().startswith("#"):
                continue
            match = re.search(r"\[(.*?)\]", line)
            if match is not None:
                current_category = match.group(1)
                continue
            if current_category == "RULES":
                self._load_rule(line)
            elif current_category == "FORMATS":
                self._load_format(line)
            elif current_category == "OPTIONS":
                self.options.load(line)
            elif current_category == "EXTENSIONS":
                self._load_extension(line)

    def load(self, path):
        """Parse config from an external file.

        Parameters
        ----------
        path : str
            Path to the external config file.

        """
        logging.info("Parsing file %s for config %s", path, repr(self))
        with open(path) as infile:
            self._load_text(infile.read())

    def reset(self):
        """Reset the accessors memories.
        """
        logging.info("Resetting config %s", repr(self))
        for accessor in self.accessor_mgr.values():
            del accessor.memory
            accessor.memory = dict()

    def edit(self):
        """Prompt user with a text editor for live editing the current config.
        This will not modify the actual file.
        """
        logging.info("Editing config %s", repr(self))
        current_config = self.__str__()
        editor = TextEditor()
        new_config = editor(current_config)
        self.rules = list()
        self.formats = list()
        self.options = Options()
        self.extensions = set()
        self._load_text(new_config.strip())
