class Rule:

    def __init__(self, accessor, constraint, scope):
        self.accessor = accessor
        self.constraint = constraint
        self.scope = scope

    def __repr__(self):
        return "%s<%s, %s, %s>" % (
            self.__class__.__name__,
            self.accessor.__class__.__name__,
            self.constraint.__class__.__name__,
            self.scope.__class__.__name__
        )

    def __str__(self):
        return "%s %s %s" % (
            self.accessor.NAME,
            self.constraint.NAME,
            self.scope.NAME
        )

    def validate(self, folder):
        outputs = list()
        for tracks in self.scope.iterate(folder):
            outputs.append(self.constraint.validate(map(
                self.accessor.get,
                tracks
            )))
        return all(outputs)
