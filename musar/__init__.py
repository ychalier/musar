# pylint: disable=R0913
"""The Music Archivist, a Python module for validating and formatting audio tags.
"""

__version__ = "2.0.1"
__author__ = "Yohan Chalier"
__license__ = "MIT"
__email__ = "yohan@chalier.fr"

import os
import logging
import json
import codecs
import datetime
import slugify

from .config import Config
from .download import PlaylistDownloader
from .folder import Folder
from .misc import most_common_list_value


def load_config(path, edit=False):
    """Load a config file.

    Parameters
    ----------
    path : str
        Path to the text file to load.
    edit : bool
        If `True`, a `curses` window will show up allowing user to edit the
        loaded configuration before any further step.

    Returns
    -------
    musar.config.Config
        The loaded configuration.

    """
    logging.info("Loading config from %s", os.path.realpath(path))
    config = Config.from_file(os.path.realpath(path))
    if edit:
        config.edit()
    return config


def iter_folders(top, explore=False, allow_empty=False):
    """Builds an iterator for folders containing MP3 files.

    Parameters
    ----------
    top : str
        Path to the root folder.
    explore : bool
        If `True`, every subfolder will be recursively explored. Otherwise,
        only the root folder is considered.
    allow_empty : bool
        If `False`, folders without any MP3 files in them will be ignored.

    Returns
    -------
    Iterator[musar.folder.Folder]
        Iterator over found folders.

    """
    logging.info("Exploring folders from %s", os.path.realpath(top))
    for root, _, _ in os.walk(os.path.realpath(top), topdown=True):
        logging.info("Exploring folder %s", os.path.realpath(root))
        folder = Folder(root)
        folder.load()
        if allow_empty or len(folder.tracks) > 0:
            yield folder
        if not explore:
            break


def action_check(config, folder):
    """Apply logic rules on a folder's tracks.

    Parameters
    ----------
    config : musar.config.Config
        Configuration containing the rules to apply.
    folder : musar.folder.Folder
        Folder to check.

    Returns
    -------
    bool
        Returns `True` if and only if the conjuction of rules is true.

    """
    logging.info("Checking rules on folder %s", folder.path)
    valid = True
    if len(config.rules) == 0:
        logging.warning("Checking album without any rule set up")
    for rule in config.rules:
        logging.debug("Checking rule %s", rule)
        if not rule.validate(folder):
            print("Violated %s" % rule)
            valid = False
    return valid


def action_extend(config, folder, fields):
    """Extend most common non-null field values to other tracks.

    Parameters
    ----------
    config : musar.config.Config
        A configuration to use the accessor manager of.
    folder : musar.folder.Folder
        Folder whose tracks fields will be extended.
    fields : List[str]
        List of accessor names of fields to extend.

    """
    logging.info("Extending fields on folder %s", folder.path)
    for field in fields:
        if field not in config.accessor_mgr:
            logging.error("Wrong accessor name: '%s'", field)
            continue
        values = list()
        for track in folder:
            value = config.accessor_mgr[field].get(track)
            if value is not None:
                values.append(value)
        if len(values) == 0:
            logging.error("Could not expand field %s: no non-null value found", field)
            continue
        common_value = most_common_list_value(values)
        logging.info("Selected common value %s for field %s", common_value, field)
        for track in folder:
            config.accessor_mgr[field].set(track, common_value)


def action_clean(config, folder):
    """Apply cleaners on the tracks of a folder.

    Parameters
    ----------
    config : musar.config.Config
        Configuration with the cleaners to apply.
    folder : musar.folder.Folder
        Folder whose tracks will be cleaned.

    """
    logging.info("Cleaning tags of folder %s", folder.path)
    # Emptying config accessors memory before properly setting them to store
    # values before formatting.
    logging.debug("Resetting config %s", config)
    config.reset()
    for fmt in config.formats:
        fmt.prepare(folder)
    logging.debug("Clearing all existing tags of folder %s", folder.path)
    for track in folder:
        track.tag.clear()
    logging.debug("Writing new tags for folder %s", folder.path)
    for fmt in config.formats:
        fmt.set(folder)
    for filename, track in folder.tracks.items():
        track.tag.save(filename=filename)


def generate_track_filename(track):
    """Generate a clean filename for a track. It is composed of disc numbering
    if strictly greater than 1, track numbering and track title, all slugified.
    Numberings are padded with 0s so explorer's ordering remains correct.

    Parameters
    ----------
    track : eyed3.mp3.Mp3AudioFile
        Track to generate the filename for.

    Returns
    -------
    str
        Generated filename.

    """
    disc_current, disc_total = track.tag.disc_num
    track_current, track_total = track.tag.track_num
    title = slugify.slugify(track.tag.title[:50])
    track_num_format = "%." + str(len(str(track_total))) + "d"
    filename = track_num_format % track_current + "-" + title + ".mp3"
    if disc_total > 1:
        disc_num_format = "%." + str(len(str(disc_total))) + "d"
        filename = disc_num_format % disc_current + "-" + filename
    return filename


