# SMACs Backend

## Running Locally

We have two methods for running the backend server:
* Run in a conda environment or
* Docker.

### Running the Server in a Local Python Environment

The steps to run in a local conda environment include:
* Setup a new Python environment and install dependencies.
* Setup local database.
* Run server.

We assume you already have conda installed.

* Setup a conda environment:
  * ```conda create --name smacs python=3.11 -y```
* Activate conda environment:
  * ```conda activate smacs```

* Install Python dependencies:
  * ```python -m pip install --use-pep517 -r requirements.txt```

* Run server:
  * ```uvicorn app.main:app --reload --host 0.0.0.0 --port 8000```

* Test server (make sure you have downloaded BCC_nano.h5ad and put into the ./data directory):
  * ```curl "http://localhost:8000/search_lr?query=Cd14"```
  * ```curl "http://localhost:8000/features?mode=Genes"```
  * ```curl "http://localhost:8000/features?mode=Ligand-Receptor```

### Running the Server using Docker

* Install Docker
  * https://docs.docker.com/desktop/install/mac-install/
  * https://docs.docker.com/desktop/install/windows-install/
  * Add ```$HOME/.docker/bin``` to you PATH.

* Setup a local database:
  * ```python manage.py migrate```
  * ```python scripts/import_csv.py```

* Running server:
  * ```docker build -t myapp-local -f Dockerfile-local .```
  * ```docker run -p 8000:8000 myapp-local```

## Other Information

* Dockerfile - for deploying/testing in AWS Lambda,
* Dockerfile-local - for testing the Dockerfile locally.

Using:
* Python in Docker https://hub.docker.com/_/python  
* Debian https://www.debian.org/releases/

