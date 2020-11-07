# The Music Archivist

A Python module for validating and formatting audio tags. Improved version of [ychalier/musicatter](https://gist.github.com/ychalier/8dbb992e5a474e41cb6af0bab22c9fee).

## Getting Started

### Prerequisites

You will need a working Python 3 installation.

### Installation

Clone the repository, and install the module with:

```
python setup.py install
```

### Usage

Execute the module with `python -m musar`. Use the `-h` or `--help` flag to show documentation. Most of the time, you will want something like this:

```
python -m musar [FOLDER] {check,format}
```

### Configuration

Constraints on tags are expressed with a simplified logic grammar. Rules are always of the form:

```
[FIELD] [CONSTRAINT] [SCOPE]
```

#### Fields

Field | Description
--- | ---
`album` | The album tag
`album_artist` | The album artist tag
`artist` | The artist tag
`comment` | The comment (only the first one is considered)
`cover` | The cover (only the first one is considered)
`disc_num` | The disc numbering (if a tuple, only the first element is considered for the constraint)
`genre` | The genre tag
`title` | The title tag
`track_num` | The track numbering (if a tuple, only the first element is considered for the constraint)
`year` | The date tag (only the year is considered)

#### Constraints

Constraint | Description
--- | ---
`distinct` | All values in scope must be different (`None` included)
`existing` | At least one value in scope is not `None`
`ordered` | Every integer between the minimum value and the maximum value is in scope (at least once)
`unique` | All values in scope must be the same (`None included`)
`valid_genre` | Genre is a valid ID3 genre (see [genres.json](data/genres.json))
`valid_cover` | Cover is a square

#### Scopes

Scope | Description
--- | ---
`album` | Group tracks per album
`disc` | Group tracks per disc
`track` | Each track is considered in a single group

Those are used for the `check` action. For the actual formatting, rules are expressed as the following:

```
[FIELD] [CLEANER]*
```

#### Cleaners

Scope | Description
--- | ---
`erase` | Set the tag to `""`
`featurings` | Format the featurings in the title into `(feat. X)`
`resize` | Resize the cover to the specified shape with `cover_target_size`
`strip` | Remove empty spaces at the beginning and the end of the tag

Check [config.txt](data/config.txt) for a config file sample.

## Contributing

Contributions are welcomed. Open issues and pull requests when you want to submit something.

## License

This project is licensed under the MIT License.
