import io
import os
import json
import glob
import subprocess
import argparse
import requests
import shadow_useragent
import PIL.Image
import eyed3


def download_video(video_url, output_filename):
    command = [
        "youtube-dlc",
        # "--verbose",
        "--extract-audio",
        "--audio-format",
        "mp3",
        "--output",
        output_filename,
        video_url
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()


def get_playlist_download_folder(data, download_folder):
    return os.path.join(
        download_folder,
        data["contents"]["twoColumnBrowseResultsRenderer"]\
            ["tabs"][0]["tabRenderer"]["content"]\
            ["sectionListRenderer"]["contents"][0]\
            ["itemSectionRenderer"]["contents"][0]\
            ["playlistVideoListRenderer"]["playlistId"]
    )


def download_videos_from_json(data, download_folder):
    video_array = data["contents"]["twoColumnBrowseResultsRenderer"]\
                      ["tabs"][0]["tabRenderer"]["content"]\
                      ["sectionListRenderer"]["contents"][0]\
                      ["itemSectionRenderer"]["contents"][0]\
                      ["playlistVideoListRenderer"]["contents"]
    os.makedirs(download_folder, exist_ok=False)
    for i, video_item in enumerate(video_array):
        print("Downloading %d of %d" % (i + 1, len(video_array)))
        video_id = video_item["playlistVideoRenderer"]["videoId"]
        video_url = "https://www.youtube.com/watch?v=%s" % video_id
        output_filename = os.path.join(
            download_folder,
            "%s.%%(ext)s" % str(i).zfill(3)
        )
        download_video(video_url, output_filename)


def request_playlist_html(playlist_url, headers):
    response = requests.get(playlist_url, headers=headers)
    return response.text


def extract_most_common(values):
    occurrences = dict()
    for value in values:
        occurrences.setdefault(value, 0)
        occurrences[value] += 1
    return max(occurrences.items(), key=lambda x: x[1])[0]


class YoutubePlaylistInfo:

    def __init__(self):
        self.tracks = None
        self.album = None
        self.thumbnail_url = None
        self.thumbnail_data = None
        self.artist = None
        self.year = None
        self.genre = None

    def parse_from_json(self, data):
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
        self.artist = extract_most_common(channels)
        return self

    def fetch_thumbnail(self, headers):
        response = requests.get(self.thumbnail_url, headers=headers)
        self.thumbnail_data = PIL.Image.open(io.BytesIO(response.content))

    def validate(self):
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


def extract_initial_data(html):
    for line in html.split("\n"):
        if line.strip().startswith('window["ytInitialData"]'):
            return json.loads(line.strip()[26:-1])
    return None


def start_musar(pdf):
    command = [
        "python",
        "-m",
        "musar",
        "--input",
        pdf,
        "--rename-hierarchy",
        "format",
    ]
    subprocess.Popen(command)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("playlist_url")
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="download folder",
        default="download",
        dest="download_folder"
    )
    parser.add_argument(
        "-sd",
        "--skip-download",
        action="store_true",
        help="skip the downloading step"
    )
    parser.add_argument(
        "-st",
        "--skip-tags",
        action="store_true",
        help="skip tags setting step"
    )
    parser.add_argument(
        "-m",
        "--musar",
        action="store_true",
        help="format downloaded data with musar"
    )
    args = parser.parse_args()
    headers = {
        "User-Agent": "{}".format(shadow_useragent.ShadowUserAgent().percent(0.05)),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    html = request_playlist_html(args.playlist_url, headers)
    data = extract_initial_data(html)
    pdf = get_playlist_download_folder(data, args.download_folder)
    print(os.path.realpath(pdf))
    if not args.skip_download:
        download_videos_from_json(data, pdf)
    if not args.skip_tags:
        playlist_info = YoutubePlaylistInfo().parse_from_json(data)
        playlist_info.validate()
        playlist_info.fetch_thumbnail(headers)
        playlist_info.set_tags(pdf)
    if args.musar:
        start_musar(pdf)


if __name__ == "__main__":
    main()
