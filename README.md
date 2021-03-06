# The Music Archivist

A Python module for validating and formatting audio tags. Improved version of [ychalier/musicatter](https://gist.github.com/ychalier/8dbb992e5a474e41cb6af0bab22c9fee).

The Music Archivist is an automated tool for analyzing a set of audio tracks and checking whether their tags follow some logical rules such as "*Each track must have a title*" or "*All tracks must have the same album name*". The main purpose is to maintain the integrity and the uniformization of a large music library, by formatting new entries and checking on old ones. A configuration file is used to state the targetted tags standard. Formatting also allows for basic tag values cleaning operations, such as removing trailing spaces, unifying featurings declarations, resizing the covers to a fixed size and encoding them into a specific format. Audio files are finally renamed into a slug string formatted using validated audio tags.

The default configuration will ensure the following:

- Each track has one title
- All tracks share the same album, artist, album artist, year and cover
- All genres must be [standard ID3 genres](https://en.wikipedia.org/wiki/ID3#Genre_list_in_ID3v1[12])
- Each track has a track number and a disc number, and those numberings are complete (no missing tracks)
- Covers are 600x600 JPEG images, and are specified as ID3 *Front Covers*

<p align="center">
  <img width="200" height="200" src="musar.svg">
</p>

## Getting Started

### Prerequisites

You will need a working Python 3 installation, and some binaries:

- [youtube-dl](https://youtube-dl.org/), required for the download feature
- [Mp3tag](https://www.mp3tag.de/en/), optional for the download feature
- [FFmpeg](https://ffmpeg.org/), required for the convert feature

Those binaries are not required for the main feature (action called `format`) of this module. They do not need to be in `PATH` since their execution path can be written in the configuration file, yet it can be useful to always have them on hand.

### Installation

#### Option 1. From the repository

Clone the repository, and install the module with:

```
python setup.py install
```

#### Option 2. From the release

Download the latest release and install it with pip:

```
pip install musar-2.0.0.tar.gz
```

#### Option 3. From the package repository

Install it from my package repository:

```
pip install --extra-index-url="https://packages.chalier.fr" musar
```

### Usage

Execute the module with `python -m musar`. Use the `-h` or `--help` flag to show documentation. Most of the time, you will want something like this:

```
python -m musar {format,download,index,convert}
```

- **Action `format`** is the main feature of this module. It evaluates logical rules on the tracks of a given folder, and apply some cleaning on their tags.
- **Action `download`** downloads tracks from a YouTube playlist with automatic tagging.
- **Action `index`** creates a JSON file with info about tracks and albums under a given location.
- **Action `convert`** converts files to MP3s under a given location.

### Configuration

Configuration is written in a single text file, split into three parts. Check [config.txt](data/config.txt) for an example. Each part starts with a tag and contains instructions whose syntax is the following:

Tag         | Line Syntax                    | Purpose
----------- | ------------------------------ | -------
`[RULES]`   | `<field> <constraint> <scope>` | Set of logic rules for validating an album; resulting constraint is the conjunction of all the rules
`[FORMATS]` | `<field> <cleaner>*`           | List of cleaners to apply to a tag value when formatting (ignored fields will simply be removed from the output file)
`[OPTIONS]` | `<key>=<value>`                | Map of general purpose options
`[EXTENSIONS]` | One extension, withtout `'.'`, per line | List of files to look for when converting folder content to mp3

Fields, constraints, scopes and cleaners are keywords that correspond to a proper implementation in the module. Here is the list of available keywords:

Keyword | Description
---- | ----
**Field** |
`album`        | Album tag
`album_artist` | Album artist tag
`artist`       | Artist tag
`comment`      | Comment (only the first one is considered)
`cover`        | Cover (only the first one is considered)
`disc_num`     | Disc number (if a tuple, only the first element is considered for the constraint)
`genre`        | Genre tag
`title`        | Title tag
`track_num`    | Track number (if a tuple, only the first element is considered for the constraint)
`year`         | Year tag (if a full date, only the year is considered)
**Constraints** |
`distinct`    | All values in scope must be different (`None` included)
`existing`    | At least one value in scope is not `None`
`ordered`     | All integers between the minimal and maximal values exist in scope
`unique`      | All values in scope must be the same (`None` included)
`valid_genre` | At least one value in scope is a valid ID3 genre (see [genres.json](data/genres.json))
`valid_cover` | At least one cover in scope is a square
**Scopes** |
`album` | Group tracks per album
`disc`  | Group tracks per disc
`track` | Each track is considered in a single group
**Cleaners** |
`erase`      | Set the tag to `""`
`featurings` | Format the featurings in the title into `(feat. X)`
`resize`     | Resize the cover to the specified shape defined in `cover_target_size`
`strip`      | Remove empty spaces at the beginning and the end of the tag
**Options**             |
`cover_target_size`     | Size in pixels covers will be resized to when using the `resize` cleaner; value is of the form `width, height`
`cover_target_format`   | Image file format, [supported by Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html), to encode the cover
`cover_target_encoding` | Color encoding scheme, must comply with the image file format (see [documentation](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html) for details)
`youtube_dl_path`       | Path to a [youtube-dl](https://youtube-dl.org/) executable, for the `download` feature
`mp3tag_path`           | Path to a [Mp3tag](https://www.mp3tag.de/en/) executable, for the `download` feature (optional)
`download_folder`       | Location for downloaded tracks; the folder structure (one folder per playlist, under the specified location) is created by the program
`ffmpeg_path`           | Path to a [FFmpeg](https://ffmpeg.org/) executable, for the `convert` feature

## Documentation

Documentation is available on https://ychalier.github.io/musar/. It is generated from docstrings using [pdoc](https://pdoc3.github.io/pdoc/).

## Contributing

Contributions are welcomed. Open issues and pull requests when you want to submit something.

**Draft Roadmap**

- [x] ~~Add scanning features for summarizing the music library~~
- [x] ~~Add [youtube-dl](https://youtube-dl.org/) integration for downloading YouTube playlists~~
- [x] ~~Add [FFmpeg](https://ffmpeg.org/) integration for converting audio files~~
- [x] ~~Allow for basic config modifications from argument parsing~~
- [x] ~~Allow for field value extension when possible~~
- [x] ~~Enhance logging and progress output~~
- [x] ~~Add docstrings & documentation~~
- [ ] Modify the architecture for supporting other file formats
- [ ] Add support for FLAC

## License

This project is licensed under the MIT License.
