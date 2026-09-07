from datetime import date


def validate_movie_date(cls, value: date) -> date:
    today = date.today()

    try:
        max_date = today.replace(year=today.year + 1)
    except ValueError:
        # today is February 29
        max_date = date(today.year + 1, 2, 28)

    if value > max_date:
        raise ValueError(
            "Date must not be more than one year in the future."
        )

    return value
