"""Field value cleaners.
"""

import re
from . import accessors


class Cleaner:
    """Placeholder class for cleaners.

    Parameters
    ----------
    config : musar.config.Config
        A reference for the config associated with the cleaner.

    Attributes
    ----------
    config : musar.config.Config

    """

    NAME: str = None
    """
    Cleaner name for identification in the config.
    """

    def __init__(self, config):
        self.config = config

    def apply(self, value):
        """Transform the value into a new one, cleaner.

        Parameters
        ----------
        value : Union[int, str, musar.misc.HashableImage]
            Input value.

        Returns
        -------
        Union[int, str, musar.misc.HashableImage]
            Output value, after cleaning.

        """
        raise NotImplementedError()


class StripSpaces(Cleaner):
    """Remove empty spaces at the beginning and at the end of the value, and
    remove doubled spaces.

    Attributes
    ----------
    PATTERN : re.Pattern
        Compiled pattern for detecting multiple spaces.

    """

    NAME = "strip"
    PATTERN = re.compile(r"  +")

    def apply(self, value):
        if value is None:
            return None
        return StripSpaces.PATTERN.sub(" ", value).strip()


class Featurings(Cleaner):
    """Detect when the string value contains a featuring reference and format
    it into `"(feat. XXXX)"`.

    Attributes
    ----------
    PATTERN : re.Pattern
        Compiled pattern for detecting featuring references.

    """

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
    """Set the value to an empty string.

    """

    NAME = "erase"

    def apply(self, value):
        return ""


class Resize(Cleaner):
    """Resize an image.

    """

    NAME = "resize"

    def apply(self, value):
        if value is None\
                or value.image.size == self.config.options.cover_target_size:
            return value
        return accessors.HashableImage(value.image.resize(
            self.config.options.cover_target_size))


class Manager(dict):
    """Manager for accessing all the cleaners.

    Parameters
    ----------
    config : musar.config.Config
        Configuration that will be shared to all cleaners.

    Attributes
    ----------
    Keys are cleaner names and values are cleaner instances.

    """

    def __init__(self, config):
        super(Manager, self).__init__()
        classes = [StripSpaces, Featurings, Erase, Resize]
        for cls in classes:
            self[cls.NAME] = cls(config)
