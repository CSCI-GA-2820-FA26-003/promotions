# Promotions Service

[![CI](https://github.com/CSCI-GA-2820-FA26-003/promotions/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA26-003/promotions/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-FA26-003/promotions/branch/master/graph/badge.svg)](https://codecov.io/gh/CSCI-GA-2820-FA26-003/promotions)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python_3.12-blue.svg)](https://python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask_3-black.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_15-336791.svg)](https://www.postgresql.org/)

The Promotions service is one of the microservices that make up the NYU DevOps
e-commerce site. It owns everything about **promotions**: the deals that apply
to a product for a period of time, such as a flash sale, a Black Friday discount
or a 2-for-1 campaign. Other squads (Shopcarts, Orders, Products) never touch the
promotions database directly; they call this service's REST API.

The service is a Flask application backed by PostgreSQL. It is developed with
Test Driven Development: every endpoint has unit tests for its happy and sad
paths, and the suite must keep at least 95% code coverage.

## Contents

- [Promotions Service](#promotions-service)
  - [Contents](#contents)
  - [What the service does](#what-the-service-does)
  - [Data model](#data-model)
  - [API reference](#api-reference)
    - [`GET /`](#get-)
    - [`GET /promotions`](#get-promotions)
    - [`GET /promotions/{promotion_id}`](#get-promotionspromotion_id)
    - [`POST /promotions`](#post-promotions)
    - [`PUT /promotions/{promotion_id}`](#put-promotionspromotion_id)
    - [`DELETE /promotions/{promotion_id}`](#delete-promotionspromotion_id)
    - [Error responses](#error-responses)
  - [Running the service](#running-the-service)
    - [Prerequisites](#prerequisites)
    - [Start the development container](#start-the-development-container)
    - [Start the service](#start-the-service)
  - [Testing and linting](#testing-and-linting)
  - [Configuration](#configuration)
  - [Project layout](#project-layout)
  - [Development workflow](#development-workflow)
  - [License](#license)

## What the service does

| Operation | Method and path | Success code |
|-----------|-----------------|--------------|
| Service information | `GET /` | 200 |
| List all promotions | `GET /promotions` | 200 |
| Read one promotion | `GET /promotions/{promotion_id}` | 200 |
| Create a promotion | `POST /promotions` | 201 + `Location` header |
| Update a promotion | `PUT /promotions/{promotion_id}` | 200 |
| Delete a promotion | `DELETE /promotions/{promotion_id}` | 204 |

Every response, including every error, is JSON. The service never returns HTML.

## Data model

A promotion is a single row in the `promotions` table. There is no child table:
a promotion has no line items, so there is no sub-resource under
`/promotions/{promotion_id}`.

```mermaid
erDiagram
    PROMOTIONS {
        int promotion_id PK "client supplied, unique"
        int product_id "NOT NULL, id of the product in the Products service"
        varchar(150) promotion_description "NOT NULL, kind of deal"
        varchar(150) campaign "NOT NULL, marketing campaign the deal belongs to"
        date start_date "NOT NULL, first valid day"
        date end_date "NOT NULL, last valid day"
        varchar(20) status "NOT NULL, default active"
        numeric final_price "NUMERIC(10,2) NOT NULL, price after the promotion"
        timestamp created_at "NOT NULL, set by the server"
    }
```

| Field | Type | Required on create | Description |
|-------|------|--------------------|-------------|
| `promotion_id` | integer | yes | Primary key. Supplied by the client and must be unique; it is the `{promotion_id}` used in URLs. |
| `product_id` | integer | yes | The product the deal applies to. This is the product's id in the Products service. It is stored as a plain integer with no foreign key, because the Products table lives in another squad's database. |
| `promotion_description` | string (≤150) | yes | The kind of deal, e.g. `discount`, `2x1`, `free shipping`, `bundle deal`, `cashback`. |
| `campaign` | string (≤150) | yes | The campaign the deal belongs to, e.g. `flash sale`, `black friday`, `summer sale`. |
| `start_date` | date `YYYY-MM-DD` | yes | First day the promotion is valid (inclusive). |
| `end_date` | date `YYYY-MM-DD` | yes | Last day the promotion is valid (inclusive). |
| `status` | string (≤20) | yes | Lifecycle state. Conventional values: `scheduled`, `active`, `inactive`, `expired`, `cancelled`. |
| `final_price` | number (2 decimals) | yes | The product's price while the promotion applies. Stored as an exact decimal, never a float. |
| `created_at` | datetime (ISO 8601) | no | Set by the server when the row is created. Ignored if a client sends it. |

## API reference

All examples assume the service is running locally on port 8080
(see [Running the service](#running-the-service)). Request bodies must be sent
with `Content-Type: application/json`.

### `GET /`

Returns information about the service so a client can discover the API.

```bash
curl -i http://localhost:8080/
```

```json
{
  "name": "Promotions REST API Service",
  "version": "1.0",
  "description": "Create, read, update, delete and list the promotions that apply to products in the e-commerce store",
  "paths": "http://localhost:8080/promotions"
}
```

### `GET /promotions`

Returns every promotion as a JSON array. An empty database returns `[]`.

```bash
curl -i http://localhost:8080/promotions
```

```json
[
  {
    "promotion_id": 1,
    "product_id": 42,
    "promotion_description": "discount",
    "campaign": "flash sale",
    "start_date": "2026-11-01",
    "end_date": "2026-11-10",
    "status": "active",
    "final_price": 9.99,
    "created_at": "2026-10-16T14:05:31.204512"
  }
]
```

### `GET /promotions/{promotion_id}`

Returns one promotion by its `promotion_id`. Cancelled or expired promotions
are still returned, with their status.

```bash
curl -i http://localhost:8080/promotions/1
```

| Result | Code |
|--------|------|
| Promotion found | `200 OK` with the promotion as JSON |
| `promotion_id` is `0` | `400 Bad Request` |
| No promotion with that id, or the id is not a positive integer | `404 Not Found` |

### `POST /promotions`

Creates a promotion from the JSON body. The response is the stored promotion
(now including `created_at`) and a `Location` header pointing at the new
resource.

```bash
curl -i -X POST http://localhost:8080/promotions \
  -H "Content-Type: application/json" \
  -d '{
    "promotion_id": 1,
    "product_id": 42,
    "promotion_description": "discount",
    "campaign": "flash sale",
    "start_date": "2026-11-01",
    "end_date": "2026-11-10",
    "status": "active",
    "final_price": 9.99
  }'
```

```http
HTTP/1.1 201 CREATED
Content-Type: application/json
Location: http://localhost:8080/promotions/1
```

| Result | Code |
|--------|------|
| Created | `201 Created` |
| Missing field, bad date, bad number, malformed JSON, or duplicate `promotion_id` | `400 Bad Request` |
| Missing or wrong `Content-Type` | `415 Unsupported Media Type` |

### `PUT /promotions/{promotion_id}`

Replaces an existing promotion with the JSON body (same fields as create).
Use this to change dates, the price, or to pause a deal by setting
`status` to `inactive`.

> Story [#6](https://github.com/CSCI-GA-2820-FA26-003/promotions/issues/6) — in progress in Sprint 1.

```bash
curl -i -X PUT http://localhost:8080/promotions/1 \
  -H "Content-Type: application/json" \
  -d '{
    "promotion_id": 1,
    "product_id": 42,
    "promotion_description": "discount",
    "campaign": "flash sale",
    "start_date": "2026-11-01",
    "end_date": "2026-11-15",
    "status": "inactive",
    "final_price": 8.99
  }'
```

| Result | Code |
|--------|------|
| Updated | `200 OK` with the updated promotion |
| No promotion with that id | `404 Not Found` |
| Invalid body | `400 Bad Request` |
| Missing or wrong `Content-Type` | `415 Unsupported Media Type` |

### `DELETE /promotions/{promotion_id}`

Deletes a promotion. The call is idempotent: deleting an id that does not
exist still returns `204`, so a client can retry safely.

```bash
curl -i -X DELETE http://localhost:8080/promotions/1
```

```http
HTTP/1.1 204 NO CONTENT
```

### Error responses

The default Flask error pages are overridden so that errors are JSON too.
Every error has the same shape:

```json
{
  "status": 404,
  "error": "Not Found",
  "message": "404 Not Found: Promotion with ID [999] was not found"
}
```

| Code | When |
|------|------|
| `400 Bad Request` | The body is missing a field, has a bad date or number, is not valid JSON, or violates a database constraint (for example a duplicate `promotion_id`). |
| `404 Not Found` | No promotion has that id, or the URL does not exist. |
| `405 Method Not Allowed` | The method is not supported on that URL, e.g. `DELETE /promotions`. |
| `415 Unsupported Media Type` | `Content-Type` is missing or is not `application/json`. |
| `500 Internal Server Error` | Something unexpected happened on the server. |

Quick sad-path checks you can run against a live service:

```bash
curl -i http://localhost:8080/nope                       # 404 as JSON
curl -i -X DELETE http://localhost:8080/promotions       # 405 as JSON
curl -i -X POST http://localhost:8080/promotions -d '{}' # 415, no Content-Type
curl -i -X POST http://localhost:8080/promotions \
  -H "Content-Type: application/json" -d '{bad'          # 400, malformed JSON
```

## Running the service

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Visual Studio Code](https://code.visualstudio.com/) with the
  [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension

Everything else (Python 3.12, PostgreSQL 15, the Python packages in the
`Pipfile`) is provided by the development container.

### Start the development container

```bash
git clone https://github.com/CSCI-GA-2820-FA26-003/promotions.git
cd promotions
code .
```

When VS Code asks, choose **Reopen in Container**. The container builds from
`.devcontainer/Dockerfile`, installs the `Pipfile` dependencies, and starts a
PostgreSQL sidecar (`.devcontainer/docker-compose.yml`). The `DATABASE_URI`
environment variable is already set inside the container to point at it.

### Start the service

Inside the container terminal:

```bash
honcho start
```

`honcho` reads the `Procfile` and runs `gunicorn` on port 8080. Open
<http://localhost:8080/> in a browser; you should see the service information
JSON from the [root URL](#get-). Stop it with `Ctrl+C`.

To wipe and recreate the database tables:

```bash
flask db-create
```

## Testing and linting

Tests live in the `tests/` folder and use the standard `unittest` style with
`pytest` as the runner. `tests/test_models.py` tests the model and
`tests/test_routes.py` tests the REST API; they are kept separate on purpose.
`tests/factories.py` builds realistic fake promotions with
[factory_boy](https://factoryboy.readthedocs.io/).

```bash
make test     # run the whole suite with coverage; fails below 95%
make lint     # flake8 + pylint; the target is a 10.00/10 rating
```

Run a single file or test while developing:

```bash
pytest tests/test_routes.py
pytest tests/test_routes.py -k test_create_promotion
```

The tests create the tables themselves on the database named in
`DATABASE_URI` and clear the `promotions` table before every test, so each
test starts from an empty table.

## Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URI` | `postgresql+psycopg://postgres:postgres@localhost:5432/postgres` | SQLAlchemy connection string. The dev container sets it to the PostgreSQL sidecar. |
| `PORT` | `8080` | Port `gunicorn` binds to (`Procfile`). |
| `FLASK_APP` | `wsgi:app` | Entry point for the `flask` CLI (set in `.flaskenv`). |
| `SECRET_KEY` | `sup3r-s3cr3t` | Flask session secret. Override outside development. |

Logging is configured in `service/common/log_handlers.py` at the level set by
`LOGGING_LEVEL` in `service/config.py` (`INFO`). Every request, every model
action and every error is logged, which is what you will want when debugging
a cloud deployment later.

Copy `dot-env-example` to `.env` to set these locally; `.env` is git-ignored.

## Project layout

```text
.devcontainer/          - VS Code Dev Container: Dockerfile + docker-compose with PostgreSQL
.github/ISSUE_TEMPLATE/ - User Story and Bug Report issue templates
Makefile                - make test / make lint / make run
Pipfile, Pipfile.lock   - Python dependencies (pipenv)
Procfile                - honcho/gunicorn process definition
setup.cfg               - pytest, coverage, pylint, flake8 and black settings
wsgi.py                 - WSGI entry point that calls create_app()

service/                - the Flask application package
├── __init__.py         - create_app(): config, database, routes, error handlers, logging
├── config.py           - configuration read from environment variables
├── models.py           - Promotions SQLAlchemy model and DataValidationError
├── routes.py           - REST API endpoints
└── common/
    ├── cli_commands.py - `flask db-create`
    ├── error_handlers.py - JSON handlers for 400, 404, 405, 415 and 500
    ├── log_handlers.py - logging setup
    └── status.py       - HTTP status code constants

tests/                  - unit tests (pytest + unittest)
├── factories.py        - PromotionsFactory for fake test data
├── test_cli_commands.py- tests for the CLI command
├── test_models.py      - tests for the model
└── test_routes.py      - tests for the REST API
```

## Development workflow

The squad works in two-week sprints tracked on a ZenHub Kanban board.

1. Take the top story from the Sprint Backlog, assign it to yourself and move it to **In Progress**.
2. Create a feature branch from `master`. Never commit to `master` directly.
3. Write the failing test first, then the code that makes it pass (`make test`), then `make lint`.
4. Push the branch and open a Pull Request. Connect the story to the PR with ZenHub's **Connect with an Issue** so it moves to **Review/QA**.
5. Ask a squad member to review in Slack. Do not approve or merge your own PR.
6. After the merge, delete the branch and move the story to **Done**. It is closed by the Product Owner after the Sprint Review.

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
