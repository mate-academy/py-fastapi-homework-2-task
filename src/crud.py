from src.database.models import CountryModel


def get_movies_on_page(page, per_page, model, db):
    return (
        db.query(model)
        .order_by(model.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )


def create_new_movie(movie, db):
    db.add(movie)
    db.commit()
    db.refresh(movie)
    return movie


def get_movie_by_id(movie_id, model, db):
    return db.query(model).filter(model.id == movie_id).first()


def get_movie_by_name_and_date(name, date, model, db):
    return db.query(model).filter(model.name == name).filter(model.date == date).first()


def get_instance_by_name(name, model, db):
    return db.query(model).filter(model.name == name).first()


def create_country_by_code(code, model, db):
    country = model(code=code)
    db.add(country)
    db.commit()
    db.refresh(country)
    return country


def create_instance_by_name(name, model, db):
    instance = model(name=name)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def check_or_create_many_instances_by_name(names, model, db):
    list_of_instances = []
    for name in names:
        instance = get_instance_by_name(name=name, model=model, db=db)
        if not instance:
            instance = create_instance_by_name(name=name, model=model, db=db)
        list_of_instances.append(instance)
    return list_of_instances
