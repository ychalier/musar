"""Wrapper for expressing logical rules.
"""

class Rule:
    """A logical rule. A constraint over an accessor must be respected
    over a scope.

    Parameters
    ----------
    accessor : musar.accessors.Accessor
        Accessor for the concerned field.
    constraint : musar.constraints.Constraint
        Constraint that should be respected.
    scope : musar.scopes.Scope
        Scope for validating the constraint.

    Attributes
    ----------
    accessor
    constraint
    scope

    """

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
        """Check if the rule is respected for a folder.

        Parameters
        ----------
        folder : musar.folder.Folder
            Folder to apply the rule on.

        Returns
        -------
        bool
            Whether the rule is respected.

        """
        outputs = list()
        for tracks in self.scope.iterate(folder):
            outputs.append(self.constraint.validate(map(
                self.accessor.get,
                tracks
            )))
        return all(outputs)
