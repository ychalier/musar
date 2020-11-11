import argparse
import logging
import os
import json
import codecs
import datetime
import slugify
import eyed3
import musar
import musar.accessors
import musar.folder
import musar.rules
import musar.config
import musar.download


def build_argument_parser():
    description = (
        "Manage and standardize your music library."
    )
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="display log messages"
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "../data/config.txt"),
        help="path to the config file"
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help="print current configuration to STDOUT"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="print current version"
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="format even if validation fails"
    )
    parser.add_argument(
        "-r",
        "--rename",
        action="store_true",
        help="formatting renames each track based on its tags"
    )
    parser.add_argument(
        "-rh",
        "--rename-hierarchy",
        action="store_true",
        help=(
            "formatting renames each track based on its tags and puts it "
            "in a 'artist > album > track' folder hierarchy"
        )
    )
    parser.add_argument(
        "-e",
        "--explore",
        action="store_true",
        help="explore subdirectories"
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="folder",
        default=None,
        type=str,
        help="target folder",
    )
    action_parser = parser.add_subparsers(
        dest="action",
        help="action to perform",
    )
    action_parser.add_parser("check")
    action_parser.add_parser("format")
    index_parser = action_parser.add_parser("index")
    index_parser.add_argument("output", type=str, help="output file")
    download_parser = action_parser.add_parser("download")
    download_parser.add_argument(
        "playlist_url",
        type=str,
        help="URL of playlist to download")
    download_parser.add_argument(
        "-sd",
        "--skip-download",
        action="store_true",
        help="skip the downloading step")
    download_parser.add_argument(
        "-st",
        "--skip-tags",
        action="store_true",
        help="skip the tag setting step")
    download_parser.add_argument(
        "-et",
        "--edit-tags",
        action="store_true",
        help="open Mp3tags at downloaded folder")
    download_parser.add_argument(
        "-ft",
        "--format-tags",
        action="store_true",
        help="use musar to format downloaded tracks")
    return parser


def action_check(config, folder):
    valid = True
    for rule in config.rules:
        if not rule.validate(folder):
            logging.error("Violated %s", rule)
            valid = False
    return valid


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


def action_format(config, folder):
    config.reset()
    for fmt in config.formats:
        fmt.prepare(folder)
    for track in folder:
        track.tag.clear()
    for fmt in config.formats:
        fmt.set(folder)
    for filename, track in folder.tracks.items():
        track.tag.save(filename=filename)


def action_rename(folder, hierarchy):
    hierarchy_folder = folder.create_hierarchy(mkdir=hierarchy)
    for filename, track in folder.tracks.items():
        new_filename = generate_track_filename(track)
        if hierarchy:
            os.rename(filename, os.path.join(hierarchy_folder, new_filename))
        else:
            os.rename(filename, os.path.join(
                os.path.dirname(filename), new_filename))


def load_folders(top, explore):
    for root, _, _ in os.walk(top, topdown=True):
        folder = musar.folder.Folder(root)
        folder.load()
        if len(folder.tracks) > 0:
            yield folder
        if not explore:
            break


def extract_most_common_value(key, items):
    values = dict()
    for item in items:
        value = item[key]
        values.setdefault(value, 0)
        values[value] += 1
    return max(values.items(), key=lambda x: x[1])[0]


def action_index(folder):
    index = {
        "path": folder.path,
        "tracks": list(),
        "info": dict(),
    }
    mgr = musar.accessors.Manager(None)
    for path, track in folder.tracks.items():
        item = {
            "path": path,
            "duration": track.info.time_secs
        }
        for name in ["title",
                     "album_artist",
                     "artist",
                     "album",
                     "track_num",
                     "disc_num",
                     "genre",
                     "year"]:
            item[name] = mgr[name].get(track)
        index["tracks"].append(item)
    for name in ["album_artist", "album", "genre", "year"]:
        index["info"][name] = extract_most_common_value(name, index["tracks"])
    index["info"]["duration"] = sum(map(lambda item: item["duration"], index["tracks"]))
    return index


def main():  # pylint: disable=R0912
    args = build_argument_parser().parse_args()
    if not args.verbose:
        eyed3.log.setLevel("ERROR")
    logging.basicConfig(
        filename="musar.log",
        format='%(asctime)s %(levelname)s\t%(message)s',
        level=logging.INFO)
    config = musar.config.Config.from_file(args.config)
    if args.version:
        print("The Music Archivist v%s" % musar.__version__)
    logging.info("Starting Musar v%s", musar.__version__)
    if args.show_config:
        print(config)
    if args.action == "download":
        downloader = musar.download.PlaylistDownloader(config)
        downloader.main(args.playlist_url, args)
        return
    if args.folder is None:
        print("A folder must be specified with -i.")
        return
    index = list()
    for folder in load_folders(args.folder, args.explore):
        logging.info("Entering %s", folder.path)
        if args.action == "check":
            action_check(config, folder)
        elif args.action == "format":
            valid = action_check(config, folder)
            if valid or args.force:
                action_format(config, folder)
                if args.rename_hierarchy or args.rename:
                    action_rename(folder, args.rename_hierarchy)
            elif not valid:
                logging.warning(
                    "Validation failed. Use -f to force formatting.")
        elif args.action == "index":
            index.append(action_index(folder))
    if args.action == "index":
        with codecs.open(args.output, "w", "utf8") as outfile:
            data = {
                "albums": index,
                "info": {
                    "date_generation": datetime.datetime.utcnow()\
                        .replace(tzinfo=datetime.timezone.utc)\
                        .isoformat(),
                    "musar_version": musar.__version__,
                    "root_folder": args.folder,
                }
            }
            json.dump(data, outfile, sort_keys=True, indent=4)


main()
