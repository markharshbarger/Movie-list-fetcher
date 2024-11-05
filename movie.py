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