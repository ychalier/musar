# pylint: disable=R0913
"""The Music Archivist
"""

__version__ = "1.5.0"
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
from .folder import Folder, extract_most_common_value


class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def load_config(path, edit=False):
    config = Config.from_file(path)
    if edit:
        config.edit()
    return config


def iter_folders(top, explore=False, allow_empty=False):
    for root, _, _ in os.walk(top, topdown=True):
        folder = Folder(root)
        folder.load()
        if allow_empty or len(folder.tracks) > 0:
            yield folder
        if not explore:
            break


def action_check(config, folder):
    valid = True
    for rule in config.rules:
        if not rule.validate(folder):
            logging.info("Violated %s", rule)
            valid = False
    return valid


def most_common_list_value(values):
    occurrences = dict()
    for value in values:
        occurrences.setdefault(value, 0)
        occurrences[value] += 1
    return max(occurrences.items(), key=lambda x: x[1])[0]


def action_extend(config, folder, fields):
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
    config.reset()
    for fmt in config.formats:
        fmt.prepare(folder)
    for track in folder:
        track.tag.clear()
    for fmt in config.formats:
        fmt.set(folder)
    for filename, track in folder.tracks.items():
        track.tag.save(filename=filename)


def generate_track_filename(track):
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
    downloader = PlaylistDownloader(config)
    downloader.main(playlist_url, Namespace(
        skip_download=skip_download,
        skip_tags=skip_tags,
        edit_tags=edit_tags,
        format_tags=format_tags
    ))
