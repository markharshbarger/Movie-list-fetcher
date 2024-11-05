import os
import logging
import ffmpeg
from movie import Movie
import gspread
from google.oauth2.service_account import Credentials
import time
import random

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
    resoulution = f"{video_stream['width']}x{video_stream['height']}"
    return resoulution

def expontial_backoff(retries):
    maximum_backoff = 64
    wait_time = 2 ** retries + random.uniform(0, 1)
    print(f"Waiting for {min(wait_time, maximum_backoff)} seconds")
    time.sleep(min(wait_time, maximum_backoff))


movie_list = []
subtitle_list = []

for directory in movie_directory:
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".mp4") or file.endswith(".mkv"):
                resolution = get_video_resolution(os.path.join(root, file))
                file = file.replace(".mp4", "").replace(".mkv", "")
                movie_list.append(Movie(file, resolution))
            elif file.endswith(".srt"):
                file = file.replace(".srt", "").replace(".en", "").replace(".default", "")
                subtitle_list.append(file)
            else:
                logging.error(f"File {file} is not recognized")

for subtitle in subtitle_list:
    for movie in movie_list:
        if subtitle in movie.name:
            movie.external_subtitles = True

scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)

# edit the sheet_id to match the ID of your Google Sheet (can be found in the URL)
sheet_id = "1zBxVHWQSeGAmai0tudG_OFNShOw1JQkZX4qIyhv6yoE"
workbook = client.open_by_key(sheet_id)

worksheet_list = map(lambda x: x.title, workbook.worksheets())

# edit the new_worksheet_name to match the desired name of worksheet
new_worksheet_name = "Movies"
min_col = "A"
max_col = "C"


if new_worksheet_name in worksheet_list:
    sheet = workbook.worksheet(new_worksheet_name)
else:
    workbook.add_worksheet(title=new_worksheet_name, rows="1000", cols="3")
    movie_format = Movie("Name", "Resolution", "External Subtitles")
    sheet = workbook.worksheet(new_worksheet_name)
    sheet.update([[movie_format.name, movie_format.resolution, "External Subtitles"]])
    sheet.format(min_col + "1:" + max_col + "1", {
        "horizontalAlignment": "CENTER",
        "textFormat": {
            "fontSize": 12,
            "bold": True
        }
    })

existing_movies_list = sheet.get_all_values()[1:]
existing_movies = []
for movie in existing_movies_list:
    existing_movies.append(Movie(movie[0], movie[1], movie[2] == "x"))

for movie in movie_list:
    movie_exists = False
    for existing_movie in existing_movies:
        if movie == existing_movie:
            movie_exists = True
            print(f"{movie.name} is already in the list and does not need to be updated")
            break
        elif movie.name == existing_movie.name:
            print(f"Updating {movie.name} in the list")
            row_index = existing_movies_list.index([existing_movie.name, existing_movie.resolution, "x" if existing_movie.external_subtitles else ""]) + 2
            range = min_col + str(row_index) + ":" + max_col + str(row_index)
            sheet.update(range_name = range, values = [movie.list()])
            movie_exists = True
            break
    if not movie_exists:
        n = 0
        while True:
            try:
                n += 1
                sheet.append_row(movie.list())
                print(f"Added {movie.name} to the list")
                break
            except gspread.exceptions.APIError as e:
                if e.response.status_code == 429:
                    expontial_backoff(n)
                else:
                    raise
                
# for movie in existing_movies:
#     n = 0
#     while True:
#         try:
#             print(f"Tried to add {movie.name}") 
#             n += 1
#             sheet.append_row(movie.list())
#             print(f"Added {movie.name} to the list")
#             break
#         except gspread.exceptions.APIError as e:
#             if e.response.status_code == 429:
#                 expontial_backoff(n)
#             else:
#                 raise
