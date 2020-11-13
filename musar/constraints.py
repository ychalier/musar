"""Implementation of constraints over sets of values.
"""
import os
import json


class Constraint:
    """Placeholder class for constraints.
    """

    NAME: str = None
    """
    Constraint name for identification in the config.
    """

    def validate(self, values):
        """Check if the contrainst is respected over given values.

        Parameters
        ----------
        values : List[Union[int, str, musar.misc.HashableImage]]
            Field values.

        Returns
        -------
        bool
            Whether the constraint is respected or not.

        """
        raise NotImplementedError()


class Existing(Constraint):
    """At least one value is not `None`.
    """

    NAME = "existing"

    def validate(self, values):
        return any([v is not None for v in values])


class Unique(Constraint):
    """All values are the same.
    """

    NAME = "unique"

    def validate(self, values):
        return len(set(values)) == 1


class Distinct(Constraint):
    """All values are different.
    """

    NAME = "distinct"

    def validate(self, values):
        val_list = list(values)
        return len(set(val_list)) == len(val_list)


class Ordered(Constraint):
    """The **set** of values contains all values between its minimum and its
    maximum.

    """

    NAME = "ordered"

    def validate(self, values):
        val_list = list(values)
        if None in val_list or len(val_list) == 0:
            return False
        val_list.sort()
        return frozenset(val_list)\
            == frozenset(range(val_list[0], val_list[-1] + 1))\
            and val_list[0] == 1


class ValidGenre(Constraint):
    """The genre is a valid ID3 genre.

    Attributes
    ----------
    valid_genres : Set[str]
        Set of valid ID3 genres.

    """

    NAME = "valid_genre"

    def __init__(self):
        Constraint.__init__(self)
        self.valid_genres = set()
        with open(os.path.join(os.path.dirname(__file__), "../data/genres.json")) as infile:
            data = json.load(infile)
        for genre_category in ["standard", "Winamp"]:
            for genre in data[genre_category]:
                self.valid_genres.add(genre["label"])

    def validate(self, values):
        return all([v in self.valid_genres for v in values])


class ValidCover(Constraint):
    """The cover has a square shape.
    """

    NAME = "valid_cover"

    def validate(self, values):
        return all([
            v.image.size[0] == v.image.size[1]
            for v in values
            if v is not None
        ])


class Manager(dict):
    """Manager for accessing all the constraints.

    Attributes
    ----------
    Keys are constraint names and values are constraint instances.

    """

    def __init__(self):
        super(Manager, self).__init__()
        classes = [Existing, Unique, Distinct, Ordered, ValidGenre, ValidCover]
        for cls in classes:
            self[cls.NAME] = cls()
