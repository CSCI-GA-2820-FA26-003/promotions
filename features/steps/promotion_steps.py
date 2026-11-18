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
from datetime import date, timedelta

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
###########################################
# step functions for updating promotions
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


@when("the admin edits the product id and clicks update")
def step_impl_update_product_id(context):
    """Edit the product id of the existing promotion via the UI"""

    # we find the promotion id field to retrieve the promotion previoulsy created
    promotion_id_field = context.driver.find_element(By.ID, "promotion_id")
    promotion_id_field.clear()
    promotion_id_field.send_keys(str(context.promotion["promotion_id"]))

    # retrieve the promotion so we can get all the field populated
    retrieve_button = context.driver.find_element(By.ID, "retrieve-btn")
    retrieve_button.click()

    # find the product id field in the UI
    product_id_field = context.driver.find_element(By.ID, "promotion_product_id")

    # now we have Selenium update the product id field so it updates the promotion's product id
    product_id_field.clear()
    product_id_field.send_keys(
        f"{context.promotion['product_id'] + 1}"
    )  # Change the product id
    context.promotion["product_id"] += 1

    # now we have Selenium click the update button to update the promotion
    update_button = context.driver.find_element(By.ID, "update-btn")
    update_button.click()


@when("the admin edits the campaign and clicks update")
def step_impl_update_campaign(context):
    """Edit the campaign of the existing promotion via the UI"""

    # we find the promotion id field to retrieve the promotion previoulsy created
    promotion_id_field = context.driver.find_element(By.ID, "promotion_id")
    promotion_id_field.clear()
    promotion_id_field.send_keys(str(context.promotion["promotion_id"]))

    # retrieve the promotion so we can get all the field populated
    retrieve_button = context.driver.find_element(By.ID, "retrieve-btn")
    retrieve_button.click()

    # find the campaign field in the UI
    campaign_field = context.driver.find_element(By.ID, "promotion_campaign")

    # now we have Selenium update the campaign field so it updates the promotion's campaign
    campaign_field.clear()
    campaign_field.send_keys("test campaign")  # Change the campaign
    context.promotion["campaign"] = "test campaign"

    # now we have Selenium click the update button to update the promotion
    update_button = context.driver.find_element(By.ID, "update-btn")
    update_button.click()


@when("the admin edits the description and clicks update")
def step_impl_update_promotion_description(context):
    """Edit the promotion description of the existing promotion via the UI"""

    # we find the promotion id field to retrieve the promotion previously created
    promotion_id_field = context.driver.find_element(By.ID, "promotion_id")
    promotion_id_field.clear()
    promotion_id_field.send_keys(str(context.promotion["promotion_id"]))

    # retrieve the promotion so we can get all the field populated
    retrieve_button = context.driver.find_element(By.ID, "retrieve-btn")
    retrieve_button.click()

    # find the promotion description field in the UI
    description_field = context.driver.find_element(By.ID, "promotion_description")

    # now we have Selenium update the promotion description field so it updates the promotion's description
    description_field.clear()
    description_field.send_keys("test description")  # Change the promotion description
    context.promotion["promotion_description"] = "test description"

    # now we have Selenium click the update button to update the promotion
    update_button = context.driver.find_element(By.ID, "update-btn")
    update_button.click()


@when("the admin edits the status and clicks update")
def step_impl_update_promotion_status(context):
    """Edit the promotion status of the existing promotion via the UI"""

    # we find the promotion id field to retrieve the promotion previoulsy created
    promotion_id_field = context.driver.find_element(By.ID, "promotion_id")
    promotion_id_field.clear()
    promotion_id_field.send_keys(str(context.promotion["promotion_id"]))

    # retrieve the promotion so we can get all the field populated
    retrieve_button = context.driver.find_element(By.ID, "retrieve-btn")
    retrieve_button.click()

    # find the promotion status field in the UI
    status_field = context.driver.find_element(By.ID, "promotion_status")

    # now we have Selenium choose a different promotion status field so it updates the promotion's status
    Select(status_field).select_by_visible_text("inactive")
    context.promotion["status"] = "inactive"

    # now we have Selenium click the update button to update the promotion
    update_button = context.driver.find_element(By.ID, "update-btn")
    update_button.click()


@when("the admin edits the final price and clicks update")
def step_impl_update_promotion_final_price(context):
    """Edit the promotion final price of the existing promotion via the UI"""

    # we find the promotion id field to retrieve the promotion previoulsy created
    promotion_id_field = context.driver.find_element(By.ID, "promotion_id")
    promotion_id_field.clear()
    promotion_id_field.send_keys(str(context.promotion["promotion_id"]))

    # retrieve the promotion so we can get all the field populated
    retrieve_button = context.driver.find_element(By.ID, "retrieve-btn")
    retrieve_button.click()

    # find the promotion final price field in the UI
    final_price_field = context.driver.find_element(By.ID, "promotion_final_price")

    # now we have Selenium update the promotion final price field so it updates the promotion's final price
    final_price_field.clear()
    final_price_field.send_keys(
        str(float(context.promotion["final_price"]) + 1.0)
    )  # Change the promotion final price
    context.promotion["final_price"] = float(context.promotion["final_price"]) + 1.0

    # now we have Selenium click the update button to update the promotion
    update_button = context.driver.find_element(By.ID, "update-btn")
    update_button.click()


