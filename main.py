import random
import time
from movie_manager import Movie
from movie_manager import MovieManager
import gspread
from google.oauth2.service_account import Credentials

# edit the movie_directories to match the directories where your movies are stored
movie_directories = ["../../../git/movie-dir-1/", "../../../git/movie-dir-2/"]

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
max_col = chr(Movie.length_of_parameters + 64)

manager = MovieManager(movie_directories)
manager.process_files()
local_movies = manager.get_movie_list()


if new_worksheet_name in worksheet_list:
    work_sheet = workbook.worksheet(new_worksheet_name)
else:
    workbook.add_worksheet(title=new_worksheet_name, rows="1000", cols=Movie.length_of_parameters)
    movie_format = Movie("Name", "Resolution", "External Subtitles")
    work_sheet = workbook.worksheet(new_worksheet_name)
    work_sheet.update([[movie_format.name, movie_format.resolution, "External Subtitles"]])
    work_sheet.format(min_col + "1:" + max_col + "1", {
        "horizontalAlignment": "CENTER",
        "textFormat": {
            "fontSize": 12,
            "bold": True
        }
    })

work_sheet_data = work_sheet.get_all_values()[1:]
work_sheet_movies = []
for movie in work_sheet_data:
    work_sheet_movies.append(Movie(movie[0], movie[1], movie[2] == "x"))

def expontial_backoff(retries):
    maximum_backoff = 64
    wait_time = 2 ** retries + random.uniform(0, 1)
    print(f"Waiting for {min(wait_time, maximum_backoff)} seconds")
    time.sleep(min(wait_time, maximum_backoff))

for movie in local_movies:
    movie_exists = False
    for existing_movie in work_sheet_movies:
        # all parameters of movies are the same
        if movie == existing_movie:
            movie_exists = True
            print(f"{movie.name} is already in the list and does not need to be updated")
            break
        # only the name of the movie is the same
        elif movie.name == existing_movie.name:
            n = 0
            while True:
                try:
                    n += 1
                    row_index = work_sheet_data.index([existing_movie.name, existing_movie.resolution, "x" if existing_movie.external_subtitles else ""]) + 2
                    range = min_col + str(row_index) + ":" + max_col + str(row_index)
                    work_sheet.update(range_name = range, values = [movie.list()])
                    print(f"Updating {movie.name} in the list")
                    movie_exists = True
                    break
                except gspread.exceptions.APIError as e:
                    if e.response.status_code == 429:
                        expontial_backoff(n)
                    else:
                        raise
            break
    if not movie_exists:
        n = 0
        while True:
            try:
                n += 1
                work_sheet.append_row(movie.list())
                print(f"Added {movie.name} to the list")
                break
            except gspread.exceptions.APIError as e:
                if e.response.status_code == 429:
                    expontial_backoff(n)
                else:
                    raise