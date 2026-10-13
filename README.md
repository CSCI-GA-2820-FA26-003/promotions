# NYU DevOps Project Template

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

This is a skeleton you can use to start your projects.

**Note:** _Feel free to overwrite this `README.md` file with the one that describes your project._

## Overview

This project template contains starter code for your class project. The `/service` folder contains your `models.py` file for your model and a `routes.py` file for your service. The `/tests` folder has test case starter code for testing the model and the service separately. All you need to do is add your functionality. You can use the [lab-flask-tdd](https://github.com/nyu-devops/lab-flask-tdd) for code examples to copy from.

## Automatic Setup

The best way to use this repo is to start your own repo using it as a git template. To do this just press the green **Use this template** button in GitHub and this will become the source for your repository.

## Manual Setup

You can also clone this repository and then copy and paste the starter code into your project repo folder on your local computer. Be careful not to copy over your own `README.md` file so be selective in what you copy.

There are 4 hidden files that you will need to copy manually if you use the Mac Finder or Windows Explorer to copy files from this folder into your repo folder.

These should be copied using a bash shell as follows:

```bash
    cp .gitignore  ../<your_repo_folder>/
    cp .flaskenv ../<your_repo_folder>/
    cp .gitattributes ../<your_repo_folder>/
```

## Contents

The project contains the following:

```text
.gitignore          - this will ignore vagrant and other metadata files
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to gix Windows CRLF issues
.devcontainers/     - Folder with support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
pyproject.toml      - Poetry list of Python libraries required by your code

service/                   - service python package
├── __init__.py            - package initializer
├── config.py              - configuration parameters
├── models.py              - module with business models
├── routes.py              - module with service routes
└── common                 - common code package
    ├── cli_commands.py    - Flask command to recreate all tables
    ├── error_handlers.py  - HTTP error handling code
    ├── log_handlers.py    - logging setup code
    └── status.py          - HTTP status constants

tests/                     - test cases package
├── __init__.py            - package initializer
├── factories.py           - Factory for testing with fake objects
├── test_cli_commands.py   - test suite for the CLI
├── test_models.py         - test suite for business models
└── test_routes.py         - test suite for service routes
```

## Retrieve a promotion by ID

`GET /promotions/{id}` returns one promotion as JSON. The path uses the unique
`promotion_id`, not the model's `product_id` primary key. No request body is needed.

```bash
curl -i http://localhost:8080/promotions/202
```

A successful response is `200 OK` with `Content-Type: application/json`:

```json
{
  "product_id": 101,
  "promotion_id": 202,
  "promotion_description": "discount",
  "campaign": "flash sale",
  "start_date": "2026-10-01",
  "end_date": "2026-10-14",
  "status": "active",
  "final_price": 19.99,
  "created_at": "2026-09-30T12:00:00"
}
```

An unknown ID returns `404 Not Found` with a JSON error:

```json
{
  "status": 404,
  "error": "Not Found",
  "message": "404 Not Found: Promotion with ID [999] was not found"
}
```

Zero returns a JSON `400 Bad Request`; negative, non-integer, or malformed IDs
return a JSON `404 Not Found` from the router. A stored cancelled promotion remains
retrievable, with its status included. GET requests do not change database records.
After creating a promotion, the POST response's `Location` header now points to
this endpoint.

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
