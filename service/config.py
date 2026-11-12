"""
Global Configuration for Application
"""
import os
import logging

# Get configuration from environment
DATABASE_URI = os.getenv(
    "DATABASE_URI",
    "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"
)

# Configure SQLAlchemy
SQLALCHEMY_DATABASE_URI = DATABASE_URI
SQLALCHEMY_TRACK_MODIFICATIONS = False
# Reconnect cleanly when the PostgreSQL Pod has been replaced.
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

# Stop Flask-RESTX appending "did you mean ...?" to our 404 error messages
RESTX_ERROR_404_HELP = False

# Secret for session management
SECRET_KEY = os.getenv("SECRET_KEY", "sup3r-s3cr3t")
LOGGING_LEVEL = logging.INFO
