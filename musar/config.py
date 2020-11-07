import re
from . import accessors
from . import constraints
from . import scopes
from . import rules
from . import cleaners
from . import formats


class Options:

    def __init__(self):
        self.cover_target_size = 600, 600
        self.cover_target_format = "jpeg"
        self.cover_target_encoding = "RBG"

    def __str__(self):
        return "\n".join([
            "cover_target_size=%d,%d" % self.cover_target_size,
            "cover_target_format=%s" % self.cover_target_format,
            "cover_target_encoding=%s" % self.cover_target_encoding
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


class Config:

    def __init__(self):
        self.rules = list()
        self.formats = list()
        self.options = Options()
        self._accessor_mgr = accessors.Manager(self)
        self._constraint_mgr = constraints.Manager()
        self._scope_mgr = scopes.Manager()
        self._cleaner_mgr = cleaners.Manager(self)

    def __str__(self):
        return "[RULES]\n" + "\n".join(map(str, self.rules))\
            + "\n\n[FORMATS]\n" + "\n".join(map(str, self.formats))\
            + "\n\n[OPTIONS]\n" + str(self.options)

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

    def load(self, path):
        current_category = None
        with open(path) as infile:
            for line in infile.readlines():
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

    def reset(self):
        for accessor in self._accessor_mgr.values():
            del accessor.memory
            accessor.memory = dict()
