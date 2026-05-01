<!-- @format -->

## Start Docker

docker-compose up --build

## Write data in DataBase

python src/database/populate.py

## Run Server

uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