@when("the admin edits the start and end dates and clicks update")
def step_impl_update_promotion_dates(context):
    """Edit the promotion start and end dates of the existing promotion via the UI"""

    # we find the promotion id field to retrieve the promotion previoulsy created
    promotion_id_field = context.driver.find_element(By.ID, "promotion_id")
    promotion_id_field.clear()
    promotion_id_field.send_keys(str(context.promotion["promotion_id"]))

    # retrieve the promotion so we can get all the field populated
    retrieve_button = context.driver.find_element(By.ID, "retrieve-btn")
    retrieve_button.click()

    # find the promotion start and end date fields in the UI
    start_date_field = context.driver.find_element(By.ID, "promotion_start_date")
    end_date_field = context.driver.find_element(By.ID, "promotion_end_date")

    # now we have Selenium update the promotion start date field so it updates the promotion's start date
    print("Start date value:", start_date_field.get_attribute("value"))

    start_date_field.clear()
    start_date_field.send_keys("01-01-9999")  # Change the promotion start date
    context.promotion["start_date"] = "9999-01-01"

    # now we have Selenium update the promotion end date field so it updates the promotion's end date
    end_date_field.clear()
    end_date_field.send_keys("01-02-9999")  # Change the promotion end date
    context.promotion["end_date"] = "9999-01-02"

    # now we have Selenium click the update button to update the promotion
    update_button = context.driver.find_element(By.ID, "update-btn")
    update_button.click()


@then("the update is successful")
def step_impl_update_successful(context):
    """Verify that the update was successful by checking the flash message"""
    flash_message = context.driver.find_element(By.ID, "flash_message")
    expect(flash_message.text).equal_to("Promotion has been updated!")


@then("the promotion reflects the new values when retrieved")
def step_impl_verify_updated_values(context):
    """Verify that the promotion reflects the new values when retrieved"""
    # Implementation for verifying updated values
    updated_promotion = (
        context.promotion
    )  # get a copy of the promotion as updated in the UI

    # now retrieve the same promotion from the database
    response = requests.get(
        f"{context.base_url}/api/promotions/{context.promotion['promotion_id']}",
        timeout=WAIT_TIMEOUT,
    )
    expect(response.status_code).equal_to(HTTP_200_OK)

    # now we check if the promotion in the context matches that retrieved from the database
    expect(updated_promotion).equal_to(response.json())


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


@then("the update is rejected because the promotion is cancelled")
def step_impl_update_fields(context):
    """Verify that the update was rejected by checking the flash message"""
    flash_message = context.driver.find_element(By.ID, "flash_message")
    expect(flash_message.text).equal_to(
        f"400 Bad Request: Promotion with id '{context.promotion['promotion_id']}' is cancelled."
    )


@when("the admin attempts to update the product id with an invalid value")
def step_impl_update_product_id_invalid(context):
    """Edit the product id of the existing promotion via the UI"""

    # we find the promotion id field to retrieve the promotion previoulsy created
    promotion_id_field = context.driver.find_element(By.ID, "promotion_id")
    promotion_id_field.clear()
    promotion_id_field.send_keys(str(context.promotion["promotion_id"]))

    # retrieve the promotion so we can get all the field populated
    retrieve_button = context.driver.find_element(By.ID, "retrieve-btn")
    retrieve_button.click()

    # find the product id field in the UI
    product_id_field = context.driver.find_element(By.ID, "promotion_product_id")

    # now we have Selenium update the product id field so it updates the promotion's product id
    product_id_field.clear()
    product_id_field.send_keys("asdf")  # Change the product id to an invalid value

    # now we have Selenium click the update button to update the promotion
    update_button = context.driver.find_element(By.ID, "update-btn")
    update_button.click()


@then("an appropriate error message is displayed stating product id must be an integer")
def step_impl_invalid_product_id_message(context):
    """Verify that the update was rejected by checking the flash message"""
    flash_message = context.driver.find_element(By.ID, "flash_message")
    expect(flash_message.text).equal_to(
        f"400 Bad Request: Input payload validation failed: product_id: None is not of type 'integer'"
    )


@when("the admin attempts to update the final price with an invalid value")
def step_impl_update_final_price_invalid(context):
    """Edit the final price of the existing promotion via the UI"""

    # we find the promotion id field to retrieve the promotion previoulsy created
    promotion_id_field = context.driver.find_element(By.ID, "promotion_id")
    promotion_id_field.clear()
    promotion_id_field.send_keys(str(context.promotion["promotion_id"]))

    # retrieve the promotion so we can get all the field populated
    retrieve_button = context.driver.find_element(By.ID, "retrieve-btn")
    retrieve_button.click()

    # find the final price field in the UI
    final_price_field = context.driver.find_element(By.ID, "promotion_final_price")

    # now we have Selenium update the final price field so it updates the promotion's final price
    final_price_field.clear()
    final_price_field.send_keys("asdf")  # Change the final price to an invalid value

    # now we have Selenium click the update button to update the promotion
    update_button = context.driver.find_element(By.ID, "update-btn")
    update_button.click()


@then("an appropriate error message is displayed stating final price must be a number")
def step_impl_update_invalid_final_price_message(context):
    """Verify that the update was rejected by checking the flash message"""
    flash_message = context.driver.find_element(By.ID, "flash_message")
    expect(flash_message.text).equal_to(
        f"400 Bad Request: Field 'final_price' must be a valid number."
    )
