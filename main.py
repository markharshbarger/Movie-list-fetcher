import random
import time
from movie_manager import Movie
from movie_manager import MovieManager
import gspread
from google.oauth2.service_account import Credentials
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')
paths = list(config['Paths'].values())
worksheet_id = config['API']['worksheet_id']
worksheet_name = config['API']['worksheet_name']

scopes = [
    "https://www.googleapis.com/auth/spreadsheets"
]
creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
client = gspread.authorize(creds)
workbook = client.open_by_key(worksheet_id)
worksheet_list = map(lambda x: x.title, workbook.worksheets())

min_col = "A"
max_col = chr(Movie.length_of_parameters + 64)

manager = MovieManager(paths)
manager.process_files()
local_movies = manager.get_movie_list()


if worksheet_name in worksheet_list:
    work_sheet = workbook.worksheet(worksheet_name)
else:
    workbook.add_worksheet(title=worksheet_name, rows="1000", cols=Movie.length_of_parameters)
    movie_format = Movie("Name", "Resolution", "External Subtitles")
    work_sheet = workbook.worksheet(worksheet_name)
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

new_movies = []

for movie in local_movies:
    movie_exists = False
    for existing_movie in work_sheet_movies:
        # all parameters of movies are the same
        if movie == existing_movie:
            movie_exists = True
            break
        # only the name of the movie is the same
        elif movie.name == existing_movie.name:
            n = 0
            while True:
                try:
                    movie_exists = True
                    n += 1
                    row_index = work_sheet_data.index([existing_movie.name, existing_movie.resolution, "x" if existing_movie.external_subtitles else ""]) + 2 # count header
                    range = min_col + str(row_index) + ":" + max_col + str(row_index)
                    work_sheet.update(range_name = range, values = [movie.list()])
                    print(f"Updating {movie.name} in the list")
                    break
                except gspread.exceptions.APIError as e:
                    if e.response.status_code == 429:
                        expontial_backoff(n)
                    else:
                        raise
            break
    if not movie_exists:
        new_movies.append(movie.list())

if len(new_movies) == 0:
    exit()
n = 0
while True:
    try:
        n += 1
        next_cell = len(work_sheet_movies) + 2 # count the header row
        range = min_col + str(next_cell) + ":" + max_col + str(next_cell + len(new_movies))
        work_sheet.update(range_name=range, values=new_movies)
        print(f"Added new moves to the sheet")
        break
    except gspread.exceptions.APIError as e:
        if e.response.status_code == 429:
            expontial_backoff(n)
        else:
            raise
