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
Flask-RESTX API Test Suite

Tests for what the Flask-RESTX refactor added on top of the behaviour that
tests/test_routes.py already covers: the /api prefix, the validation of
request payloads, the single JSON format for every error, and the API docs.
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from unittest.mock import patch
from urllib.parse import urlparse
from flask_restx import abort as restx_abort
from wsgi import app
from service.common import status
from service.models import db, Promotions
from .factories import PromotionsFactory

BASE_URL = "/api/promotions"

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods


class TestRestxApi(TestCase):
    """Flask-RESTX API Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Promotions).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ############################################################
    # Utility functions
    ############################################################
    def _payload(self, **changes) -> dict:
        """A valid body for creating a promotion, with the given changes applied"""
        data = PromotionsFactory().serialize()
        data.pop("promotion_id")
        data.pop("created_at")
        data.update(changes)
        return data

    def _assert_error(self, response, code: int, name: str) -> dict:
        """Checks that a response is an error in the format every error shares"""
        self.assertEqual(response.status_code, code)
        self.assertTrue(response.is_json)
        body = response.get_json()
        self.assertEqual(set(body), {"status", "error", "message"})
        self.assertEqual(body["status"], code)
        self.assertEqual(body["error"], name)
        self.assertIsInstance(body["message"], str)
        self.assertTrue(body["message"])
        return body

    # ----------------------------------------------------------
    # TEST THE /api PREFIX
    # ----------------------------------------------------------
    def test_endpoints_use_the_api_prefix(self):
        """It should serve every promotion endpoint under /api"""
        response = self.client.get("/api/swagger.json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        spec = response.get_json()
        self.assertEqual(spec["basePath"], "/api")

        expected = {
            "/promotions": {"get", "post"},
            "/promotions/{promotion_id}": {"get", "put", "delete"},
            "/promotions/{promotion_id}/cancel": {"put"},
        }
        for path, methods in expected.items():
            with self.subTest(path=path):
                self.assertIn(path, spec["paths"])
                # "parameters" sits beside the methods when a path has an id
                documented = set(spec["paths"][path]) - {"parameters"}
                self.assertEqual(documented, methods)

    def test_paths_without_the_prefix_are_gone(self):
        """It should no longer answer on the paths used before the /api prefix"""
        promotion = PromotionsFactory()
        promotion.create()
        promotion_id = promotion.promotion_id

        for method, url in (
            ("get", "/promotions"),
            ("post", "/promotions"),
            ("get", f"/promotions/{promotion_id}"),
            ("put", f"/promotions/{promotion_id}"),
            ("delete", f"/promotions/{promotion_id}"),
            ("put", f"/promotions/{promotion_id}/cancel"),
        ):
            with self.subTest(method=method, url=url):
                response = self.client.open(url, method=method.upper(), json={})
                self._assert_error(response, status.HTTP_404_NOT_FOUND, "Not Found")

        # nothing was changed or deleted through the old paths
        db.session.expire_all()
        self.assertEqual(len(Promotions.all()), 1)
        self.assertNotEqual(Promotions.find(promotion_id).status, "cancelled")

    def test_location_header_uses_the_api_prefix(self):
        """It should return a Location under /api for a new promotion"""
        response = self.client.post(BASE_URL, json=self._payload())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        promotion_id = response.get_json()["promotion_id"]
        location = urlparse(response.headers["Location"])
        self.assertEqual(location.path, f"{BASE_URL}/{promotion_id}")

    def test_admin_ui_and_api_docs_are_separate_pages(self):
        """It should keep the admin UI at / and serve the API docs at /apidocs"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b'id="promotion_id"', response.data)
        self.assertNotIn(b"swagger-ui", response.data)

        response = self.client.get("/apidocs")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/html", response.content_type)
        self.assertIn(b"swagger-ui", response.data)
        self.assertIn(b"/api/swagger.json", response.data)

    def test_health_is_not_part_of_the_api(self):
        """It should keep /health outside the /api prefix and the API docs"""
        response = self.client.get("/api/health")
        self._assert_error(response, status.HTTP_404_NOT_FOUND, "Not Found")
        spec = self.client.get("/api/swagger.json").get_json()
        self.assertNotIn("/health", spec["paths"])

    # ----------------------------------------------------------
    # TEST PAYLOAD VALIDATION
    # ----------------------------------------------------------
    def test_create_rejects_a_wrong_type(self):
        """It should not Create a Promotion when a field has the wrong type"""
        for field, value in (
            ("product_id", "abc"),
            ("product_id", 1.5),
            ("start_date", 20261120),
            ("status", 5),
            ("campaign", ["black friday"]),
            ("promotion_description", None),
        ):
            with self.subTest(field=field, value=value):
                response = self.client.post(BASE_URL, json=self._payload(**{field: value}))
                body = self._assert_error(
                    response, status.HTTP_400_BAD_REQUEST, "Bad Request"
                )
                self.assertIn(field, body["message"])
        self.assertEqual(Promotions.all(), [])

    def test_create_reports_every_invalid_field(self):
        """It should name each field that failed validation in the message"""
        data = self._payload(product_id="abc")
        del data["campaign"]
        del data["end_date"]
        response = self.client.post(BASE_URL, json=data)
        body = self._assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")
        for field in ("product_id", "campaign", "end_date"):
            self.assertIn(field, body["message"])

    def test_create_rejects_a_blank_field(self):
        """It should not Create a Promotion when a required field is blank"""
        response = self.client.post(BASE_URL, json=self._payload(campaign=""))
        body = self._assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")
        self.assertIn("campaign", body["message"])
        self.assertEqual(Promotions.all(), [])

    def test_create_rejects_a_bad_price(self):
        """It should not Create a Promotion when the price is not a number"""
        for value in ("free", True, [19.99], {"amount": 19.99}):
            with self.subTest(value=value):
                response = self.client.post(BASE_URL, json=self._payload(final_price=value))
                self._assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")
        self.assertEqual(Promotions.all(), [])

    def test_create_accepts_a_numeric_string_price(self):
        """It should still Create a Promotion when the price is a numeric string"""
        response = self.client.post(BASE_URL, json=self._payload(final_price="19.99"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.get_json()["final_price"], 19.99)

    def test_create_ignores_fields_the_service_assigns(self):
        """It should ignore promotion_id and created_at sent by the client"""
        data = self._payload(promotion_id=987654, created_at="2001-01-01T00:00:00")
        response = self.client.post(BASE_URL, json=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = response.get_json()
        self.assertNotEqual(created["promotion_id"], 987654)
        self.assertNotEqual(created["created_at"], "2001-01-01T00:00:00")

    def test_update_rejects_a_body_that_is_not_an_object(self):
        """It should not Update a Promotion when the body is not a JSON object"""
        promotion = PromotionsFactory()
        promotion.create()
        expected = promotion.serialize()
        for body in ([1, 2], "campaign", 5):
            with self.subTest(body=body):
                response = self.client.put(
                    f"{BASE_URL}/{promotion.promotion_id}", json=body
                )
                self._assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")
        db.session.expire_all()
        self.assertEqual(Promotions.find(promotion.promotion_id).serialize(), expected)

    def test_update_accepts_a_partial_body(self):
        """It should Update only the fields that are sent"""
        promotion = PromotionsFactory(status="active")
        promotion.create()
        expected = promotion.serialize()
        expected["campaign"] = "winter sale"

        response = self.client.put(
            f"{BASE_URL}/{promotion.promotion_id}", json={"campaign": "winter sale"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), expected)

    def test_update_checks_the_body_before_the_id(self):
        """It should answer 400, not 404, for an invalid body on an unknown id"""
        response = self.client.put(f"{BASE_URL}/999999", json={"product_id": "abc"})
        self._assert_error(response, status.HTTP_400_BAD_REQUEST, "Bad Request")

    def test_json_content_type_with_a_charset_is_accepted(self):
        """It should accept application/json with a charset parameter"""
        response = self.client.post(
            BASE_URL,
            json=self._payload(),
            content_type="application/json; charset=utf-8",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    # ----------------------------------------------------------
    # TEST THE ERROR FORMAT
    # ----------------------------------------------------------
    def test_errors_share_one_format(self):
        """It should return every error as the same JSON document"""
        bad_request = (status.HTTP_400_BAD_REQUEST, "Bad Request")
        not_found = (status.HTTP_404_NOT_FOUND, "Not Found")
        not_allowed = (status.HTTP_405_METHOD_NOT_ALLOWED, "Method not Allowed")
        unsupported = (status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported media type")

        cases = (
            # raised by the resources
            ("an unknown promotion", "GET", f"{BASE_URL}/999999", {}, not_found),
            ("an id of zero", "GET", f"{BASE_URL}/0", {}, bad_request),
            ("update unknown", "PUT", f"{BASE_URL}/999999", {"json": {}}, not_found),
            ("cancel unknown", "PUT", f"{BASE_URL}/999999/cancel", {}, not_found),
            ("a bad active flag", "GET", f"{BASE_URL}?active=false", {}, bad_request),
            # raised by the model
            ("a bad date", "POST", BASE_URL, {"json": self._payload(start_date="soon")}, bad_request),
            # raised by Flask-RESTX validation
            ("an empty body", "POST", BASE_URL, {"json": {}}, bad_request),
            ("a bad query string", "GET", f"{BASE_URL}?product_id=abc", {}, bad_request),
            ("malformed JSON", "POST", BASE_URL, {"data": "{bad", "content_type": "application/json"}, bad_request),
            ("no Content-Type", "POST", BASE_URL, {"data": "hello"}, unsupported),
            ("a wrong Content-Type", "PUT", f"{BASE_URL}/1", {"data": "x", "content_type": "text/plain"}, unsupported),
            # raised by the URL routing, inside and outside the API
            ("a wrong method on the API", "DELETE", BASE_URL, {}, not_allowed),
            ("a wrong method on an action", "GET", f"{BASE_URL}/1/cancel", {}, not_allowed),
            ("a wrong method on the UI", "POST", "/", {}, not_allowed),
            ("an id that is not an integer", "GET", f"{BASE_URL}/abc", {}, not_found),
            ("an unknown API URL", "GET", "/api/nope", {}, not_found),
            ("an unknown URL", "GET", "/nope", {}, not_found),
        )
        for name, method, url, kwargs, (code, error) in cases:
            with self.subTest(case=name):
                response = self.client.open(url, method=method, **kwargs)
                self._assert_error(response, code, error)

    def test_error_messages_are_not_decorated(self):
        """It should not let Flask-RESTX append URL suggestions to a 404 message"""
        response = self.client.get(f"{BASE_URL}/999999")
        body = self._assert_error(response, status.HTTP_404_NOT_FOUND, "Not Found")
        self.assertEqual(
            body["message"], "404 Not Found: Promotion with ID [999999] was not found"
        )

    @patch("service.routes.Promotions.all")
    def test_flask_restx_abort_uses_the_same_format(self, all_mock):
        """It should format errors raised with the Flask-RESTX abort() the same way"""
        all_mock.side_effect = lambda: restx_abort(
            status.HTTP_409_CONFLICT, "Promotions are locked"
        )
        response = self.client.get(BASE_URL)
        body = self._assert_error(response, status.HTTP_409_CONFLICT, "Conflict")
        self.assertEqual(body["message"], "409 Conflict: Promotions are locked")

    @patch("service.routes.Promotions.all")
    def test_unexpected_error_is_a_json_500(self, all_mock):
        """It should return a JSON 500 that does not leak the cause of a crash"""
        all_mock.side_effect = RuntimeError("password=hunter2")
        # Behave as in production, where exceptions are not re-raised
        app.config["PROPAGATE_EXCEPTIONS"] = False
        self.addCleanup(app.config.__setitem__, "PROPAGATE_EXCEPTIONS", None)

        response = self.client.get(BASE_URL)
        body = self._assert_error(
            response, status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal Server Error"
        )
        self.assertNotIn("hunter2", body["message"])
