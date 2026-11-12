Feature: The promotions service admin page
    As a Promotions Manager
    I need to manage promotions from a web page
    So that I can run campaigns without calling the API by hand

Background:
    Given the following promotions
        | promotion_id | product_id | campaign     | description        | status    | final_price | start_date | end_date   |
        | 101          | 1          | black friday | 30 percent off     | active    | 70.00       | 2026-11-20 | 2026-11-30 |
        | 102          | 2          | black friday | Free shipping      | active    | 25.50       | 2026-11-20 | 2026-11-30 |
        | 103          | 3          | summer sale  | Beach bundle deal  | cancelled | 15.00       | 2026-06-01 | 2026-08-31 |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Promotions RESTful Service" in the title
    And I should not see "404 Not Found"

# Each ticket adds its own scenarios below, in this order: Create, Read, List, Update, Delete, Query, Action

# --- Create ---
Scenario: Display required fields
    When I visit the "Home Page"
    Then all required fields should be displayed

Scenario: Create promotion successfully
    When I visit the "Home Page"
    And I set the "Product ID" to "4"
    And I set the "Campaign" to "winter sale"
    And I set the "Description" to "20 percent off"
    And I select "active" in the "Status" dropdown
    And I set the "Final Price" to "80.00"
    And I set the "Start Date" to "2026-12-01"
    And I set the "End Date" to "2026-12-31"
    And I press the "Create" button
    Then I should see the message "Success"
    And the "Campaign" field should contain "winter sale"
    And the "Description" field should contain "20 percent off"
    And the "ID" field should contain a generated promotion ID

Scenario Outline: Validate missing required fields
    When I visit the "Home Page"
    And I set the "Product ID" to "4"
    And I set the "Campaign" to "winter sale"
    And I set the "Description" to "20 percent off"
    And I select "active" in the "Status" dropdown
    And I set the "Final Price" to "80.00"
    And I set the "Start Date" to "2026-12-01"
    And I set the "End Date" to "2026-12-31"
    And I leave the "<field>" field empty
    And I press the "Create" button
    Then I should see the message "Please fill in: <field>"

    Examples:
        | field       |
        | Product ID  |
        | Campaign    |
        | Description |
        | Status      |
        | Final Price |
        | Start Date  |
        | End Date    | 

# --- Retrieve ---

Scenario: Retrieve an existing promotion
    When I visit the "Home Page"
    And I set the "ID" to "101"
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "1" in the "Product ID" field
    And I should see "black friday" in the "Campaign" field
    And I should see "30 percent off" in the "Description" field
    And I should see "active" in the "Status" field
    And I should see "2026-11-20" in the "Start Date" field
    And I should see "2026-11-30" in the "End Date" field

Scenario: Retrieve a promotion that does not exist
    When I visit the "Home Page"
    And I set the "ID" to "101"
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "black friday" in the "Campaign" field
    When I set the "ID" to "9999"
    And I press the "Retrieve" button
    Then I should see the message "Promotion not found"
    And the "Campaign" field should be empty
    And the "Description" field should be empty
    And the "Product ID" field should be empty

Scenario: Retrieve with an empty ID
    When I visit the "Home Page"
    And I press the "Retrieve" button
    Then I should see the message "Please enter a valid Promotion ID"
    And the "Campaign" field should be empty
    And the "Description" field should be empty

Scenario Outline: Retrieve with an invalid ID
    When I visit the "Home Page"
    And I set the "ID" to "101"
    And I press the "Retrieve" button
    Then I should see the message "Success"
    When I set the "ID" to "<id>"
    And I press the "Retrieve" button
    Then I should see the message "Please enter a valid Promotion ID"
    And the "Campaign" field should be empty
    And the "Description" field should be empty

    Examples:
        | id  |
        | abc |
        | 0   |
        | -5  |

