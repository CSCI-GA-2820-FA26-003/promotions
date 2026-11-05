"""
Promotion Steps

Background step: loads known promotions through the REST API so each
scenario starts from the same data. The scenarios themselves use only the UI.
"""

import requests
from compare3 import expect
from behave import given  # pylint: disable=no-name-in-module

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
WAIT_TIMEOUT = 60


@given("the following promotions")
def step_impl(context):
    """Delete all Promotions and load new ones"""
    endpoint = f"{context.base_url}/promotions"
    context.resp = requests.get(endpoint, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(HTTP_200_OK)
    for promotion in context.resp.json():
        context.resp = requests.delete(
            f"{endpoint}/{promotion['promotion_id']}", timeout=WAIT_TIMEOUT
        )
        expect(context.resp.status_code).equal_to(HTTP_204_NO_CONTENT)

    for row in context.table:
        payload = {
            "promotion_id": int(row["promotion_id"]),
            "product_id": int(row["product_id"]),
            "campaign": row["campaign"],
            "promotion_description": row["description"],
            "status": row["status"],
            "final_price": float(row["final_price"]),
            "start_date": row["start_date"],
            "end_date": row["end_date"],
        }
        context.resp = requests.post(endpoint, json=payload, timeout=WAIT_TIMEOUT)
        expect(context.resp.status_code).equal_to(HTTP_201_CREATED)
