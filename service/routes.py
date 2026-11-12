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
Promotions Service

This service implements a REST API that allows you to Create, Read, Update,
Delete, List, Query and Cancel Promotions

Paths:
------
GET /                              - Displays the admin UI
GET /health                        - Health check for Kubernetes
GET /api/promotions                - Returns a list of the Promotions (optionally filtered)
POST /api/promotions               - Creates a new Promotion
GET /api/promotions/{id}           - Returns the Promotion with the given id
PUT /api/promotions/{id}           - Updates the Promotion with the given id
DELETE /api/promotions/{id}        - Deletes the Promotion with the given id
PUT /api/promotions/{id}/cancel    - Cancels the Promotion with the given id
"""

from flask import jsonify, abort
from flask import current_app as app  # Import Flask application
from flask_restx import Resource, fields, reqparse
from service import api
from service.models import Promotions
from service.common import status  # HTTP Status Codes

######################################################################
# GET HEALTH CHECK
######################################################################


@app.route("/health")
def health_check():
    """Let them know our heart is still beating"""
    return jsonify(status="OK"), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL: serves the admin UI"""
    app.logger.info("Request for Root URL")
    return app.send_static_file("index.html")


######################################################################
#  A P I   M O D E L S
######################################################################
class Price(fields.Raw):
    """A price such as 19.99

    The schema deliberately has no type, so it is the Promotions model that
    decides what a valid price is. That keeps numeric strings such as "19.99"
    working, as they did before the service moved to Flask-RESTX.
    """

    __schema_type__ = None
    __schema_example__ = 19.99


def promotion_fields(required: bool) -> dict:
    """The fields a client can send: all of them to create, any of them to update"""
    return {
        "product_id": fields.Integer(
            required=required,
            description="The ID of the product the promotion applies to",
        ),
        "start_date": fields.Date(
            required=required,
            description="The first day of the promotion (YYYY-MM-DD)",
        ),
        "end_date": fields.Date(
            required=required,
            description="The last day of the promotion (YYYY-MM-DD)",
        ),
        "status": fields.String(
            required=required,
            description="The status of the promotion, e.g. active, inactive or cancelled",
        ),
        "final_price": Price(
            required=required,
            description="The price of the product while the promotion runs",
        ),
        "promotion_description": fields.String(
            required=required,
            description="What the promotion offers",
        ),
        "campaign": fields.String(
            required=required,
            description="The campaign the promotion belongs to, e.g. black friday",
        ),
    }


# What a client sends to create a Promotion: every field is required
create_model = api.model("Promotion", promotion_fields(required=True))

# What a client sends to update a Promotion: only the fields that change
update_model = api.model("PromotionUpdate", promotion_fields(required=False))

# What the service returns: the Promotion plus the fields the service assigns
promotion_model = api.inherit(
    "PromotionModel",
    create_model,
    {
        "promotion_id": fields.Integer(
            readonly=True,
            description="The unique ID assigned by the service",
        ),
        "created_at": fields.DateTime(
            readonly=True,
            description="When the promotion was created",
        ),
    },
)

# Query string arguments for listing Promotions
promotion_args = reqparse.RequestParser()
promotion_args.add_argument(
    "product_id",
    type=int,
    location="args",
    required=False,
    help="List only the Promotions for this product ID (an integer).",
)
promotion_args.add_argument(
    "status",
    type=str,
    location="args",
    required=False,
    help="List only the Promotions with exactly this status.",
)
promotion_args.add_argument(
    "campaign",
    type=str,
    location="args",
    required=False,
    help="List only the Promotions in exactly this campaign.",
)
promotion_args.add_argument(
    "active",
    type=str,
    location="args",
    required=False,
    help="Set to true to list only the Promotions that are live today.",
)


######################################################################
#  R E S T   A P I   E N D P O I N T S
######################################################################