Scenario: Retrieving a promotion twice leaves it unchanged
    When I visit the "Home Page"
    And I set the "ID" to "101"
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "1" in the "Product ID" field
    And I should see "black friday" in the "Campaign" field
    And I should see "30 percent off" in the "Description" field
    And I should see "active" in the "Status" field
    And I should see "2026-11-20" in the "Start Date" field
    And I should see "2026-11-30" in the "End Date" field
    When I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "1" in the "Product ID" field
    And I should see "black friday" in the "Campaign" field
    And I should see "30 percent off" in the "Description" field
    And I should see "active" in the "Status" field
    And I should see "2026-11-20" in the "Start Date" field
    And I should see "2026-11-30" in the "End Date" field
    When I press the "Clear" button
    And I set the "ID" to "101"
    And I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "black friday" in the "Campaign" field
    And I should see "30 percent off" in the "Description" field
    And I should see "active" in the "Status" field

# --- List ---

Scenario: List all promotions
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "30 percent off" in the results
    And I should see "Free shipping" in the results
    And I should see "Beach bundle deal" in the results

Scenario: The list shows the relevant promotion fields
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see the message "Success"
    And I should see "Promotion ID" in the results
    And I should see "Product ID" in the results
    And I should see "Campaign" in the results
    And I should see "Description" in the results
    And I should see "Status" in the results
    And I should see "Final Price" in the results
    And I should see "Start Date" in the results
    And I should see "End Date" in the results
    And I should see "black friday" in the results
    And I should see "cancelled" in the results
    And I should see "25.5" in the results
    And I should see "2026-11-20" in the results

Scenario: List when no promotions exist
    Given no promotions exist
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see the message "No promotions found"
    And I should see "No promotions found" in the results
    And I should not see "30 percent off" in the results

Scenario: A refreshed list shows newly added promotions
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see "Beach bundle deal" in the results
    And I should not see "Cyber week bundle" in the results
    # Meanwhile another promotion is added behind the scenes
    Given the following promotions
        | promotion_id | product_id | campaign     | description        | status    | final_price | start_date | end_date   |
        | 101          | 1          | black friday | 30 percent off     | active    | 70.00       | 2026-11-20 | 2026-11-30 |
        | 102          | 2          | black friday | Free shipping      | active    | 25.50       | 2026-11-20 | 2026-11-30 |
        | 103          | 3          | summer sale  | Beach bundle deal  | cancelled | 15.00       | 2026-06-01 | 2026-08-31 |
        | 104          | 4          | cyber week   | Cyber week bundle  | active    | 49.00       | 2026-12-01 | 2026-12-07 |
    When I press the "Search" button
    Then I should see "Cyber week bundle" in the results
    And I should see "Beach bundle deal" in the results

Scenario: Clear removes the list
    Given the following promotions
      | promotion_id | product_id | campaign     | description       | status    | final_price | start_date | end_date   |
      | 101          | 1          | black friday | 30 percent off    | active    | 70.00       | 2026-11-20 | 2026-11-30 |
      | 102          | 2          | black friday | Free shipping     | active    | 25.50       | 2026-11-20 | 2026-11-30 |
      | 103          | 3          | summer sale  | Beach bundle deal | cancelled | 15.00       | 2026-06-01 | 2026-08-31 |
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see "30 percent off" in the results
    When I press the "Clear" button
    Then I should not see "30 percent off" in the results

# --- Delete ---

Scenario: Deleting a promotion asks for confirmation
    When I visit the "Home Page"
    And I set the "ID" to "101"
    And I press the "Retrieve" button
    And I press the "Delete" button
    Then I should see a confirmation prompt asking "Are you sure you want to delete this promotion?"
    When I cancel the deletion

Scenario: Confirming the deletion removes the promotion
    When I visit the "Home Page"
    And I set the "ID" to "101"
    And I press the "Retrieve" button
    And I press the "Delete" button
    And I confirm the deletion
    Then I should see the message "Promotion has been Deleted!"
    And the "ID" field should be empty
    And the "Campaign" field should be empty
    And the "Description" field should be empty
    When I set the "ID" to "101"
    And I press the "Retrieve" button
    Then I should see the message "Promotion not found"

