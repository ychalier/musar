import re
from . import accessors
from . import constraints
from . import scopes
from . import rules
from . import cleaners
from . import formats
from .text_editor import TextEditor


class Options:

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

    def __init__(self):
        self.rules = list()
        self.formats = list()
        self.options = Options()
        self.extensions = set()
        self._accessor_mgr = accessors.Manager(self)
        self._constraint_mgr = constraints.Manager()
        self._scope_mgr = scopes.Manager()
        self._cleaner_mgr = cleaners.Manager(self)

    def __str__(self):
        return "[RULES]\n" + "\n".join(map(str, self.rules))\
            + "\n\n[FORMATS]\n" + "\n".join(map(str, self.formats))\
            + "\n\n[OPTIONS]\n" + str(self.options)\
            + "\n\n[EXTENSIONS]\n" + "\n".join(self.extensions)

    @classmethod
    def from_file(cls, path):
        config = Config()
        config.load(path)
        return config

    def _load_rule(self, line):
        split = line.strip().split(" ")
        if len(split) != 3:
            return
        accessor_name, constraint_name, scope_name = split
        if accessor_name not in self._accessor_mgr:
            return
        if constraint_name not in self._constraint_mgr:
            return
        if scope_name not in self._scope_mgr:
            return
        self.rules.append(rules.Rule(
            self._accessor_mgr[accessor_name],
            self._constraint_mgr[constraint_name],
            self._scope_mgr[scope_name]
        ))

    def _load_format(self, line):
        split = line.strip().split(" ")
        if len(split) == 0:
            return
        if split[0] not in self._accessor_mgr:
            return
        cleaners_ = list()
        for cleaner_name in split[1:]:
            if cleaner_name not in self._cleaner_mgr:
                continue
            cleaners_.append(self._cleaner_mgr[cleaner_name])
        self.formats.append(formats.Format(
            self._accessor_mgr[split[0]],
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
        with open(path) as infile:
            self._load_text(infile.read())

    def reset(self):
        for accessor in self._accessor_mgr.values():
            del accessor.memory
            accessor.memory = dict()

    def edit(self):
        current_config = self.__str__()
        editor = TextEditor()
        new_config = editor(current_config)
        self.rules = list()
        self.formats = list()
        self.options = Options()
        self.extensions = set()
        self._load_text(new_config.strip())
