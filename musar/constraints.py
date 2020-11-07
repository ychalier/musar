import os
import json


class Constraint:

    def validate(self, values):
        raise NotImplementedError()


class Existing(Constraint):

    NAME = "existing"

    def validate(self, values):
        return any([v is not None for v in values])


class Unique(Constraint):

    NAME = "unique"

    def validate(self, values):
        return len(set(values)) == 1


class Distinct(Constraint):

    NAME = "distinct"

    def validate(self, values):
        val_list = list(values)
        return len(set(val_list)) == len(val_list)


class Ordered(Constraint):

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

    NAME = "valid_cover"

    def validate(self, values):
        return all([
            v.image.size[0] == v.image.size[1]
            for v in values
            if v is not None
        ])


class Manager(dict):

    def __init__(self):
        super(Manager, self).__init__()
        classes = [Existing, Unique, Distinct, Ordered, ValidGenre, ValidCover]
        for cls in classes:
            self[cls.NAME] = cls()
