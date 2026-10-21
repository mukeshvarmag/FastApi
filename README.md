# Student Information API

A small FastAPI REST API using SQLite and SQLAlchemy 2.x.

## Requirements

- Python 3.14 (or another Python version supported by the installed dependencies)
- pip

## Windows PowerShell setup

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
fastapi dev main.py
```

If `py -3.14` is not available, use the installed Python launcher version, for example `py -3`.

## Linux / Ubuntu / WSL setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
fastapi dev main.py
```

Open http://127.0.0.1:8000/docs for Swagger UI.

## Endpoints

- `GET /` — health check
- `POST /students` — create a student
- `GET /students` — list students; optional `department`, `year`, `skip`, and `limit` query parameters
- `GET /students/{student_id}` — get one student
- `PATCH /students/{student_id}` — partially update a student
- `DELETE /students/{student_id}` — delete a student

## Example request

Use `POST /students` in Swagger UI with:

```json
{
  "name": "Aarav Sharma",
  "year": 2,
  "department": "Computer Science",
  "date_of_birth": "2004-06-15",
  "phone_number": "+91 9876543210",
  "gender": "Male"
}
```

The SQLite database file (`students.db`) is created in the current working directory on first startup. Phone numbers must be unique. Do not expose real student personal data publicly without appropriate access controls.
