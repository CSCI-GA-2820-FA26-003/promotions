"""
Models for Promotions

All of the models are stored in this module
"""

import logging
from datetime import datetime, date, timezone
from decimal import Decimal, InvalidOperation
from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger("flask.app")

# Create the SQLAlchemy object to be initialized later in init_db()
db = SQLAlchemy()


class DataValidationError(Exception):
    """Used for an data validation errors when deserializing"""


class Promotions(db.Model):  # pylint: disable=too-many-instance-attributes
    """
    Class that represents a Promotions
    """

    ##################################################
    # Table Schema
    ##################################################
    product_id = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    final_price = db.Column(db.Numeric(10, 2), nullable=False)
    promotion_id = db.Column(db.Integer, unique=True, nullable=False, primary_key=True)
    promotion_description = db.Column(db.String(150), nullable=False)
    campaign = db.Column(db.String(150), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self):
        return f"<Promotions promotion_id=[{self.promotion_id}] product_id=[{self.product_id}]>"

    def create(self):
        """
        Creates a Promotions to the database
        """
        logger.info("Creating promotion_id %s", self.promotion_id)
        try:
            db.session.add(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error creating record: %s", self)
            raise DataValidationError(e) from e

    def update(self):
        """
        Updates a Promotions to the database
        """
        logger.info("Saving promotion ID: %s", self.promotion_id)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error updating record: %s", self)
            raise DataValidationError(e) from e

    def delete(self):
        """Removes a Promotions from the data store"""
        logger.info("Deleting promotion_id: %s", self.promotion_id)
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.error("Error deleting record: %s", self)
            raise DataValidationError(e) from e

    def serialize(self):
        """Serializes a Promotions into a dictionary"""
        return {
            "product_id": self.product_id,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "status": self.status,
            "final_price": (
                float(self.final_price) if self.final_price is not None else None
            ),
            "promotion_id": self.promotion_id,
            "promotion_description": self.promotion_description,
            "campaign": self.campaign,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def deserialize(self, data):
        """
        Deserializes a Promotions from a dictionary

        Args:
            data (dict): A dictionary containing the resource data
        """
        try:
            self.product_id = data["product_id"]
            self.start_date = date.fromisoformat(data["start_date"])
            self.end_date = date.fromisoformat(data["end_date"])
            self.status = data["status"]
            self.final_price = Decimal(str(data["final_price"]))
            self.promotion_id = data["promotion_id"]
            self.promotion_description = data["promotion_description"]
            self.campaign = data["campaign"]

        except KeyError as error:
            raise DataValidationError(
                "Invalid Promotions: missing " + error.args[0]
            ) from error
        except (TypeError, ValueError, InvalidOperation) as error:
            raise DataValidationError(
                "Invalid Promotions: body of request contained bad or no data "
                + str(error)
            ) from error
        return self

    ##################################################
    # CLASS METHODS
    ##################################################

    @classmethod
    def all(cls):
        """Returns all of the Promotions in the database"""
        logger.info("Processing all Promotions")
        return cls.query.all()

    @classmethod
    def find(cls, by_id):
        """Finds a Promotions by it's ID"""
        logger.info("Processing lookup for id %s ...", by_id)
        return cls.query.session.get(cls, by_id)

    @classmethod
    def find_by_description(cls, description):
        """Returns all Promotions with the given description

        Args:
            description (string): the promotion_description to match
        """
        logger.info("Processing description query for %s ...", description)
        return cls.query.filter_by(promotion_description=description).all()

    @classmethod
    def find_by_product_id(cls, product_id):
        """Returns all Promotions for a given product_id

        Args:
            product_id (int): the product_id to match
        """
        logger.info("Processing lookup for product_id %s ...", product_id)
        return cls.query.filter_by(product_id=product_id).all()

    @classmethod
    def find_by_status(cls, promotion_status):
        """Returns all Promotions with the given status

        Args:
            promotion_status (string): the status to match exactly
        """
        logger.info("Processing status query for %s ...", promotion_status)
        return cls.query.filter_by(status=promotion_status).all()

    @classmethod
    def find_by_campaign(cls, campaign):
        """Returns all Promotions that belong to the given campaign

        Args:
            campaign (string): the campaign to match exactly
        """
        logger.info("Processing campaign query for %s ...", campaign)
        return cls.query.filter_by(campaign=campaign).all()