def action_rename(folder, rename_hierarchy):
    """Rename the tracks within a folder with clean filenames.

    Parameters
    ----------
    folder : musar.folder.Folder
        Folder with the tracks to rename.
    rename_hierarchy : bool
        If `True`, a folder hierarchy artist > album is created within the
        original folder and tracks are moved at the bottom of it.

    """
    logging.info("Renaming tracks of folder %s", folder.path)
    hierarchy_folder = folder.create_hierarchy(mkdir=rename_hierarchy)
    for filename, track in folder.tracks.items():
        new_filename = generate_track_filename(track)
        if rename_hierarchy:
            os.rename(filename, os.path.join(hierarchy_folder, new_filename))
        else:
            os.rename(filename, os.path.join(
                os.path.dirname(filename), new_filename))


def action_format(
        config,
        root,
        check_only=False,
        force=False,
        rename=False,
        rename_hierarchy=False,
        explore=False,
        extend=None
        ):
    """Format the tracks within a folder.

    Parameters
    ----------
    config : musar.config.Config
        Configuration to follow.
    root : str
        Path to a root folder to look for audio tracks.
    check_only : bool
        If `True`, function will return after the check action.
    force : bool
        If `True`, function will try to format even if the checking failed.
    rename : bool
        If `True`, tracks are renamed once formatted.
    rename_hierarchy : bool
        If `True`, tracks are renamed once formatted and moved to a dedicated
        folder. See `musar.action_rename` for details.
    explore : bool
        If `True`, subfolders will be explored for audio tracks.
    extend : List[str]
        If empty or `None`, ignored. Else it contains accessor names for fields
        to extend. See `musar.action_extend` for details.

    """
    for folder in iter_folders(root, explore, allow_empty=False):
        valid = action_check(config, folder)
        if not check_only and (valid or force):
            if extend is not None and len(extend) > 0:
                action_extend(config, folder, extend)
            action_clean(config, folder)
            if rename or rename_hierarchy:
                action_rename(folder, rename)
        elif not check_only and not force:
            logging.warning(
                "Validation failed. Use -f to force formatting.")


def action_index(root, output):
    """Create a JSON index file of the music library.

    Parameters
    ----------
    root : str
        Path to the root folder to explore. Every subfolders are explored.
    output : str
        Path for the output JSON.

    """
    index = list()
    for folder in iter_folders(root, explore=True, allow_empty=False):
        index.append(folder.index())
    with codecs.open(output, "w", "utf8") as outfile:
        data = {
            "albums": index,
            "info": {
                "date_generation": datetime.datetime.utcnow()
                                   .replace(tzinfo=datetime.timezone.utc)
                                   .isoformat(),
                "musar_version": __version__,
                "root_folder": root,
            }
        }
        json.dump(data, outfile, sort_keys=True, indent=4)


def action_convert(config, root, explore, remove_original):
    """Convert non MP3 files to MP3 using FFmpeg.

    Parameters
    ----------
    config : musar.config.Config
        The configuration contains options and more importantly the list of
        file extensions that should be converted to MP3 when encountered.
    root : str
        Root folder to look for convertible files.
    explore : bool
        If `True`, subfolders are explored.
    remove_original : bool
        If `True`, original files are deleted once converted.

    """
    for folder in iter_folders(root, explore, allow_empty=True):
        folder.convert(config, remove_original)


def action_download(
        config,
        playlist_url,
        skip_download=False,
        skip_tags=False,
        edit_tags=False,
        format_tags=False
        ):
    """Download a YouTube playlist and automatically set the appropriate tags
    to downloaded files. Requires an up-to-date youtube-dl executable.

    Parameters
    ----------
    config : musar.config.Config
        Configuration with executable paths.
    playlist_url : str
        URL of the playlist to download. The script is best suited for actual
        album playlists, such as those automatically generated by YouTube.
    skip_download : bool
        If `True`, no downloading occurs, simply tag setting for already
        downloaded files. Files must be in the correct downloads folder.
    skip_tags : bool
        If `True`, tags are not automatically set to the tracks.
    edit_tags : bool
        If `True`, opens the Mp3tag program on the downloaded folder.
    format_tags : bool
        If `True`, `musar.action_format` is called on downloaded files.

    """
    downloader = PlaylistDownloader(config)
    pdf = downloader.main(
        playlist_url,
        skip_download,
        skip_tags,
        edit_tags
    )
    if format_tags:
        action_format(config, pdf, rename_hierarchy=True)
