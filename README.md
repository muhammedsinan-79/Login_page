# Django Login Page with Request Throttling

A Django-based web application featuring user authentication and request throttling to help protect authentication endpoints against excessive requests.

## Features

- User login page
- User registration interface
- Django-based backend
- Request throttling implementation
- MySQL database integration (if configured)
- Server-side request handling

## Tech Stack

- **Backend:** Python, Django
- **Frontend:** HTML, CSS
- **Database:** MySQL / SQLite (depending on configuration)
- **Version Control:** Git and GitHub

## Project Structure

```text
Login_page/
├── login_page/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── loginapp/
│   ├── views.py
│   ├── throttle.py
│   ├── urls.py
│   └── ...
├── manage.py
├── .gitignore
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/muhammedsinan-79/Login_page.git
cd Login_page
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

If a `requirements.txt` file exists:

```bash
pip install -r requirements.txt
```

Otherwise, install Django and any other dependencies used by the project.

### 4. Configure the database

Update the database configuration in `login_page/settings.py` according to your local setup. Configure environment variables for credentials where appropriate.

### 5. Apply migrations

```bash
python manage.py migrate
```

### 6. Start the development server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

## Request Throttling

The project includes a custom throttling module in `loginapp/throttle.py`.

Request throttling can help limit repeated requests to selected endpoints, such as login or registration, and reduce the risk of automated abuse.

The effectiveness of the implementation depends on its configuration, request identification method, storage mechanism, and integration with the relevant views.

## Future Improvements

- Add automated tests for authentication and throttling.
- Improve input validation and error handling.
- Configure secure password and session policies.
- Add logging and monitoring for repeated requests.
- Deploy the application to a production server.

## Author

**Muhammed Sinan**

Electrical and Electronics Engineering Student | Django and Embedded Systems Enthusiast

## License

This project is available for educational and learning purposes. Add a specific open-source license if you intend to permit reuse and redistribution.