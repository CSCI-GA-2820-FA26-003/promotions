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
class TestYourResourceService(TestCase):
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

    ######################################################################
    #  P L A C E   T E S T   C A S E S   H E R E
    ######################################################################

    def test_index(self):
        """It should call the home page"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Todo: Add your test cases here...

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

        # Todo: Uncomment this code when get promotion is implemented

        # Check that the location header was correct
        # response = self.client.get(location)
        # self.assertEqual(new_promotion["product_id"], test_promotion.product_id)
        # self.assertEqual(new_promotion["promotion_id"], test_promotion.promotion_id)
        # self.assertEqual(
        #     new_promotion["promotion_description"], test_promotion.promotion_description
        # )
        # self.assertEqual(new_promotion["campaign"], test_promotion.gender.campaign)
        # self.assertEqual(
        #     new_promotion["start_date"], test_promotion.start_date.isoformat()
        # )
        # self.assertEqual(new_promotion["end_date"], test_promotion.end_date.isoformat())
        # self.assertEqual(new_promotion["status"], test_promotion.status)
        # self.assertAlmostEqual(
        #     new_promotion["final_price"],
        #     float(test_promotion.final_price),
        # )
        # self.assertIsNotNone(new_promotion["created_at"])

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
