"""
Promotion Steps

Background step: loads known promotions through the REST API so each
scenario starts from the same data. The scenarios themselves use only the UI.
"""

import requests
from compare3 import expect
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from behave import given, then  # pylint: disable=no-name-in-module

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
WAIT_TIMEOUT = 60

@given("the following promotions")
def step_impl(context):
    """Delete all Promotions and load new ones"""
    endpoint = f"{context.base_url}/api/promotions"

    context.resp = requests.get(endpoint, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(HTTP_200_OK)

    for promotion in context.resp.json():
        context.resp = requests.delete(
            f"{endpoint}/{promotion['promotion_id']}",
            timeout=WAIT_TIMEOUT
        )
        expect(context.resp.status_code).equal_to(HTTP_204_NO_CONTENT)

    # Store the mapping between Gherkin IDs and generated IDs
    context.promotion_ids = {}

    for row in context.table:
        payload = {
            "product_id": int(row["product_id"]),
            "campaign": row["campaign"],
            "promotion_description": row["description"],
            "status": row["status"],
            "final_price": float(row["final_price"]),
            "start_date": row["start_date"],
            "end_date": row["end_date"],
        }

        context.resp = requests.post(
            endpoint, json=payload, timeout=WAIT_TIMEOUT
        )
        expect(context.resp.status_code).equal_to(HTTP_201_CREATED)

        # Associate the original Gherkin ID with the generated ID
        context.promotion_ids[row["promotion_id"]] = (
            context.resp.json()["promotion_id"]
        )

@given("no promotions exist")
def step_no_promotions(context):
    """Delete all Promotions so the list starts empty"""
    endpoint = f"{context.base_url}/api/promotions"
    context.resp = requests.get(endpoint, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(HTTP_200_OK)
    for promotion in context.resp.json():
        context.resp = requests.delete(
            f"{endpoint}/{promotion['promotion_id']}", timeout=WAIT_TIMEOUT
        )
        expect(context.resp.status_code).equal_to(HTTP_204_NO_CONTENT)

@then('all required fields should be displayed')
def step_check_required_fields(context):
    fields = [
        "promotion_product_id",
        "promotion_start_date",
        "promotion_end_date",
        "promotion_status",
        "promotion_final_price",
        "promotion_description",
        "promotion_campaign",
    ]

    for field_id in fields:
        element = WebDriverWait(context.driver, context.wait_seconds).until(
            EC.visibility_of_element_located((By.ID, field_id))
        )
        assert element.is_displayed()

@then('the "ID" field should contain a generated promotion ID')
def step_verify_generated_id(context):
    element = context.driver.find_element(By.ID, "promotion_id")

    promotion_id = element.get_attribute("value")

    assert promotion_id is not None
    assert promotion_id.isdigit()
    assert int(promotion_id) > 0