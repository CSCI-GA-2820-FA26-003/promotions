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

This service implements a REST API that allows you to Create, Read, Update
and Delete Promotions
"""

from datetime import date
from flask import jsonify, request, abort, url_for
from flask import current_app as app  # Import Flask application
from service.models import Promotions, db
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
#  R E S T   A P I   E N D P O I N T S
######################################################################

######################################################################
# CREATE A NEW PROMOTION
######################################################################
@app.route("/promotions", methods=["POST"])
def create_promotions():
    """
    Create a Promotion
    This endpoint creates a Promotion with an automatically generated ID
    """
    app.logger.info("Request to Create a Promotion...")
    check_content_type("application/json")

    promotion = Promotions()
    data = request.get_json()
    app.logger.info("Processing: %s", data)

    # Deserialize the data without requiring promotion_id
    promotion.deserialize(data)

    # Save the promotion (database automatically generates promotion_id)
    promotion.create()
    app.logger.info("Promotion with new id [%s] saved!", promotion.promotion_id)

    # Generate the URL for the newly created promotion
    location_url = url_for(
        "get_promotions", promotion_id=promotion.promotion_id, _external=True
    )

    return promotion.serialize(), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# LIST ALL PROMOTIONS
######################################################################
@app.route("/promotions", methods=["GET"])
def list_promotions():  # noqa: C901
    """Returns all of the Promotions, optionally filtered by query string

    Supported filters (combined with AND when more than one is given):
        product_id  - integer id of the product the promotion applies to
        status      - exact status value, e.g. active, cancelled
        campaign    - exact campaign name, e.g. black friday
    """
    app.logger.info("Request for promotion list")

    product_id = request.args.get("product_id")
    promotion_status = request.args.get("status")
    campaign = request.args.get("campaign")
    active = request.args.get(
        "active"
    )  # to store the boolean value of active in a query parameter

    if product_id is not None:
        try:
            product_id = int(product_id)
        except ValueError:
            abort(
                status.HTTP_400_BAD_REQUEST,
                f"product_id must be an integer, got '{product_id}'",
            )

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


######################################################################
# RETRIEVE ONE PROMOTION
######################################################################
@app.route("/promotions/<int:promotion_id>", methods=["GET"])
def get_promotions(promotion_id):
    """Return one promotion by its unique promotion ID, including cancelled ones."""
    app.logger.info("Request for promotion with ID [%s]", promotion_id)
    if promotion_id <= 0:
        abort(status.HTTP_400_BAD_REQUEST, "Promotion ID must be a positive integer")

    # product_id is the model's primary key; the URL identifies promotion_id.
    promotion = Promotions.query.filter_by(promotion_id=promotion_id).first()
    if promotion is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Promotion with ID [{promotion_id}] was not found",
        )
    return promotion.serialize(), status.HTTP_200_OK


def check_content_type(content_type) -> None:
    """Checks that the media type is correct"""
    if "Content-Type" not in request.headers:
        app.logger.error("No Content-Type specified.")
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {content_type}",
        )

    if request.headers["Content-Type"] == content_type:
        return

    app.logger.error("Invalid Content-Type: %s", request.headers["Content-Type"])
    abort(
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        f"Content-Type must be {content_type}",
    )


######################################################################
# DELETE A PROMOTION
######################################################################


@app.route("/promotions/<int:promotion_id>", methods=["DELETE"])
def delete_promotions(promotion_id):
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
    return {}, status.HTTP_204_NO_CONTENT


def parse_date_field(key, value):
    """Converts an ISO date string to a date, or aborts with a JSON 400"""
    try:
        return date.fromisoformat(value)
    except ValueError:
        db.session.rollback()
        abort(
            status.HTTP_400_BAD_REQUEST,
            f"Field '{key}' must be a date in YYYY-MM-DD format.",
        )


######################################################################
# UPDATE A PROMOTION
######################################################################

@app.route("/promotions/<int:promotion_id>", methods=["PUT"])
def update_promotions(promotion_id):
    """Update a Promotion"""
    app.logger.info("Request to update promotion with id: %s", promotion_id)

    check_content_type("application/json")

    # Find the existing promotion
    promotion = Promotions.find(promotion_id)

    if promotion is None:
        abort(
            status.HTTP_404_NOT_FOUND,
            f"Promotion with id '{promotion_id}' was not found.",
        )

    # Let the model validate and apply the changes
    data = request.get_json(silent=True)
    promotion.deserialize_update(data)

    # Save the updated promotion
    promotion.update()

    app.logger.info("Promotion with ID %s updated.", promotion_id)

    return jsonify(promotion.serialize()), status.HTTP_200_OK


######################################################################
# CANCEL A PROMOTION (ACTION)
######################################################################
@app.route("/promotions/<int:promotion_id>/cancel", methods=["PUT"])
def cancel_promotions(promotion_id):
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


@app.route("/promotions/<int:promotion_id>/activate", methods=["PUT"])
def activate_promotion(promotion_id):
    """Activate an existing promotion without modifying its other fields."""
    return set_promotion_status(promotion_id, "active")


@app.route("/promotions/<int:promotion_id>/deactivate", methods=["PUT"])
def deactivate_promotion(promotion_id):
    """Deactivate an existing promotion without cancelling it."""
    return set_promotion_status(promotion_id, "inactive")


def set_promotion_status(promotion_id, target_status):
    """Apply an idempotent availability action, preserving cancellation."""
    promotion = Promotions.find(promotion_id)
    if promotion is None:
        abort(status.HTTP_404_NOT_FOUND, "Promotion not found")
    if promotion.status == "cancelled":
        abort(status.HTTP_409_CONFLICT, "Cancelled promotions cannot be activated or deactivated")
    promotion.status = target_status
    promotion.update()
    app.logger.info("Promotion %s status changed to %s", promotion_id, target_status)
    return promotion.serialize(), status.HTTP_200_OK