Scenario: Cancelling the deletion keeps the promotion
    When I visit the "Home Page"
    And I set the "ID" to "101"
    And I press the "Retrieve" button
    And I press the "Delete" button
    And I cancel the deletion
    Then I should see the message "Delete cancelled"
    And I should see "black friday" in the "Campaign" field
    When I press the "Retrieve" button
    Then I should see the message "Success"
    And I should see "30 percent off" in the "Description" field

Scenario: Deleting a promotion that does not exist
    When I visit the "Home Page"
    And I set the "ID" to "9999"
    And I press the "Delete" button
    Then I should see the message "Promotion not found"

Scenario: Deleting without a Promotion ID
    When I visit the "Home Page"
    And I press the "Delete" button
    Then I should see the message "Please enter a valid Promotion ID"

Scenario: A deleted promotion no longer appears in the list
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see "30 percent off" in the results
    When I set the "ID" to "101"
    And I press the "Retrieve" button
    And I press the "Delete" button
    And I confirm the deletion
    Then I should see the message "Promotion has been Deleted!"
    When I press the "Search" button
    Then I should see "Free shipping" in the results
    And I should not see "30 percent off" in the results

# --- Query ---

Scenario: Filter promotions by status
    When I visit the "Home Page"
    And I select "cancelled" in the "Status" dropdown
    And I press the "Search" button
    Then I should see "Beach bundle deal" in the results
    And I should see the message "Success"
    And I should not see "30 percent off" in the results
    And I should not see "Free shipping" in the results

Scenario: Filter promotions by campaign
    When I visit the "Home Page"
    And I set the "Campaign" to "black friday"
    And I press the "Search" button
    Then I should see "30 percent off" in the results
    And I should see "Free shipping" in the results
    And I should see the message "Success"
    And I should not see "Beach bundle deal" in the results

Scenario: Filter promotions by status and campaign together
    Given the following promotions
        | promotion_id | product_id | campaign     | description        | status    | final_price | start_date | end_date   |
        | 101          | 1          | black friday | 30 percent off     | active    | 70.00       | 2026-11-20 | 2026-11-30 |
        | 102          | 2          | black friday | Free shipping      | active    | 25.50       | 2026-11-20 | 2026-11-30 |
        | 103          | 3          | summer sale  | Beach bundle deal  | cancelled | 15.00       | 2026-06-01 | 2026-08-31 |
        | 104          | 4          | black friday | Early bird teaser  | inactive  | 80.00       | 2026-11-15 | 2026-11-19 |
        | 105          | 5          | summer sale  | Pool party pack    | inactive  | 30.00       | 2026-07-01 | 2026-07-15 |
    When I visit the "Home Page"
    And I select "inactive" in the "Status" dropdown
    And I set the "Campaign" to "black friday"
    And I press the "Search" button
    Then I should see "Early bird teaser" in the results
    And I should see the message "Success"
    And I should not see "30 percent off" in the results
    And I should not see "Free shipping" in the results
    And I should not see "Pool party pack" in the results
    And I should not see "Beach bundle deal" in the results

Scenario: No promotions match the filters
    When I visit the "Home Page"
    And I select "cancelled" in the "Status" dropdown
    And I set the "Campaign" to "black friday"
    And I press the "Search" button
    Then I should see "No promotions found" in the results
    And I should see the message "No promotions found"
    And I should not see "30 percent off" in the results
    And I should not see "Beach bundle deal" in the results

Scenario: Clearing the filters and searching again restores the full list
    When I visit the "Home Page"
    And I select "cancelled" in the "Status" dropdown
    And I set the "Campaign" to "summer sale"
    And I press the "Search" button
    Then I should see "Beach bundle deal" in the results
    And I should not see "30 percent off" in the results
    When I press the "Clear" button
    Then the "Status" field should be empty
    And the "Campaign" field should be empty
    When I press the "Search" button
    Then I should see "30 percent off" in the results
    And I should see "Free shipping" in the results
    And I should see "Beach bundle deal" in the results
