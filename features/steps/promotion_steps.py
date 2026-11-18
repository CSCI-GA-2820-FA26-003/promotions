"""
Promotion Steps

Background step: loads known promotions through the REST API so each
scenario starts from the same data. The scenarios themselves use only the UI.
"""

import requests
from compare3 import expect
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from behave import given, then, when  # pylint: disable=no-name-in-module

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
            f"{endpoint}/{promotion['promotion_id']}", timeout=WAIT_TIMEOUT
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

        context.resp = requests.post(endpoint, json=payload, timeout=WAIT_TIMEOUT)
        expect(context.resp.status_code).equal_to(HTTP_201_CREATED)

        # Associate the original Gherkin ID with the generated ID
        context.promotion_ids[row["promotion_id"]] = context.resp.json()["promotion_id"]


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


@then("all required fields should be displayed")
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


###########################################
# step functions for updating promotions
###########################################
def wait_for_message(context, text):
    """Wait until the flash message contains the text"""
    WebDriverWait(context.driver, context.wait_seconds).until(
        EC.text_to_be_present_in_element((By.ID, "flash_message"), text)
    )


def load_promotion(context):
    """Retrieve context.promotion through the UI and wait for the form to fill"""
    id_field = context.driver.find_element(By.ID, "promotion_id")
    id_field.clear()
    id_field.send_keys(str(context.promotion["promotion_id"]))
    context.driver.find_element(By.ID, "retrieve-btn").click()
    wait_for_message(context, "Success")


def set_text(context, element_id, value):
    """Replace the text in a form field"""
    field = context.driver.find_element(By.ID, element_id)
    field.clear()
    field.send_keys(value)


def set_date(context, element_id, value):
    """Set a date input without depending on the browser's date format"""
    field = context.driver.find_element(By.ID, element_id)
    context.driver.execute_script("arguments[0].value = arguments[1];", field, value)


def click_update(context):
    """Press the Update button"""
    context.driver.find_element(By.ID, "update-btn").click()


@given("a promotion exists")
def step_impl_promotion_exist(context):
    """Ensure that a promotion exists for the update scenarios"""
    endpoint = f"{context.base_url}/api/promotions"

    # Create a promotion and add it to the database
    payload = {
        "product_id": 1,
        "campaign": "new campaign",
        "promotion_description": "new promotion",
        "status": "active",
        "final_price": 9.99,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
    }
    context.resp = requests.post(endpoint, json=payload, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(HTTP_201_CREATED)
    context.promotion = context.resp.json()  # store the promotion data in the context


@given("a promotion is cancelled")
def step_impl_promotion_cancelled(context):
    """Ensure that a promotion is cancelled for the update scenarios"""
    endpoint = f"{context.base_url}/api/promotions"

    # Create a promotion and add it to the database
    payload = {
        "product_id": 1,
        "campaign": "cancelled campaign",
        "promotion_description": "cancelled promotion",
        "status": "cancelled",
        "final_price": 9.99,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
    }
    context.resp = requests.post(endpoint, json=payload, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(HTTP_201_CREATED)
    context.promotion = context.resp.json()  # store the promotion data in the context


@when("the admin edits the product id and clicks update")
def step_impl_update_product_id(context):
    """Edit the product id of the existing promotion via the UI"""
    load_promotion(context)
    context.promotion["product_id"] += 1
    set_text(context, "promotion_product_id", str(context.promotion["product_id"]))
    click_update(context)


@when("the admin edits the campaign and clicks update")
def step_impl_update_campaign(context):
    """Edit the campaign of the existing promotion via the UI"""
    load_promotion(context)
    set_text(context, "promotion_campaign", "test campaign")
    context.promotion["campaign"] = "test campaign"
    click_update(context)


@when("the admin edits the description and clicks update")
def step_impl_update_promotion_description(context):
    """Edit the promotion description of the existing promotion via the UI"""
    load_promotion(context)
    set_text(context, "promotion_description", "test description")
    context.promotion["promotion_description"] = "test description"
    click_update(context)


@when("the admin edits the status and clicks update")
def step_impl_update_promotion_status(context):
    """Edit the promotion status of the existing promotion via the UI"""
    load_promotion(context)
    status_field = context.driver.find_element(By.ID, "promotion_status")
    Select(status_field).select_by_visible_text("inactive")
    context.promotion["status"] = "inactive"
    click_update(context)


@when("the admin edits the final price and clicks update")
def step_impl_update_promotion_final_price(context):
    """Edit the promotion final price of the existing promotion via the UI"""
    load_promotion(context)
    context.promotion["final_price"] = float(context.promotion["final_price"]) + 1.0
    set_text(context, "promotion_final_price", str(context.promotion["final_price"]))
    click_update(context)


@when("the admin edits the start and end dates and clicks update")
def step_impl_update_promotion_dates(context):
    """Edit the promotion start and end dates of the existing promotion via the UI"""
    load_promotion(context)
    set_date(context, "promotion_start_date", "2027-01-01")
    context.promotion["start_date"] = "2027-01-01"
    set_date(context, "promotion_end_date", "2027-01-02")
    context.promotion["end_date"] = "2027-01-02"
    click_update(context)


@when("the admin attempts to update the product id with an invalid value")
def step_impl_update_product_id_invalid(context):
    """Enter an invalid product id for the existing promotion via the UI"""
    load_promotion(context)
    set_text(context, "promotion_product_id", "asdf")
    click_update(context)


@when("the admin attempts to update the final price with an invalid value")
def step_impl_update_final_price_invalid(context):
    """Enter an invalid final price for the existing promotion via the UI"""
    load_promotion(context)
    set_text(context, "promotion_final_price", "asdf")
    click_update(context)


@then("the update is successful")
def step_impl_update_successful(context):
    """Verify that the update was successful by checking the flash message"""
    wait_for_message(context, "Promotion has been updated!")


@then("the promotion reflects the new values when retrieved")
def step_impl_verify_updated_values(context):
    """Verify that the promotion reflects the new values when retrieved"""
    updated_promotion = context.promotion  # the promotion as updated in the UI

    # now retrieve the same promotion from the database
    response = requests.get(
        f"{context.base_url}/api/promotions/{context.promotion['promotion_id']}",
        timeout=WAIT_TIMEOUT,
    )
    expect(response.status_code).equal_to(HTTP_200_OK)

    # the whole promotion must match, including the original created_at
    expect(updated_promotion).equal_to(response.json())


@then("the update is rejected because the promotion is cancelled")
def step_impl_update_fields(context):
    """Verify that the update was rejected by checking the flash message"""
    wait_for_message(context, "is cancelled")


@then("an appropriate error message is displayed stating product id must be an integer")
def step_impl_invalid_product_id_message(context):
    """Verify that the update was rejected by checking the flash message"""
    wait_for_message(context, "product_id: None is not of type 'integer'")


@then("an appropriate error message is displayed stating final price must be a number")
def step_impl_update_invalid_final_price_message(context):
    """Verify that the update was rejected by checking the flash message"""
    wait_for_message(context, "Field 'final_price' must be a valid number.")
