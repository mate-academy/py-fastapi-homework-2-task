class NoMoviesError(Exception):
    """Exception raised for errors in the movies searching by input."""


class MovieAlreadyExistsError(Exception):
    """Exception raised for errors if movie already exists in database."""
