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
