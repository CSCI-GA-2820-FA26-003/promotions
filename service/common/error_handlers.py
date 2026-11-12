######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
"""
Module: error_handlers

Every error leaves the service as the same JSON document:

    {"status": 404, "error": "Not Found", "message": "404 Not Found: ..."}

Flask-RESTX handles the errors raised inside its resources (the /api
endpoints) and Flask handles the rest (/, /health and unknown URLs), so
each framework needs its own handlers. They all build the response with
error_response(), which is what keeps the format the same everywhere.
"""

from flask import current_app as app  # Import Flask application
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.http import HTTP_STATUS_CODES
from service import api
from service.models import DataValidationError
from . import status

# The "error" text this service has always used where it differs from the
# standard reason phrase. Every other code uses the standard phrase.
ERROR_NAMES = {
    status.HTTP_405_METHOD_NOT_ALLOWED: "Method not Allowed",
    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: "Unsupported media type",
}


def error_response(code, message):
    """Logs an error and builds the JSON response that every error shares"""
    if code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        app.logger.error(message)
    else:
        app.logger.warning(message)

    name = ERROR_NAMES.get(code) or HTTP_STATUS_CODES.get(code, "Unknown Error")
    return {"status": code, "error": name, "message": message}, code


######################################################################
# Flask Error Handlers: errors raised outside the API
######################################################################
@app.errorhandler(HTTPException)
def http_error(error):
    """Handles HTTP errors outside the API, e.g. an unknown URL or a POST to /"""
    return error_response(error.code, str(error))


######################################################################
# Flask-RESTX Error Handlers: errors raised inside the API resources
######################################################################
@api.errorhandler(DataValidationError)
def request_validation_error(error):
    """Handles Value Errors from bad data"""
    return error_response(status.HTTP_400_BAD_REQUEST, str(error))


@api.errorhandler(HTTPException)
def api_http_error(error):
    """Handles HTTP errors raised inside the API, including failed validation"""
    details = getattr(error, "data", None)
    if details:
        # Flask-RESTX keeps what failed validation in error.data. Put it in
        # the message, in place of werkzeug's generic description.
        reasons = "; ".join(
            f"{field}: {reason}" if field else reason
            for field, reason in details.get("errors", {}).items()
        )
        described = ": ".join(filter(None, [details.get("message"), reasons]))
        error.description = described or error.description

    body, code = error_response(
        error.code or status.HTTP_500_INTERNAL_SERVER_ERROR, str(error)
    )
    # When error.data is set, Flask-RESTX sends it instead of what a handler
    # returns, so point it at the standard body to keep a single format.
    error.data = body
    return body, code


@api.errorhandler
def api_unexpected_error(_error):
    """Handles any other exception raised inside the API as a 500

    The reason is logged with its traceback by Flask-RESTX and is not sent
    to the client, which gets the standard Internal Server Error text.
    """
    return error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR, str(InternalServerError())
    )
