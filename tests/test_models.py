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
Test cases for Promotions Model
"""

# pylint: disable=duplicate-code
import os
import logging
from unittest import TestCase
from datetime import date, datetime, timezone
from decimal import Decimal
from wsgi import app
from service.models import Promotions, DataValidationError, db
from .factories import PromotionsFactory, PROMOTION_TYPES

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql+psycopg://postgres:postgres@localhost:5432/testdb"
)


######################################################################
#  P R O M O T I O N S   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestPromotions(TestCase):
    """Test Cases for Promotions Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        app.app_context().push()

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Promotions).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_promotion(self):
        """It should create one promotion"""
    
        # Count the rows before adding anything.
        before = len(Promotions.all())
        
        # Build a Promotions object with fake data from the factory.
        promotion = PromotionsFactory()
        promotion.create() # Save it to the database
        
        #Assert that no fields are missing
        self.assertIsNotNone(promotion.product_id) 
        self.assertIsNotNone(promotion.product_id)
        self.assertIsNotNone(promotion.start_date)
        self.assertIsNotNone(promotion.end_date)
        self.assertIsNotNone(promotion.status)
        self.assertIsNotNone(promotion.final_price)
        self.assertIsNotNone(promotion.promotion_id)
        self.assertIsNotNone(promotion.promotion_description)
        self.assertIsNotNone(promotion.campaign)
        self.assertIsNotNone(promotion.created_at)

        # Compare number of rows before and after promotion.create()
        after = len(Promotions.all())
        self.assertEqual(before+1, after)

        #Fetch a promotion from database
        data = Promotions.find(promotion.promotion_id)

        # Compare what was saved in the database against the original object
        self.assertEqual(data.product_id, promotion.product_id)      
        self.assertEqual(data.start_date, promotion.start_date)      
        self.assertEqual(data.end_date, promotion.end_date)          
        self.assertEqual(data.status, promotion.status)              
        self.assertEqual(data.final_price, promotion.final_price)    
        self.assertEqual(data.promotion_id, promotion.promotion_id)  
        self.assertEqual(data.promotion_description, promotion.promotion_description)  
        self.assertEqual(data.campaign, promotion.campaign)  
        self.assertEqual(data.created_at, promotion.created_at)

         # Rules hold for the stored promotion
        self.assertGreater(data.end_date, data.start_date)          
        self.assertLess(data.created_at.date(), data.start_date)
        self.assertIn(data.status, ["active", "inactive", "scheduled", "expired"])
        self.assertIn(data.promotion_description, PROMOTION_TYPES)

    def test_update_a_promotion(self):
        """It should update a promotion"""
        promotion = PromotionsFactory()
        promotion.create()

        promotion.start_date = date(2026, 1, 1)
        promotion.end_date = date(2026, 12, 31)
        promotion.status = "expired"
        promotion.final_price = Decimal("12.34")
        promotion.promotion_description = "Updated description"
        promotion.campaign = "Updated Campaign"
        promotion.update()

        found = Promotions.find(promotion.promotion_id)
        self.assertEqual(found.start_date, date(2026, 1, 1))
        self.assertEqual(found.end_date, date(2026, 12, 31))
        self.assertEqual(found.status, "expired")
        self.assertEqual(found.final_price, Decimal("12.34"))
        self.assertEqual(found.promotion_description, "Updated description")
        self.assertEqual(found.campaign, "Updated Campaign")

    def test_delete_a_promotion(self):
        """It should delete a promotion"""
        promotion = PromotionsFactory()
        promotion.create()
        promotion.delete()
        self.assertIsNone(Promotions.find(promotion.promotion_id))
    
    def test_serialize_a_promotion(self):
        """It should serialize a promotion"""
        promotion = PromotionsFactory()
        promotion.create()  # needed so created_at gets its default value

        data = promotion.serialize() #Create the dictionary

        self.assertIsInstance(data, dict) #Assert the dictionary
        self.assertEqual(data["product_id"], promotion.product_id)
        self.assertEqual(data["start_date"], promotion.start_date.isoformat())
        self.assertEqual(data["end_date"], promotion.end_date.isoformat())
        self.assertEqual(data["status"], promotion.status)
        self.assertEqual(data["final_price"], float(promotion.final_price))
        self.assertEqual(data["promotion_id"], promotion.promotion_id)
        self.assertEqual(data["promotion_description"], promotion.promotion_description)
        self.assertEqual(data["campaign"], promotion.campaign)
        self.assertEqual(data["created_at"], promotion.created_at.isoformat())

    def test_deserialize_a_promotion(self):
        """It should deserialize a promotion"""
        data = {
            "start_date": "2026-12-01",
            "end_date": "2026-12-31",
            "status": "active",
            "final_price": 12.34,
            "promotion_id": 101,
            "product_id": 102,
            "promotion_description": "Winter sale",
            "campaign": "Winter Campaign",
        }

        promotion = Promotions()
        promotion.deserialize(data)

        self.assertEqual(promotion.start_date, date(2026, 12, 1))
        self.assertEqual(promotion.end_date, date(2026, 12, 31))
        self.assertEqual(promotion.status, "active")
        self.assertEqual(promotion.final_price, Decimal("12.34"))
        self.assertEqual(promotion.promotion_id, 101)
        self.assertEqual(promotion.product_id, 102)
        self.assertEqual(promotion.promotion_description, "Winter sale")
        self.assertEqual(promotion.campaign, "Winter Campaign")

    def test_find_by_product_id(self):
        """It should find all promotions for a product"""
        PromotionsFactory(product_id=7).create()
        PromotionsFactory(product_id=7).create()
        PromotionsFactory(product_id=8).create()

        found = Promotions.find_by_product_id(7)
        self.assertEqual(len(found), 2)
        for promotion in found:
            self.assertEqual(promotion.product_id, 7)

    def test_find_by_product_id_none(self):
        """It should return an empty list when the product has no promotions"""
        self.assertEqual(Promotions.find_by_product_id(999), [])

    def test_find_by_description(self):
        """It should find all promotions with a description"""
        PromotionsFactory(promotion_description="cashback").create()
        PromotionsFactory(promotion_description="cashback").create()
        PromotionsFactory(promotion_description="2x1").create()

        found = Promotions.find_by_description("cashback")
        self.assertEqual(len(found), 2)
        for promotion in found:
            self.assertEqual(promotion.promotion_description, "cashback")

    def test_find_by_description_none(self):
        """It should return an empty list when nothing matches"""
        self.assertEqual(Promotions.find_by_description("nonexistent"), [])