import os
import logging
import ffmpeg

class Movie:
    length_of_parameters = 3

    def __init__(self, name, resolution, external_subtitles=False):
        self.name = name
        self.resolution = resolution
        self.external_subtitles = external_subtitles

    def __str__(self):
        return f"{self.name} ({self.resolution}) ({self.external_subtitles})"

    def __repr__(self):
        return str(self)
    
    def __eq__(self, other):
        if isinstance(other, Movie):
            return self.name == other.name and self.resolution == other.resolution and self.external_subtitles == other.external_subtitles
        return False
    
    def list (self):
        return [self.name, self.resolution, "x" if self.external_subtitles else ""]

class MovieManager:
    def __init__(self, directories=[]):
        self.movie_directories = directories
        self.movie_list = []
        self.subtitle_list = []

    def get_movie_list(self):
        return self.movie_list
    
    def get_video_resolution(self, file_path):
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None:
            logging.error(f"No video stream found in {file_path}")
            raise ValueError("No video stream found in {file_path}")
        resoulution = f"{video_stream['width']}x{video_stream['height']}"
        return resoulution

    def process_files(self):
        for directory in self.movie_directories:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith(".mp4") or file.endswith(".mkv"):
                        resolution = self.get_video_resolution(os.path.join(root, file))
                        file = file.replace(".mp4", "").replace(".mkv", "")
                        self.movie_list.append(Movie(file, resolution))
                    elif file.endswith(".srt"):
                        file = file.replace(".srt", "").replace(".en", "").replace(".default", "")
                        self.subtitle_list.append(file)
                    else:
                        logging.error(f"File {file} is not recognized")
        for subtitle in self.subtitle_list:
            for movie in self.movie_list:
                if subtitle in movie.name:
                    movie.external_subtitles = True
