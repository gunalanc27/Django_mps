# 🛠️ Installation Guide - tes

Follow these steps to set up the tes project on your local machine.

## Prerequisites

- **Python**: 3.10 or higher (Python 3.13 recommended)
- **Node.js**: 16.x or higher (Required for Tailwind CSS)
- **Git**: For version control

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/TNlucfer01/Django_mps.git
cd Django_mps
```

### 2. Create and Activate Virtual Environment

```bash
# On Linux/macOS
python -m venv Dvenv
source Dvenv/bin/activate

# On Windows
python -m venv Dvenv
Dvenv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

*Note: If `requirements.txt` is missing, ensure the following core packages are installed:*
`django django-tailwind django-jazzmin dj-database-url python-dotenv whitenoise`

### 4. Setup Tailwind CSS

tes uses `django-tailwind`. You need to install the Node.js dependencies for the theme:

```bash

```python manage.py tailwind install

### 5. Initialize the Database

Apply the migrations to set up your local SQLite database:

```bash
python manage.py migrate
```

### 6. Create a Superuser

To access the colorful `/admin/` panel:

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

Start the Django server:

```bash
python manage.py runserver
```

In a separate terminal (with the virtual environment activated), start the Tailwind watcher or build the styles:

```bash
# To watch for changes
python manage.py tailwind start

# To build for production
python manage.py tailwind build
```

The application will be available at`http://127.0.0.1:8000/`.

## Environment Variables

Create a `.env` file in the root directory and add the following:

```env
DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
```

## Troubleshooting

- **ModuleNotFoundError: No module named 'django'**: Ensure your virtual environment (`Dvenv`) is activated.
- **Tailwind not loading**: Ensure you have run `python manage.py tailwind build` at least once.
```
