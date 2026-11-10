
$(function () {

    // Change this one line when the Flask-RESTX refactor moves the API to /api
    const API = "/promotions";

    // ---------- Utilities (shared by every button) ----------
    function fill_form(res) {
        $("#promotion_id").val(res.promotion_id);
        $("#promotion_product_id").val(res.product_id);
        $("#promotion_campaign").val(res.campaign);
        $("#promotion_description").val(res.promotion_description);
        $("#promotion_status").val(res.status);
        $("#promotion_final_price").val(res.final_price);
        $("#promotion_start_date").val(res.start_date);
        $("#promotion_end_date").val(res.end_date);
    }

    function clear_fields() {
        $("#promotion_product_id, #promotion_campaign, #promotion_description, " +
          "#promotion_final_price, #promotion_start_date, #promotion_end_date").val("");
        $("#promotion_status").val("");
    }

    function flash_message(message) {
        $("#flash_message").text(message);
    }

    function error_text(res) {
        return (res.responseJSON && res.responseJSON.message) || "Server error!";
    }

    // Reads the form; blank fields are left out of the payload
    function read_form() {
        let data = {};
        let v;

        if ((v = $("#promotion_id").val().trim())) {
            data.promotion_id = parseInt(v, 10);
        }
        if ((v = $("#promotion_product_id").val().trim())) {
            data.product_id = parseInt(v, 10);
        }
        if ((v = $("#promotion_campaign").val().trim())) {
            data.campaign = v;
        }
        if ((v = $("#promotion_description").val().trim())) {
            data.promotion_description = v;
        }
        if ((v = $("#promotion_status").val())) {
            data.status = v;
        }
        if ((v = $("#promotion_final_price").val().trim())) {
            data.final_price = parseFloat(v);
        }
        if ((v = $("#promotion_start_date").val())) {
            data.start_date = v;
        }
        if ((v = $("#promotion_end_date").val())) {
            data.end_date = v;
        }

        return data;
    }

    // ---------- Clear ----------
    $("#clear-btn").click(function () {
        $("#promotion_id").val("");
        $("#flash_message").empty();
        clear_fields();
    });

    // Add your code here for the other buttons
    // (Read, List, Update, Delete, Query, Action)

    // ---------- Create ----------
    $("#create-btn").click(function () {
        $("#flash_message").empty();

        let data = read_form();
        delete data.promotion_id; // ID is generated automatically

        const requiredFields = [
            ["product_id", "Product ID"],
            ["start_date", "Start Date"],
            ["end_date", "End Date"],
            ["status", "Status"],
            ["final_price", "Final Price"],
            ["promotion_description", "Description"],
            ["campaign", "Campaign"]
        ];

        const missingFields = requiredFields.filter(([key]) =>
        data[key] === undefined ||
        data[key] === null ||
        data[key] === "" ||
        Number.isNaN(data[key])).map(([, label]) => label);

        if (missingFields.length > 0) {
            flash_message("Please fill in: " + missingFields.join(", "));
            return;
        }
        
        $.ajax({
            type: "POST",
            url: API,
            contentType: "application/json",
            data: JSON.stringify(data)
        })
        .done(function (res) {
            fill_form(res);
            flash_message("Success");
        })
        .fail(function (res) {
            flash_message(error_text(res));
        });
    });

    // ---------- Retrieve ----------
    $("#retrieve-btn").click(function () {
        let id = $("#promotion_id").val().trim();
        $("#flash_message").empty();

        // The ID must be a positive whole number;
        // anything else never reaches the server
        if (!/^[1-9][0-9]*$/.test(id)) {
            clear_fields();
            flash_message("Please enter a valid Promotion ID (a positive whole number)");
            return;
        }

        $.ajax({
            type: "GET",
            url: `${API}/${id}`
        })
        .done(function (res) {
            fill_form(res);
            flash_message("Success");
        })
        .fail(function (res) {
            clear_fields();
            flash_message(res.status === 404 ? "Promotion not found" : error_text(res));
        });
    });

    // ---------- List ----------
    // The Query ticket (#60) will return the filters from the form here
    function query_string() {
        return "";
    }

    function show_results(promotions) {
        $("#search_results").empty();

        let table = $('<table class="table table-striped"></table>');

        let head = [
            "Promotion ID",
            "Product ID",
            "Campaign",
            "Description",
            "Status",
            "Final Price",
            "Start Date",
            "End Date"
        ];

        let tr = $("<tr></tr>");

        head.forEach(h => tr.append($("<th></th>").text(h)));

        table.append($("<thead></thead>").append(tr));

        let body = $("<tbody></tbody>");

        if (promotions.length === 0) {
            body.append(
                $("<tr></tr>").append(
                    $('<td colspan="8"></td>').text("No promotions found")
                )
            );
        }

        promotions.forEach(function (p, i) {
            let row = $("<tr></tr>").attr("id", `row_${i}`);

            [
                p.promotion_id,
                p.product_id,
                p.campaign,
                p.promotion_description,
                p.status,
                p.final_price,
                p.start_date,
                p.end_date
            ].forEach(c => row.append($("<td></td>").text(c)));

            body.append(row);
        });

        table.append(body);
        $("#search_results").append(table);
    }

    // ---------- Search ----------
    $("#search-btn").click(function () {
        $("#flash_message").empty();

        $.ajax({
            type: "GET",
            url: `${API}${query_string()}`
        })
        .done(function (res) {
            show_results(res);
            flash_message(res.length === 0 ? "No promotions found" : "Success");
        })
        .fail(function (res) {
            flash_message(error_text(res));
        });
    });
});
