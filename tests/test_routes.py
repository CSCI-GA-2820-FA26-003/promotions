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

    # ----------------------------------------------------------
    # TEST ROOT URL
    # ----------------------------------------------------------

    def test_index(self):
        """It should return service information as JSON from the root URL"""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.is_json)
        data = resp.get_json()
        self.assertEqual(data["name"], "Promotions REST API Service")
        self.assertEqual(data["version"], "1.0")
        self.assertIn("description", data)
        # paths points at the promotions collection so a client can discover the API
        self.assertTrue(data["paths"].endswith(BASE_URL))

    def test_index_method_not_allowed(self):
        """It should return a JSON 405 when the root URL is called with POST"""
        resp = self.client.post("/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(resp.is_json)
        self.assertIn("message", resp.get_json())

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------

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
        """It should retrieve by promotion ID"""
        # product_id=101 is a regular column; promotion_id=202 is the primary key.
        # The values differ on purpose so a lookup on the wrong column fails loudly.
        promotion = PromotionsFactory(product_id=101, promotion_id=202)
        promotion.create()
        expected = promotion.serialize()  # the dictionary we expect the API to return

        # GET by promotion_id (202): should find the row
        response = self.client.get(f"{BASE_URL}/202")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json(), expected)

        # The GET must not create or delete anything: still exactly one row
        self.assertEqual(len(Promotions.all()), 1)

        # Clear the session cache so find() reads a fresh copy from the database,
        # then confirm the stored row is unchanged (find uses the primary key, 202)
        db.session.expire_all()
        self.assertEqual(Promotions.find(202).serialize(), expected)

        # GET by product_id (101): not a valid key, so no row matches -> 404
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

    # ----------------------------------------------------------
    # TEST DELETE
    # ----------------------------------------------------------

    def test_delete_promotion(self):
        """It should Delete a Promotion"""
        test_promotion = self._create_promotions(1)[0]
        response = self.client.delete(f"{BASE_URL}/{test_promotion.promotion_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)
        # make sure they are deleted
        response = self.client.get(f"{BASE_URL}/{test_promotion.promotion_id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_non_existing_promotion(self):
        """It should Delete a Promotion even if it doesn't exist"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

    # ----------------------------------------------------------
    # TEST UPDATE
    # ----------------------------------------------------------

    def test_update_existing_promotion(self):
        """It should Update a Promotion"""
        test_promotion = PromotionsFactory()  # create a promotion

        # add it to the database
        test_promotion.create()

        # now we try to update the promotion in the database
        response = self.client.put(
            # we pass both the promotion id and the promotion data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=test_promotion.serialize(),
        )

        # check that the update was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # let's also check the update is persisted in the database by retrieving the promotion and checking its data
        # is the same as we just sent in the update request
        db.session.remove()  # remove the session cache so we get a fresh copy from the database
        self.assertEqual(
            response.get_json(),
            Promotions.find(test_promotion.promotion_id).serialize(),
        )

        # remove the test_promotion from the database
        test_promotion.delete()

    def test_update_non_existing_promotion(self):
        """It should fail to update a non-existing Promotion"""
        test_promotion = PromotionsFactory()  # create a promotion
        test_promotion.promotion_id = 999999  # set to a non-existing ID

        # now we try to update a promotion not in the database
        response = self.client.put(
            # we pass both the promotion id and the promotion data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=test_promotion.serialize(),
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_invalid_field_promotion(self):
        """It should fail to update a promotion with invalid data"""
        test_promotion = PromotionsFactory()  # create a valid promotion
        test_promotion.create()  # add it to the database

        # we obtain the python dict of the test_promotion's data and modify each one to make them invalid
        invalid_body = (
            test_promotion.serialize()
        )  # get the valid data for the promotion
        invalid_body["product_id"] = "asdf"
        invalid_body["start_date"] = 123
        invalid_body["end_date"] = 123
        invalid_body["status"] = 123
        invalid_body["final_price"] = "asdf"
        invalid_body["promotion_description"] = 123
        invalid_body["campaign"] = 12
        invalid_body["created_at"] = "asdf"

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )

        test_promotion.delete()  # remove the test_promotion from the database

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
