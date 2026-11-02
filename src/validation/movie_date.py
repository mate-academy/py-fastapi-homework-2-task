from datetime import date


def validate_future_limit(v: date) -> date:
    today = date.today()
    one_year_hence = today.replace(year=today.year + 1)

    if v > one_year_hence:
        raise ValueError(
            f"Date cannot be more than 1 year in the future. "
            f"Max allowed date: {one_year_hence}"
        )
    return v
