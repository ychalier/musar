"""Field value cleaners.
"""

import re
from . import accessors


class Cleaner:

    def __init__(self, config):
        self.config = config

    def apply(self, value):
        raise NotImplementedError()


class StripSpaces(Cleaner):

    NAME = "strip"
    PATTERN = re.compile(r"  +")

    def apply(self, value):
        if value is None:
            return None
        return StripSpaces.PATTERN.sub(" ", value).strip()


class Featurings(Cleaner):

    NAME = "featurings"
    PATTERN = re.compile((
        r"^(.*) [\(\[]?[Ff](?:ea|EA)?[tT](?:uring)?\.?"
        r" ?(.*?)\.?[\)\]]?(?: [\(\[](?:Prod|Perf)\..*?"
        r"[\]\)])?( [\(\[].*?(?:[Mm][Ii][Xx]|[Vv]ersion)"
        r"[\]\)])?$"
    ))

    def apply(self, value):
        match = Featurings.PATTERN.match(value)
        if match is not None:
            cleaned_value = "%s (feat. %s)" % (match.group(1), match.group(2))
            if match.group(3) is not None:
                cleaned_value += match.group(3)
            return cleaned_value
        return value


class Erase(Cleaner):

    NAME = "erase"

    def apply(self, value):
        return ""


class Resize(Cleaner):

    NAME = "resize"

    def apply(self, value):
        if value is None\
                or value.image.size == self.config.options.cover_target_size:
            return value
        return accessors.HashableImage(value.image.resize(
            self.config.options.cover_target_size))


class Manager(dict):

    def __init__(self, config):
        super(Manager, self).__init__()
        classes = [StripSpaces, Featurings, Erase, Resize]
        for cls in classes:
            self[cls.NAME] = cls(config)
