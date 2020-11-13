"""Tools to download YouTube playlists and set the appropriate audio tags.
"""

import io
import os
import re
import json
import glob
import logging
import subprocess
import requests
import shadow_useragent
import PIL.Image
import eyed3
from .misc import most_common_list_value


def download_video(youtube_dl_path, video_url, output_filename):
    """Download a YouTube video using youtube-dl, and extract its audio.

    Parameters
    ----------
    youtube_dl_path : str
        Path to the youtube-dl executable.
    video_url : str
        URL of the YouTube video.
    output_filename : str
        Path for the output MP3 file.

    """
    logging.info("Downloading YouTube video %s", video_url)
    command = [
        youtube_dl_path,
        # "--verbose",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--output",
        output_filename,
        video_url
    ]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    process.wait()


class YoutubePlaylistInfo:
    """Wrapper for a YouTube playlist metadata.

    Attributes
    ----------
    tracks : Dict[index, str]
        Keys are playlist indices and values are video titles.
    album : str
        Playlist title.
    thumbnail_url : str
        URL of the playlist's thumbnail.
    thumbnail_data : PIL.Image.Image
        Playlist's thumbnail.
    artist : str
        Most common channel accross playlist's videos.
    year : str
        Year information from user input.
    genre : str
        Genre information from user input.

    """

    def __init__(self):
        self.tracks = None
        self.album = None
        self.thumbnail_url = None
        self.thumbnail_data = None
        self.artist = None
        self.year = None
        self.genre = None

    def parse_from_json(self, data):
        """Parse the JSON data available after an HTML request to the
        YouTube playlist URL.

        Parameters
        ----------
        data : Dict
            JSON data extracted from the HTML request response.

        Returns
        -------
        YoutubePlaylistInfo
            Returns itself.

        """
        logging.info("Parsing playlist JSON data")
        self.tracks = dict()
        channels = list()
        video_array = data["contents"]["twoColumnBrowseResultsRenderer"]\
                          ["tabs"][0]["tabRenderer"]["content"]\
                          ["sectionListRenderer"]["contents"][0]\
                          ["itemSectionRenderer"]["contents"][0]\
                          ["playlistVideoListRenderer"]["contents"]
        for video_item in video_array:
            item = video_item["playlistVideoRenderer"]
            self.tracks[item["index"]["simpleText"]] = item["title"]["runs"][0]["text"]
            channels.append(item["shortBylineText"]["runs"][0]["text"])
        thumbnail_array = data["sidebar"]["playlistSidebarRenderer"]\
                              ["items"][0]\
                              ["playlistSidebarPrimaryInfoRenderer"]\
                              ["thumbnailRenderer"]\
                              ["playlistCustomThumbnailRenderer"]\
                              ["thumbnail"]["thumbnails"]
        self.thumbnail_url = max(
            thumbnail_array,
            key=lambda item: item["width"]
        )["url"]
        self.album = data["sidebar"]["playlistSidebarRenderer"]["items"][0]\
                         ["playlistSidebarPrimaryInfoRenderer"]\
                         ["title"]["runs"][0]["text"]
        self.artist = most_common_list_value(channels)
        return self

    def fetch_thumbnail(self, headers):
        """Send a request for the thumbnail. Uses the `thumbnail_url` attribute
        and writes response to the `thumbnail_data` attribute.

        Parameters
        ----------
        headers : Dict[str, str]
            Request HTTP headers.

        """
        logging.info("Requesting thumbnail at %s", self.thumbnail_url)
        response = requests.get(self.thumbnail_url, headers=headers)
        self.thumbnail_data = PIL.Image.open(io.BytesIO(response.content))

    def validate(self):
        """Ask for user input to validate the playlist info.
        """
        print("The playlist contains %d tracks." % len(self.tracks))
        for attr in ["album", "artist", "year", "genre"]:
            attr_value = getattr(self, attr)
            uinput = input("%s: %s\n>>> " % (
                attr,
                "?" if attr_value is None else "'%s'" % attr_value
            ))
            if uinput.strip() != "":
                setattr(self, attr, uinput.strip())

    def set_tags(self, pdf):
        """Set the tags to downloaded tracks from the playlist info.

        Parameters
        ----------
        pdf : str
            Path to the folder tracks were downloaded to.

        """
        img_data = io.BytesIO()
        self.thumbnail_data.convert("RGB").save(img_data, format="jpeg")
        for filename in glob.glob(os.path.join(pdf, "*.mp3")):
            track_key = str(int(os.path.splitext(os.path.basename(filename))[0]) + 1)
            audiofile = eyed3.load(filename)
            audiofile.tag.title = self.tracks[track_key].strip()
            audiofile.tag.artist = self.artist.strip()
            audiofile.tag.album_artist = self.artist.strip()
            audiofile.tag.album = self.album.strip()
            audiofile.tag.track_num = (int(track_key), len(self.tracks))
            audiofile.tag.disc_num = (1, 1)
            audiofile.tag.genre = self.genre.strip()
            audiofile.tag.recording_date = int(self.year.strip())
            audiofile.tag.images.set(
                eyed3.id3.frames.ImageFrame.FRONT_COVER,
                img_data.getvalue(),
                "image/jpeg"
            )
            audiofile.tag.save()


