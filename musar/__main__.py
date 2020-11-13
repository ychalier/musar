import argparse
import logging
import os
import eyed3
import musar
import musar.accessors
import musar.folder
import musar.rules
import musar.config
import musar.download


def build_format_parser(base_parser):
    parser = base_parser.add_parser("format")
    parser.add_argument(
        "-e",
        "--extend",
        type=str,
        help="comma separated list of fields to extend"
    )
    parser.add_argument(
        "-c",
        "--check-only",
        action="store_true",
        help="read-only check on the target folder")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="format even if validation fails")
    parser.add_argument(
        "-r",
        "--rename",
        action="store_true",
        help="formatting renames each track based on its tags")
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
        "-x",
        "--explore",
        action="store_true",
        help="explore subdirectories")
    parser.add_argument(
        "folder",
        type=str,
        help="target folder")


def build_download_parser(base_parser):
    parser = base_parser.add_parser("download")
    parser.add_argument(
        "playlist_url",
        type=str,
        help="URL of playlist to download")
    parser.add_argument(
        "-sd",
        "--skip-download",
        action="store_true",
        help="skip the downloading step")
    parser.add_argument(
        "-st",
        "--skip-tags",
        action="store_true",
        help="skip the tag setting step")
    parser.add_argument(
        "-e",
        "--edit-tags",
        action="store_true",
        help="open Mp3tag at downloaded folder")
    parser.add_argument(
        "-f",
        "--format-tags",
        action="store_true",
        help="use musar to format downloaded tracks")


def build_index_parser(base_parser):
    parser = base_parser.add_parser("index")
    parser.add_argument(
        "folder",
        type=str,
        help="target folder")
    parser.add_argument(
        "output",
        type=str,
        help="output file")


def build_convert_parser(base_parser):
    parser = base_parser.add_parser("convert")
    parser.add_argument(
        "folder",
        type=str,
        help="target folder")
    parser.add_argument(
        "-r",
        "--remove-original",
        action="store_true",
        help="delete original files after conversion")
    parser.add_argument(
        "-x",
        "--explore",
        action="store_true",
        help="explore subdirectories")


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
        "--version",
        action="store_true",
        help="print current version"
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
        "-ec",
        "--edit-config",
        action="store_true",
        help="edit default config before execution"
    )
    action_parser = parser.add_subparsers(
        dest="action",
        help="action to perform",
    )
    build_format_parser(action_parser)
    build_download_parser(action_parser)
    build_index_parser(action_parser)
    build_convert_parser(action_parser)
    return parser


def main():
    args = build_argument_parser().parse_args()
    if not args.verbose:
        eyed3.log.setLevel("ERROR")
    logging.basicConfig(
        filename="musar.log",
        format='%(asctime)s %(levelname)s\t%(message)s',
        level=logging.INFO)
    if args.version:
        print("The Music Archivist v%s" % musar.__version__)
    logging.info("Starting Musar v%s", musar.__version__)
    config = musar.load_config(args.config, args.edit_config)
    if args.show_config:
        print(config)
    if args.action == "format":
        musar.action_format(
            config,
            args.folder,
            args.check_only,
            args.force,
            args.rename,
            args.rename_hierarchy,
            args.explore,
            list(map(lambda s: s.strip(), args.extend.split(",")))
        )
    elif args.action == "download":
        musar.action_download(
            config,
            args.playlist_url,
            args.skip_download,
            args.skip_tags,
            args.edit_tags,
            args.format_tags
        )
    elif args.action == "index":
        musar.action_index(
            args.folder,
            args.output
        )
    elif args.action == "convert":
        musar.action_convert(
            config,
            args.folder,
            args.explore,
            args.remove_original
        )

main()
