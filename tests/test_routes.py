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
from unittest.mock import patch
from werkzeug.exceptions import InternalServerError
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

    def test_health(self):
        """It should expose the Kubernetes health-check contract as JSON"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json(), {"status": "OK"})

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
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(response.is_json)
        self.assertIn("already exists", response.get_json()["message"])

    def test_create_promotion_missing_data(self):
        """It should not Create a Promotion with an empty body"""
        response = self.client.post(BASE_URL, json={})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_promotion_no_content(self):
        """It should not Create a Promotion without Content-Type"""
        response = self.client.post(BASE_URL, data="hello")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertTrue(response.is_json)

    def test_create_promotion_wrong_content(self):
        """It should not Create a Promotion with the wrong Content-Type"""
        response = self.client.post(BASE_URL, data="hello", content_type="text/plain")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
        self.assertTrue(response.is_json)

    def test_create_promotion_missing_field(self):
        """It should not Create a Promotion missing a required field"""
        body = PromotionsFactory().serialize()
        del body["campaign"]
        response = self.client.post(BASE_URL, json=body)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.is_json)
        self.assertIn("campaign", response.get_json()["message"])

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

    @patch("service.routes.Promotions.all")
    def test_list_promotions_server_error(self, all_mock):
        """It should return a JSON 500 on an internal error"""
        all_mock.side_effect = InternalServerError("boom")
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data["status"], 500)
        self.assertIn("message", data)

    # ----------------------------------------------------------
    # TEST QUERY (filters on LIST)
    # ----------------------------------------------------------
    def test_query_by_product_id(self):
        """It should Query promotions by product_id"""
        PromotionsFactory(product_id=1).create()
        PromotionsFactory(product_id=1).create()
        PromotionsFactory(product_id=2).create()
        response = self.client.get(BASE_URL, query_string="product_id=1")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        for promotion in data:
            self.assertEqual(promotion["product_id"], 1)

    def test_query_by_status(self):
        """It should Query promotions by status"""
        PromotionsFactory(status="active").create()
        PromotionsFactory(status="active").create()
        PromotionsFactory(status="cancelled").create()
        response = self.client.get(BASE_URL, query_string="status=active")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        for promotion in data:
            self.assertEqual(promotion["status"], "active")

    def test_query_by_campaign(self):
        """It should Query promotions by campaign"""
        PromotionsFactory(campaign="black friday").create()
        PromotionsFactory(campaign="black friday").create()
        PromotionsFactory(campaign="summer sale").create()
        response = self.client.get(BASE_URL, query_string="campaign=black friday")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 2)
        for promotion in data:
            self.assertEqual(promotion["campaign"], "black friday")

    def test_query_combined_filters(self):
        """It should require every supplied filter to match (AND)"""
        PromotionsFactory(product_id=1, status="active", campaign="black friday").create()
        PromotionsFactory(product_id=1, status="cancelled", campaign="black friday").create()
        PromotionsFactory(product_id=2, status="active", campaign="black friday").create()
        response = self.client.get(
            BASE_URL, query_string="product_id=1&status=active&campaign=black friday"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["product_id"], 1)
        self.assertEqual(data[0]["status"], "active")
        self.assertEqual(data[0]["campaign"], "black friday")

    def test_query_no_match(self):
        """It should return an empty list when no promotion matches the filter"""
        PromotionsFactory(product_id=1).create()
        response = self.client.get(BASE_URL, query_string="product_id=999")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_query_unknown_status_value(self):
        """It should return an empty list, not an error, for an unknown status"""
        PromotionsFactory(status="active").create()
        response = self.client.get(BASE_URL, query_string="status=bogus")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json(), [])

    def test_query_invalid_product_id(self):
        """It should return a JSON 400 when product_id is not an integer"""
        PromotionsFactory(product_id=1).create()
        response = self.client.get(BASE_URL, query_string="product_id=abc")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.is_json)
        self.assertIn("message", response.get_json())

    def test_query_unknown_parameter_is_ignored(self):
        """It should ignore query parameters it does not understand"""
        self._create_promotions(3)
        response = self.client.get(BASE_URL, query_string="colour=red")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.get_json()), 3)

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

        # we obtain a python dict with only the updatable fields
        update_payload = {
            "product_id": test_promotion.product_id,
            "start_date": test_promotion.start_date,
            "end_date": test_promotion.end_date,
            "status": test_promotion.status,
            "final_price": test_promotion.final_price,
            "promotion_description": test_promotion.promotion_description,
            "campaign": test_promotion.campaign,
        }

        # now we try to update the promotion in the database
        response = self.client.put(
            # we pass both the promotion id and the promotion data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=update_payload,
        )

        # check that the update was successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # let's also check the update is persisted in the database by retrieving the promotion and checking its data
        # is the same as the one we just sent in the update request
        db.session.remove()  # remove the session cache so we get a fresh copy from the database
        self.assertEqual(
            response.get_json(),
            Promotions.find(test_promotion.promotion_id).serialize(),
        )

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

    def test_update_promotion_id_not_updatable(self):
        """It should fail to update a promotion id"""
        test_promotion = PromotionsFactory()  # create a promotion
        test_promotion.create()  # add it to the database

        # we obtain a python dict with product_id
        update_payload = {
            "promotion_id": test_promotion.promotion_id,
        }

        # now we try to update the promotion_id if the existing promotion
        response = self.client.put(
            # we pass both the promotion id
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=update_payload,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_created_at_not_updatable(self):
        """It should fail to update created_at field"""
        test_promotion = PromotionsFactory()  # create a promotion
        test_promotion.create()  # add it to the database

        # we obtain a python dict with only created_at
        update_payload = {
            "created_at": test_promotion.created_at,
        }

        # now we try to update the created_at field of the promotion
        response = self.client.put(
            # we pass both the promotion id
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=update_payload,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_invalid_product_id_promotion(self):
        """It should fail to update a promotion with invalid product ID data"""
        test_promotion = PromotionsFactory()  # create a valid promotion
        test_promotion.create()  # add it to the database

        # we obtain the python dict of the test_promotion's data and modify the product id to an invalid value
        invalid_body = (
            test_promotion.serialize()
        )  # get the valid data for the promotion

        # remove the non-updatable fields
        invalid_body.pop("promotion_id")
        invalid_body.pop("created_at")
        # assign invalid value to field being tested
        invalid_body["product_id"] = "asdf"

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_invalid_start_date_promotion(self):
        """It should fail to update a promotion with invalid start date data"""
        test_promotion = PromotionsFactory()  # create a valid promotion
        test_promotion.create()  # add it to the database

        # we obtain the python dict of the test_promotion's data and modify the start date to an invalid value
        invalid_body = (
            test_promotion.serialize()
        )  # get the valid data for the promotion

        # remove the non-updatable fields
        invalid_body.pop("promotion_id")
        invalid_body.pop("created_at")
        # assign invalid value to field being tested
        invalid_body["start_date"] = 123

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_invalid_end_date_promotion(self):
        """It should fail to update a promotion with invalid end date data"""
        test_promotion = PromotionsFactory()  # create a valid promotion
        test_promotion.create()  # add it to the database

        # we obtain the python dict of the test_promotion's data and modify the end date to an invalid value
        invalid_body = (
            test_promotion.serialize()
        )  # get the valid data for the promotion

        # remove the non-updatable fields
        invalid_body.pop("promotion_id")
        invalid_body.pop("created_at")
        # assign invalid value to field being tested
        invalid_body["end_date"] = 123

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_invalid_status_promotion(self):
        """It should fail to update a promotion with invalid status data"""
        test_promotion = PromotionsFactory()  # create a valid promotion
        test_promotion.create()  # add it to the database

        # we obtain the python dict of the test_promotion's data and modify the status to an invalid value
        invalid_body = (
            test_promotion.serialize()
        )  # get the valid data for the promotion

        # remove the non-updatable fields
        invalid_body.pop("promotion_id")
        invalid_body.pop("created_at")
        invalid_body["status"] = None

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_invalid_final_price_promotion(self):
        """It should fail to update a promotion with invalid final price data"""
        test_promotion = PromotionsFactory()  # create a valid promotion
        test_promotion.create()  # add it to the database

        # we obtain the python dict of the test_promotion's data and modify the final price to an invalid value
        invalid_body = (
            test_promotion.serialize()
        )  # get the valid data for the promotion

        # remove the non-updatable fields
        invalid_body.pop("promotion_id")
        invalid_body.pop("created_at")
        # assign invalid value to field being tested
        invalid_body["final_price"] = "asdf"

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test for boolean
        invalid_body["final_price"] = True

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )
        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # test for nan
        invalid_body["final_price"] = float("nan")

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )
        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_invalid_description_promotion(self):
        """It should fail to update a promotion with invalid description data"""
        test_promotion = PromotionsFactory()  # create a valid promotion
        test_promotion.create()  # add it to the database

        # we obtain the python dict of the test_promotion's data and modify the description to an invalid value
        invalid_body = (
            test_promotion.serialize()
        )  # get the valid data for the promotion

        # remove the non-updatable fields
        invalid_body.pop("promotion_id")
        invalid_body.pop("created_at")
        # assign invalid value to field being tested
        invalid_body["promotion_description"] = None

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_invalid_campaign_promotion(self):
        """It should fail to update a promotion with invalid campaign data"""
        test_promotion = PromotionsFactory()  # create a valid promotion
        test_promotion.create()  # add it to the database

        # we obtain the python dict of the test_promotion's data and modify the campaign to an invalid value
        invalid_body = (
            test_promotion.serialize()
        )  # get the valid data for the promotion
        # remove the non-updatable fields
        invalid_body.pop("promotion_id")
        invalid_body.pop("created_at")
        invalid_body["campaign"] = None

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=invalid_body,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_promotion_no_content_type(self):
        """It should not Update a Promotion without content-type"""
        response = self.client.put(BASE_URL + "/1", data="hello")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_update_promotion_wrong_content_type(self):
        """It should not Update a Promotion with the wrong Content-Type"""
        response = self.client.put(
            BASE_URL + "/1", data="hello", content_type="text/plain"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_update_cancelled_promotion(self):
        """It should fail to update a promotion that is cancelled"""
        test_promotion = PromotionsFactory()  # create a valid promotion
        test_promotion.create()  # add it to the database
        test_promotion.status = "cancelled"  # set the status to cancelled
        test_promotion.update()

        body = test_promotion.serialize()  # get the valid data for the promotion

        response = self.client.put(
            # we pass both the promotion id and the invalid data for the update
            f"{BASE_URL}/{test_promotion.promotion_id}",
            json=body,
        )

        # check that the update was unsuccessful
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ----------------------------------------------------------
    # TEST CANCEL - ACTION
    # ----------------------------------------------------------

    def test_cancel_promotion(self):
        """It should cancel an active promotion"""
        test_promotion = PromotionsFactory(status="active")
        test_promotion.create()
        promotion_id = test_promotion.promotion_id

        response = self.client.put(f"{BASE_URL}/{promotion_id}/cancel")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.is_json)
        self.assertEqual(response.get_json()["status"], "cancelled")

        # drop uncommitted state, then prove the change was saved
        db.session.remove()
        self.assertEqual(Promotions.find(promotion_id).status, "cancelled")

        # a GET also shows it, and the row was not deleted
        response = self.client.get(f"{BASE_URL}/{promotion_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["status"], "cancelled")

    def test_cancel_promotion_not_found(self):
        """It should return a JSON 404 when cancelling an unknown promotion"""
        response = self.client.put(f"{BASE_URL}/999999/cancel")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.is_json)
        self.assertIn("message", response.get_json())

    def test_cancel_promotion_twice(self):
        """It should allow cancelling an already cancelled promotion"""
        test_promotion = PromotionsFactory(status="cancelled")
        test_promotion.create()
        promotion_id = test_promotion.promotion_id

        response = self.client.put(f"{BASE_URL}/{promotion_id}/cancel")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.get_json()["status"], "cancelled")

    def test_cancel_promotion_method_not_allowed(self):
        """It should not allow GET on the cancel route"""
        test_promotion = PromotionsFactory()
        test_promotion.create()
        response = self.client.get(f"{BASE_URL}/{test_promotion.promotion_id}/cancel")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(response.is_json)
