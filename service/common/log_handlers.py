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
Log Handlers

This module contains utility functions to set up logging
consistently
"""
import logging
import os
import re
from flask import request


class SafeFormatter(logging.Formatter):
    """Format logs without exposing database connection credentials."""

    def format(self, record):
        message = super().format(record)
        return re.sub(
            r"(?:postgres(?:ql)?(?:\+\w+)?|mysql(?:\+\w+)?)://[^\s\"']+",
            "[REDACTED DATABASE URI]", message,
        )


def init_logging(app, logger_name: str):
    """Configure a shared format and level, with a standalone fallback."""
    app.logger.propagate = False
    source_logger = logging.getLogger(logger_name)
    app.logger.handlers = list(source_logger.handlers) or [logging.StreamHandler()]
    level = os.getenv("LOGGING_LEVEL", app.config.get("LOGGING_LEVEL", "INFO"))
    if isinstance(level, str):
        level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
    app.logger.setLevel(level)
    formatter = SafeFormatter(
        "[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s",
        "%Y-%m-%d %H:%M:%S %z",
    )
    for handler in app.logger.handlers:
        handler.setLevel(logging.NOTSET)
        handler.setFormatter(formatter)
    app.logger.info("Logging handler established")
    app.logger.debug("Debug logging enabled")


def log_request():
    """Record every request independently of route implementation or prefix."""
    from flask import current_app  # pylint: disable=import-outside-toplevel
    promotion_id = (request.view_args or {}).get("promotion_id")
    current_app.logger.info(
        "Request %s %s promotion_id=%s", request.method, request.path, promotion_id
    )
    current_app.logger.debug("Handling endpoint %s", request.endpoint)
