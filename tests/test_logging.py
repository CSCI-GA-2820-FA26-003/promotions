"""Verify observable request/action logs and logging configuration."""
import io
import logging
from unittest import TestCase
from unittest.mock import patch
from flask import Flask
from wsgi import app
from service.common.log_handlers import init_logging
from service.models import db
from tests.factories import PromotionsFactory


class TestServiceLogging(TestCase):
    """Logging should work in development as well as under Gunicorn."""

    def test_request_logging(self):
        """Every route, including future API prefixes and misses, logs method/path."""
        with self.assertLogs(app.logger.name, level="INFO") as captured:
            app.test_client().get("/api/promotions/999999")
            app.test_client().get("/health")
        output = "\n".join(captured.output)
        self.assertIn("GET /api/promotions/999999", output)
        self.assertIn("GET /health", output)

    def test_model_logging(self):
        """Committed model actions reach the same configured service logger."""
        with app.app_context():
            promotion = PromotionsFactory()
            with self.assertLogs(app.logger.name, level="INFO") as captured:
                promotion.create()
                promotion.update()
                promotion.delete()
            db.session.remove()
        output = "\n".join(captured.output)
        for action in ("Created promotion", "Updated promotion", "Deleted promotion"):
            self.assertIn(action, output)

    def test_error_logging(self):
        """Error handlers include the failure reason at ERROR level."""
        with self.assertLogs(app.logger.name, level="ERROR") as captured:
            response = app.test_client().get("/not-a-real-route")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", "\n".join(captured.output).lower())

    def test_development_handler_and_level(self):
        """A standalone process has a formatted handler and honors DEBUG."""
        standalone = Flask("logging-test")
        source = logging.getLogger("empty-test-gunicorn")
        with patch.dict("os.environ", {"LOGGING_LEVEL": "DEBUG"}):
            init_logging(standalone, source.name)
        self.assertEqual(standalone.logger.level, logging.DEBUG)
        stream = io.StringIO()
        handler = standalone.logger.handlers[0]
        with patch.object(handler, "stream", stream):
            standalone.logger.debug("Debug logging enabled")
            standalone.logger.error("Connection postgresql+psycopg://user:private-password@db/test failed")
        self.assertIn("[DEBUG]", stream.getvalue())
        self.assertIn("Debug logging enabled", stream.getvalue())
        self.assertNotIn("private-password", stream.getvalue())
        self.assertIn("REDACTED", stream.getvalue())

    def test_cancel_logging(self):
        """Cancellation emits a successful action log with its promotion ID."""
        with app.app_context():
            promotion = PromotionsFactory()
            promotion.create()
            promotion_id = promotion.promotion_id
            with self.assertLogs(app.logger.name, level="INFO") as captured:
                response = app.test_client().put(f"/promotions/{promotion_id}/cancel")
            self.assertEqual(response.status_code, 200)
            self.assertIn(f"Promotion with ID {promotion_id} cancelled", "\n".join(captured.output))
            db.session.delete(promotion)
            db.session.commit()
            db.session.remove()
