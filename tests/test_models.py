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
        data = Promotions.find(promotion.product_id)

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

    def test_read_a_promotion(self):
        """It should read a promotion"""
        pass
    
    def test_list_all_promotions(self):
        """It should list all promotions"""
        pass

    def test_delete_a_promotion(self):
        """It should delete a promotion"""
        pass

    def test_update_a_promotion(self):
        """It should update a promotion"""
        pass