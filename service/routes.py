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

from flask import jsonify, request, abort, url_for
from flask import current_app as app  # Import Flask application
from service.models import Promotions
from service.common import status  # HTTP Status Codes


######################################################################
# GET HEALTH CHECK
######################################################################
@app.route("/health")
def health_check():
    """Let them know our heart is still beating"""
    return jsonify(status=200, message="Healthy"), status.HTTP_200_OK


######################################################################
# GET INDEX
######################################################################
@app.route("/")
def index():
    """Root URL response

    Returns the service name, version and the URL of the promotions
    collection as JSON so that clients can discover the API.
    """
    app.logger.info("Request for Root URL")
    return (
        jsonify(
            name="Promotions REST API Service",
            version="1.0",
            description=(
                "Create, read, update, delete and list the promotions "
                "that apply to products in the e-commerce store"
            ),
            paths=url_for("list_promotions", _external=True),
        ),
        status.HTTP_200_OK,
    )


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
    This endpoint will create a Promotion based the data in the body that is posted
    """
    app.logger.info("Request to Create a Promotion...")
    check_content_type("application/json")

    promotion = Promotions()
    data = request.get_json()
    app.logger.info("Processing: %s", data)
    promotion.deserialize(data)
    # Reject duplicates with a short message instead of a raw database error
    if Promotions.find(promotion.promotion_id):
        abort(
            status.HTTP_400_BAD_REQUEST,
            f"Promotion with id '{promotion.promotion_id}' already exists.",
        )

    # Save the new Promotion to the database
    promotion.create()
    app.logger.info("Promotion with new id [%s] saved!", promotion.promotion_id)

    location_url = url_for(
        "get_promotions", promotion_id=promotion.promotion_id, _external=True
    )

    return promotion.serialize(), status.HTTP_201_CREATED, {"Location": location_url}


######################################################################
# LIST ALL PROMOTIONS
######################################################################
@app.route("/promotions", methods=["GET"])
def list_promotions():
    """Returns all of the Promotions"""
    app.logger.info("Request for promotion list")

    # returns all of the promotions
    promotions = Promotions.all()

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
