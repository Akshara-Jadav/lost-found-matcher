# 🎒 Campus Lost & Found Matcher

A web app that helps students recover lost belongings. People report items they **lost** or **found**, the app scores every lost/found pair and suggests the best matches, and owners get the finder's contact only after passing a verification check.

Built with **FastAPI** (backend), **Streamlit** (frontend) and tested with **pytest**.

## Features

- **Report lost or found items** with category, description, location, date, colour and brand
- **Smart matching:** every lost/found pair gets a score out of 100, and only pairs scoring 60 or more are shown
- **"Why this match?" breakdown:** a chart shows how many points each factor contributed
- **Secure claim flow:** the finder sets a secret question when reporting. An owner can claim an item only when:
  1. the match score is at least **80%**, and
  2. they answer the secret question correctly (3 wrong attempts block the item)
- **Privacy by design:** contact details and secret answers are never exposed through the public API, and the CSV export leaves contacts out
- **Browse and search** reports in card or table view, with filters for type and status
- **Admin tools:** expire old reports, export reports as CSV, view stats
- **Logging** of reports, matches and claim attempts to `logs/app.log`

## How matching works

| Factor | Points | How it is scored |
|---|---|---|
| Category | 30 | Same word, typo or plural tolerant |
| Description | 30 | Text similarity between the two descriptions |
| Location | 20 | Same place, nearby place, or a spelling mistake |
| Date | 15 | Closer dates score higher; found before lost scores 0 |
| Colour / brand | 5 | Matching colour and/or brand |

The "nearby places" map is in `app/scorers.py` (`NEARBY`). Edit it to match your own campus.

## Tech stack

- Python 3
- FastAPI and Uvicorn (REST API)
- Pydantic (input validation)
- Streamlit (user interface)
- Pandas and Requests
- pytest (75 tests)
- JSON file storage

## Project structure

```
lost-found-matcher/
├── app/
│   ├── main.py          # FastAPI endpoints
│   ├── models.py        # Report, LostReport, FoundReport classes
│   ├── schemas.py       # Pydantic validation
│   ├── scorers.py       # Individual scoring rules
│   ├── matcher.py       # Combines scorers into a 0-100 score
│   ├── storage.py       # JSON-backed report store
│   ├── text_utils.py    # Text similarity helpers
│   ├── reports.py       # CSV export
│   └── logger.py        # Rotating log file
├── tests/               # pytest test suite
├── streamlit_app.py     # Streamlit frontend
├── make_sample_data.py  # Sample data generator
└── requirements.txt
```

## Getting started

**1. Clone and set up**

```bash
git clone https://github.com/Akshara-Jadav/lost-found-matcher.git
cd lost-found-matcher
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

**2. Start the backend** (terminal 1)

```bash
uvicorn app.main:app
```

The API runs at http://127.0.0.1:8000 and interactive docs are at http://127.0.0.1:8000/docs.

**3. Start the app** (terminal 2)

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501 in your browser.

**4. Run the tests**

```bash
pytest
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/reports` | Create a lost or found report |
| GET | `/reports` | List reports (filter by kind and status) |
| GET | `/reports/{id}` | Get one report |
| GET | `/reports/{id}/matches` | Matches for a report, with score breakdown |
| POST | `/claim` | Verify a claim and reveal the finder's contact |
| GET | `/stats` | Summary counters |
| POST | `/admin/expire` | Expire reports older than N days |
| GET | `/export/csv` | Download reports as CSV |

## What I learned

- Designing a REST API with FastAPI and validating input with Pydantic
- Object-oriented design: inheritance for report types, abstract base class for scorers
- Building a multi-page Streamlit app that talks to an API
- Protecting private data and limiting abuse (verification questions, attempt limits)
- Writing a test suite that covers models, scoring, storage and the API

## Possible improvements

- Replace JSON storage with a database such as SQLite
- Add user accounts and image uploads
- Notify owners by email or SMS when a strong match appears

## Author

**Jadav Akshara**, [GitHub](https://github.com/Akshara-Jadav)