# Tutoring Platform

This project is a Django-based web application designed to facilitate tutoring. It allows users to create public profiles, manage sessions, and interact through a user-friendly interface. The platform supports various functionalities including profile management, session scheduling, and more.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.12
- Django (Version as per `requirements.txt`)
- Pipenv or pip for managing Python packages

### Installing

1. Clone the repository to your local machine:

```sh
git clone https://github.com/catenacciA/tutoringPlatform.git
```

2. Navigate to the project directory:

```sh
cd tutoringPlatform
```

3. Install the required packages:

Using Pipenv:

```sh
pipenv install
```

Or using pip:

```sh
pip install -r requirements.txt
```

4. Set up the database:

```sh
python manage.py migrate
```

5. Run the development server:

```sh
python manage.py runserver
```

The application should now be running on [http://localhost:8000](http://localhost:8000).

## Running the tests

To run the automated tests for this system, execute:

```sh
python manage.py test core
```

## Deployment

Add additional notes about how to deploy this on a live system.

## Built With

* [Django](https://www.djangoproject.com/) - The web framework used
* [SQLite](https://www.sqlite.org/index.html) - Database Engine

# License

This project is licensed under the MIT License - see the LICENSE.md file for details

