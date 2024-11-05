import os
import logging
import ffmpeg

# Path to the directories where the movies are stored
movie_directory = ["../../../git/movie-dir-1/", "../../../git/movie-dir-2/"]

# Configure logging
logging.basicConfig(filename='app.log', level=logging.ERROR)

def get_video_resolution(file_path):
    probe = ffmpeg.probe(file_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    if video_stream is None:
        logging.error(f"No video stream found in {file_path}")
        raise ValueError("No video stream found in {file_path}")
    width = video_stream['width']
    height = video_stream['height']
    return width, height

for directory in movie_directory:
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp4") or file.endswith(".mkv"):
                print(file)
                width, height = get_video_resolution(os.path.join(root, file))
                print(f"Resolution: {width}x{height}")
            elif file.endswith(".srt"):
                print(file)
            else:
                logging.error(f"File {file} is not recognized")