######################################################################
#  PATH: /promotions/{promotion_id}
######################################################################
@api.route("/promotions/<int:promotion_id>")
@api.param("promotion_id", "The Promotion identifier")
class PromotionResource(Resource):
    """
    PromotionResource class

    Allows the manipulation of a single Promotion
    GET /promotions/{id} - Returns the Promotion with the id
    PUT /promotions/{id} - Updates the Promotion with the id
    DELETE /promotions/{id} - Deletes the Promotion with the id
    """

    # ------------------------------------------------------------------
    # RETRIEVE ONE PROMOTION
    # ------------------------------------------------------------------
    @api.doc("get_promotions")
    @api.response(200, "Success", promotion_model)
    @api.response(400, "The Promotion ID is not a positive integer")
    @api.response(404, "Promotion not found")
    def get(self, promotion_id):
        """Return one promotion by its unique promotion ID, including cancelled ones."""
        app.logger.info("Request for promotion with ID [%s]", promotion_id)
        if promotion_id <= 0:
            abort(status.HTTP_400_BAD_REQUEST, "Promotion ID must be a positive integer")

        promotion = Promotions.query.filter_by(promotion_id=promotion_id).first()
        if promotion is None:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Promotion with ID [{promotion_id}] was not found",
            )
        return promotion.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # UPDATE A PROMOTION
    # ------------------------------------------------------------------
    @api.doc("update_promotions")
    @api.expect(update_model, validate=True)
    @api.response(200, "Promotion updated", promotion_model)
    @api.response(400, "The posted data was not valid, or the Promotion is cancelled")
    @api.response(404, "Promotion not found")
    @api.response(415, "Content-Type must be application/json")
    def put(self, promotion_id):
        """Update a Promotion"""
        app.logger.info("Request to update promotion with id: %s", promotion_id)

        # Find the existing promotion
        promotion = Promotions.find(promotion_id)

        if promotion is None:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Promotion with id '{promotion_id}' was not found.",
            )

        # Let the model validate and apply the changes
        promotion.deserialize_update(api.payload)

        # Save the updated promotion
        promotion.update()

        app.logger.info("Promotion with ID %s updated.", promotion_id)

        return promotion.serialize(), status.HTTP_200_OK

    # ------------------------------------------------------------------
    # DELETE A PROMOTION
    # ------------------------------------------------------------------
    @api.doc("delete_promotions")
    @api.response(204, "Promotion deleted")
    def delete(self, promotion_id):
        """
        Delete a Promotion

        This endpoint will delete a Promotion based the id specified in the path
        """
        app.logger.info("Request to Delete a promotion with id [%s]", promotion_id)

        # Delete the Promotion if it exists
        promotion = Promotions.find(promotion_id)
        if promotion:
            app.logger.info("Promotion with ID: %d found.", promotion.promotion_id)
            promotion.delete()

        app.logger.info("Promotion with ID: %d delete complete.", promotion_id)
        return "", status.HTTP_204_NO_CONTENT


