import os

# Path to the directories where the movies are stored
movie_directory = ["../../../git/movie-dir-1/", "../../../git/movie-dir-2/"]

for directory in movie_directory:
    for root, dirs, files in os.walk(directory):
        for file in files:
            print(file)