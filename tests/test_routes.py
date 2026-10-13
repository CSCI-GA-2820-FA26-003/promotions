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
TestPromotions API Service Test Suite
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from wsgi import app
from service.common import status
from service.models import db, Promotions
from .factories import PromotionsFactory

BASE_URL = "/promotions"

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestYourPromotionsService(TestCase):
    """REST API Server Tests"""

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
    # Utility function to bulk create promotions
    ############################################################
    def _create_promotions(self, count: int = 1) -> list:
        """Factory method to create promotions in bulk"""
        promotions = []
        for _ in range(count):
            test_promotion = PromotionsFactory()
            response = self.client.post(BASE_URL, json=test_promotion.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test promotion",
            )
            promotions.append(test_promotion)
        return promotions

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_promotion(self):
        """It should Create a new Promotion"""
        test_promotion = PromotionsFactory()
        logging.debug("Test Promotion: %s", test_promotion.serialize())
        response = self.client.post(BASE_URL, json=test_promotion.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_promotion = response.get_json()
        self.assertEqual(new_promotion["product_id"], test_promotion.product_id)
        self.assertEqual(new_promotion["promotion_id"], test_promotion.promotion_id)
        self.assertEqual(
            new_promotion["promotion_description"], test_promotion.promotion_description
        )
        self.assertEqual(new_promotion["campaign"], test_promotion.campaign)
        self.assertEqual(
            new_promotion["start_date"], test_promotion.start_date.isoformat()
        )
        self.assertEqual(new_promotion["end_date"], test_promotion.end_date.isoformat())
        self.assertEqual(new_promotion["status"], test_promotion.status)
        self.assertAlmostEqual(
            new_promotion["final_price"],
            float(test_promotion.final_price),
        )
        self.assertIsNotNone(new_promotion["created_at"])

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), new_promotion)
        self.assertEqual(new_promotion["product_id"], test_promotion.product_id)
        self.assertEqual(new_promotion["promotion_id"], test_promotion.promotion_id)
        self.assertEqual(
            new_promotion["promotion_description"], test_promotion.promotion_description
        )
        self.assertEqual(new_promotion["campaign"], test_promotion.campaign)
        self.assertEqual(
            new_promotion["start_date"], test_promotion.start_date.isoformat()
        )
        self.assertEqual(new_promotion["end_date"], test_promotion.end_date.isoformat())
        self.assertEqual(new_promotion["status"], test_promotion.status)
        self.assertAlmostEqual(
            new_promotion["final_price"],
            float(test_promotion.final_price),
        )
        self.assertIsNotNone(new_promotion["created_at"])

    def test_create_promotion_duplicate(self):
        """It should not Create a duplicate promotion"""
        body = PromotionsFactory().serialize()
        response = self.client.post(BASE_URL, json=body)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.post(BASE_URL, json=body)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_promotion_missing_data(self):
        """It should not Create a Promotion with an empty body"""
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_promotion_no_content(self):
        """It should not Create a Promotion without Content-Type"""
        response = self.client.post(BASE_URL, data="hello")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_promotion_wrong_content(self):
        """It should not Create a Promotion with the wrong Content-Type"""
        response = self.client.post(BASE_URL, data="hello", content_type="text/plain")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_promotion_missing_field(self):
        """It should not Create a Promotion missing a required field"""
        body = PromotionsFactory().serialize()
        del body["campaign"]
        response = self.client.post(BASE_URL, json=body)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_promotion_wrong_date(self):
        """It should not Create a Promotion with a wrong date"""
        body = PromotionsFactory().serialize()
        body["start_date"] = "wrong-date-check"
        response = self.client.post(BASE_URL, json=body)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_promotion_malformed_json(self):
        """It should not Create a Promotion with wrong Json body"""
        response = self.client.post(
            BASE_URL, data="{bad", content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.is_json)

    # ----------------------------------------------------------
    # TEST RETRIEVE BY ID
    # ----------------------------------------------------------
    def test_get_promotion_by_id(self):
        """It should retrieve by promotion ID rather than the product primary key"""
        promotion = PromotionsFactory(product_id=101, promotion_id=202)
        promotion.create()
        expected = promotion.serialize()
        response = self.client.get(f"{BASE_URL}/202")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json(), expected)
        self.assertEqual(len(Promotions.all()), 1)
        db.session.expire_all()
        self.assertEqual(Promotions.find(101).serialize(), expected)
        response = self.client.get(f"{BASE_URL}/101")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_promotion_missing(self):
        """It should return a JSON 404 for an unknown promotion ID"""
        response = self.client.get(f"{BASE_URL}/999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.is_json)
        self.assertIn("message", response.get_json())

    def test_get_cancelled_promotion(self):
        """It should retrieve a cancelled promotion without changing its status"""
        promotion = PromotionsFactory(status="cancelled")
        promotion.create()
        response = self.client.get(f"{BASE_URL}/{promotion.promotion_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), promotion.serialize())
        self.assertEqual(response.get_json()["status"], "cancelled")

    def test_get_promotion_invalid_id(self):
        """It should reject invalid IDs as JSON client errors without changing data"""
        promotion = PromotionsFactory()
        promotion.create()
        expected = promotion.serialize()
        for value, expected_status in (
            ("0", status.HTTP_400_BAD_REQUEST),
            ("-1", status.HTTP_404_NOT_FOUND),
            ("abc", status.HTTP_404_NOT_FOUND),
            ("1.5", status.HTTP_404_NOT_FOUND),
        ):
            with self.subTest(value=value):
                response = self.client.get(f"{BASE_URL}/{value}")
                self.assertEqual(response.status_code, expected_status)
                self.assertTrue(response.is_json)
                self.assertIn("message", response.get_json())
                db.session.expire_all()
                self.assertEqual(Promotions.all()[0].serialize(), expected)
                self.assertEqual(len(Promotions.all()), 1)

    # ----------------------------------------------------------
    # TEST LIST
    # ----------------------------------------------------------
    def test_get_promotion_list(self):
        """It should Get a list of Promotions"""
        self._create_promotions(5)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_get_promotion_list_empty(self):
        """It should return an empty list when there are no Promotions"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_list_promotions_method_not_allowed(self):
        """It should not allow DELETE on the promotions collection"""
        response = self.client.delete(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        # Test for json response
        self.assertTrue(response.is_json)
        self.assertIn("message", response.get_json())