######################################################################
#  PATH: /promotions
######################################################################
@api.route("/promotions")
class PromotionCollection(Resource):
    """Handles all interactions with collections of Promotions"""

    # ------------------------------------------------------------------
    # LIST ALL PROMOTIONS
    # ------------------------------------------------------------------
    @api.doc("list_promotions")
    @api.expect(promotion_args, validate=True)
    @api.response(200, "Success", [promotion_model])
    @api.response(400, "A query string argument was not valid")
    def get(self):
        """Returns all of the Promotions, optionally filtered by query string

        Supported filters (combined with AND when more than one is given):
            product_id  - integer id of the product the promotion applies to
            status      - exact status value, e.g. active, cancelled
            campaign    - exact campaign name, e.g. black friday
            active      - true lists only the promotions that are live today
        """
        app.logger.info("Request for promotion list")

        # The parser answers 400 when product_id is not an integer
        args = promotion_args.parse_args()
        product_id = args["product_id"]
        promotion_status = args["status"]
        campaign = args["campaign"]
        active = args["active"]

        # Start from the narrowest single-column finder, then apply the rest in memory
        if product_id is not None:
            app.logger.info("Filtering by product_id: %s", product_id)
            promotions = Promotions.find_by_product_id(product_id)
        elif promotion_status is not None:
            app.logger.info("Filtering by status: %s", promotion_status)
            promotions = Promotions.find_by_status(promotion_status)
        elif campaign is not None:
            app.logger.info("Filtering by campaign: %s", campaign)
            promotions = Promotions.find_by_campaign(campaign)
        else:
            promotions = Promotions.all()

        # Every supplied filter must match (AND semantics)
        if promotion_status is not None:
            promotions = [p for p in promotions if p.status == promotion_status]
        if campaign is not None:
            promotions = [p for p in promotions if p.campaign == campaign]

        # check if the active query parameter is provided and if it is, filter the promotions by active status and today's date
        if active is not None and active.lower() == "true":
            active_promotions = (
                Promotions.find_by_active()
            )  # when we dont pass any date it will by filter by today's date

            # now we iterate over the promotions list and remove any invalid promotions
            for i in range(len(promotions)):  # pylint: disable=consider-using-enumerate
                if promotions[i] not in active_promotions:
                    promotions[i] = None
            promotions = [p for p in promotions if p is not None]

        elif active is not None:
            # Any other value besides True returns a 400 error
            abort(
                status.HTTP_400_BAD_REQUEST,
                f"active must be 'true', got '{active}'",
            )

        # serializes all of the promotions
        results = [promotion.serialize() for promotion in promotions]
        app.logger.info("Returning %d promotions", len(results))
        return results, status.HTTP_200_OK

    # ------------------------------------------------------------------
    # CREATE A NEW PROMOTION
    # ------------------------------------------------------------------
    @api.doc("create_promotions")
    @api.expect(create_model, validate=True)
    @api.response(201, "Promotion created", promotion_model)
    @api.response(400, "The posted data was not valid")
    @api.response(415, "Content-Type must be application/json")
    def post(self):
        """
        Create a Promotion
        This endpoint creates a Promotion with an automatically generated ID
        """
        app.logger.info("Request to Create a Promotion...")

        promotion = Promotions()
        data = api.payload
        app.logger.info("Processing: %s", data)

        # Deserialize the data without requiring promotion_id
        promotion.deserialize(data)

        # Save the promotion (database automatically generates promotion_id)
        promotion.create()
        app.logger.info("Promotion with new id [%s] saved!", promotion.promotion_id)

        # Generate the URL for the newly created promotion
        location_url = api.url_for(
            PromotionResource, promotion_id=promotion.promotion_id, _external=True
        )

        return promotion.serialize(), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
#  PATH: /promotions/{promotion_id}/cancel
######################################################################
@api.route("/promotions/<int:promotion_id>/cancel")
@api.param("promotion_id", "The Promotion identifier")
class CancelResource(Resource):
    """Cancel action on a Promotion"""

    # ------------------------------------------------------------------
    # CANCEL A PROMOTION (ACTION)
    # ------------------------------------------------------------------
    @api.doc("cancel_promotions")
    @api.response(200, "Promotion cancelled", promotion_model)
    @api.response(404, "Promotion not found")
    def put(self, promotion_id):
        """Cancel a Promotion
        This action sets the status to cancelled.
        """
        app.logger.info("Request to cancel promotion with id: %s", promotion_id)

        promotion = Promotions.find(promotion_id)
        if promotion is None:
            abort(
                status.HTTP_404_NOT_FOUND,
                f"Promotion with id '{promotion_id}' was not found.",
            )

        promotion.status = "cancelled"
        promotion.update()

        app.logger.info("Promotion with ID %s cancelled.", promotion_id)
        return promotion.serialize(), status.HTTP_200_OK
