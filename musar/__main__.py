import argparse
import logging
import os
import slugify
import eyed3
import musar
import musar.folder
import musar.rules
import musar.config


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


def main():
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
    if args.folder is None:
        print("A folder must be specified with -i.")
        return
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


main()
