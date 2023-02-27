## Project Description
The goal is to write a simple financial service with RESTfull API and script for DB population from external source.

## Tech stack
- Python 
- PostgreSQL - good, fast, easy to use, maintain, partitionate, ACID compliance.
- FastAPI - fast asynchronous framework for python with built-in docs, dependency injection, good validation working with pydantic
- pydantic - recommended by fastapi and easy to use validator, formatter with user friendly messages, good integration, customization.
- SQLAlchemy - is also recommended, fast and quite easy to use.

## Project Launch
    docker-compose up

The project starts on port 8000 in a Docker image with PostgreSQL.
An interface for convenient access to the project API after the start is available at http://127.0.0.1:8000/docs

Every API endpoint has a description and is available without authorization.

## Run linters
    docker-compose run app linters

Runs code checkers: isort, black, pylint, mypy.

## How to maintain the API key
All secrets MUST be stored securely and never present in GIT.
On the local machine I use .env file that is added to .gitignore
On dev / stage / stable / prod usually env variables are used. But also can be used .evn files for this.
My implementation supports both variants.

## Structure
At the root of the short project are the following directories:
- financial - contains the Python code for the short link service.
- migrations - contains migrations for the Postgres database with the necessary tables, indexes and system files.
- tests - contains not as many tests as would be enough.
- get_raw_data.py - Python script to parse AlphaVantage API and store parsed data to PostgreSQL database.
- Makefile - bash script to run all linters for Python code: isort, black, pylint, mypy.
- system files for starting a project through docker, linter settings and dependency lists.

The financial directory contains the following project directories and files:
- main.py - starting point, main project file. Contains settings for logging, managing exceptions and converting them into a form that the frontend can easily parse and display.
  Also, it is a good place to start with @app.on_event("startup") decorator code from get_raw_data.py to be run periodically.
- logging.py - file with logging settings.
- exceptions.py - a file with exception settings that the user should not see, ex. a 500 error. When adding an exception to the list, it will be caught, processed and sent to the frontend in standard JSON error format.
- db.py - base class for inheritance of SQLAlchemy models and their standardization.
- utils.py - a couple of small functions used in the project.
- config.py - application settings. If you put the .env file in the root of the project, then the settings defined in it will overwrite those from the config. Allowing values to be overridden by environment variables. A convenient and secure way to store the secrets - works with github actions, etc.
- api directory - contains "probes" - small API endpoints that show the current state of the service and its performance. Often used by Kubernetes, etc.
- apps/financial/models.py and apps/financial/schemas.py - contains SQLAlchemy models for the database and Pydantic models for displaying and verifying user input.
- and finally =) apps/financial/api/views.py - a list of methods that, according to the requirements, I had to implement.

## Suggestions
- Use same response format for all API endpoints. Also same error format.
  A standard format is always a good thing for frontend developers. Allows not to write different handlers and standardize the code.
- Make error not the string but list of dicts like:
<pre><code>{
    "error": True, 
    "message": "Server unable to process user input",
    "details": [{"symbol": "value must be of string type"}, {"start_date": "value must not be from future"}]
}</code></pre>
In this case we can easily return more than one error and frontend developers could recognize field errors and not parse strings.
- precision
  In the task description there is no information about the operations and storage precision.
  Of course, since we are working with money, the precision should be good and in no case data should be 
  stored in float, etc. because precision may be lost. Therefore, I used a decimal and did not round 
  when calculating statistics. It might look ugly in statistics, but I decided to keep it that way to show 
  the importance of precision.
- partitioning
  For every day and every stock we have 1 record in the database. Over time, the size of the database 
  can increase dramatically, and the query time will increase too. Now I use index to fasten the search
  by date and symbol fields. But when the volume increase to hundreds of millions of records in won't
  be enough. For this case Postgres partitioning could be used. We can have a table for every month / week
  with partitioning by date and when data requested by date, only necessary tables will be hit.
- None if no data in stats
  In case when stats has no data for a requested period I return None instead of 0. The reason is - 0 could
  mean 0 volume, but None means no data.