def check_playlist_url(playlist_url):
    """Check if a playlist URL is well-formated.

    Parameters
    ----------
    playlist_url : str
        URL to a YouTube playlist.

    Returns
    -------
    str
        If the URL is well-formated, return the playlist ID. Else return `None`.

    """
    match = re.match(
        r"https?://www\.youtube\.com/playlist\?list=(.+)",
        playlist_url.strip()
    )
    if match is None:
        raise ValueError("Incorrect URL: %s" % playlist_url)
    return match.group(1)


class PlaylistDownloader:
    """Wrapper for YouTube playlist downloading processes.

    Parameters
    ----------
    config : musar.config.Config
        General configuration.

    Attributes
    ----------
    html : str
        Response from the playlist HTTP request
    data : Dict
        Parsed JSON data from the response `html`
    info : YoutubePlaylistInfo
        Playlist metadata.
    headers : Dict[str, str]
        Headers for HTTP requests.
    config

    """

    def __init__(self, config):
        self.config = config
        self.html = None
        self.data = None
        self.info = YoutubePlaylistInfo()
        self.headers = {
            "User-Agent": "{}".format(shadow_useragent.ShadowUserAgent().percent(0.05)),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }

    def main(self,
             playlist_url,
             skip_download=False,
             skip_tags=False,
             edit_tags=False
             ):
        """Download a YouTube playlist and set the tags to the audio tracks.

        Parameters
        ----------
        playlist_url : str
            URL of the playlist to download.
        skip_download : bool
            If `True`, no downloading occurs, simply tag setting for already
            downloaded files. Files must be in the correct downloads folder.
        skip_tags : bool
            If `True`, tags are not automatically set to the tracks.
        edit_tags : bool
            If `True`, opens the Mp3tag program on the downloaded folder.

        Returns
        -------
        str
            Path to the folder tracks were downloaded to.

        """
        playlist_id = check_playlist_url(playlist_url)
        logging.info("Downloading playlist with id '%s'", playlist_id)
        pdf = os.path.join(self.config.options.download_folder, playlist_id)
        if not skip_download or not skip_tags:
            self.html = request_playlist_html(playlist_url, self.headers)
            self.data = extract_initial_data(self.html)
        if not skip_download:
            video_array = self.data["contents"]["twoColumnBrowseResultsRenderer"]\
                                   ["tabs"][0]["tabRenderer"]["content"]\
                                   ["sectionListRenderer"]["contents"][0]\
                                   ["itemSectionRenderer"]["contents"][0]\
                                   ["playlistVideoListRenderer"]["contents"]
            os.makedirs(pdf, exist_ok=False)
            for i, video_item in enumerate(video_array):
                print("Downloading %d of %d" % (i + 1, len(video_array)))
                video_id = video_item["playlistVideoRenderer"]["videoId"]
                video_url = "https://www.youtube.com/watch?v=%s" % video_id
                output_filename = os.path.join(
                    pdf,
                    "%s.%%(ext)s" % str(i).zfill(3)
                )
                download_video(
                    self.config.options.youtube_dl_path,
                    video_url,
                    output_filename
                )
        if not skip_tags:
            self.info.parse_from_json(self.data)
            self.info.validate()
            self.info.fetch_thumbnail(self.headers)
            self.info.set_tags(pdf)
        if edit_tags:
            command = [
                self.config.options.mp3tag_path,
                "/fp",
                os.path.realpath(pdf),
            ]
            process = subprocess.Popen(command)
            process.wait()
        os.startfile(pdf)
        return pdf


def request_playlist_html(playlist_url, headers):
    """Send a request to a YouTube playlist webpage.

    Parameters
    ----------
    playlist_url : str
        URL to the playlist webpage.
    headers : Dict[str, str]
        HTTP request headers.

    Returns
    -------
    str
        Response HTML

    """
    logging.info("Requesting YouTube playlist at %s", playlist_url)
    response = requests.get(playlist_url, headers=headers)
    return response.text


def extract_initial_data(html):
    """Extract and parse the JSON string from the HTML of a playlist webpage.

    Parameters
    ----------
    html : str
        HTML to extract the string from.

    Returns
    -------
    Dict
        Parsed JSON data.

    """
    logging.info("Extracting JSON string from playlist HTML data")
    for line in html.split("\n"):
        if line.strip().startswith('window["ytInitialData"]'):
            return json.loads(line.strip()[26:-1])
    return None
