$(function () {

    // Change this one line when the Flask-RESTX refactor moves the API to /api
    const API = "/promotions";

    // ---------- utilities (shared by every button) ----------
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
        if ((v = $("#promotion_id").val().trim())) { data.promotion_id = parseInt(v, 10); }
        if ((v = $("#promotion_product_id").val().trim())) { data.product_id = parseInt(v, 10); }
        if ((v = $("#promotion_campaign").val().trim())) { data.campaign = v; }
        if ((v = $("#promotion_description").val().trim())) { data.promotion_description = v; }
        if ((v = $("#promotion_status").val())) { data.status = v; }
        if ((v = $("#promotion_final_price").val().trim())) { data.final_price = parseFloat(v); }
        if ((v = $("#promotion_start_date").val())) { data.start_date = v; }
        if ((v = $("#promotion_end_date").val())) { data.end_date = v; }
        return data;
    }

    // ---------- Clear ----------
    $("#clear-btn").click(function () {
        $("#promotion_id").val("");
        $("#flash_message").empty();
        clear_fields();
    });
        // Add your code here for the other buttons (Create, Read, List, Update, Delete, Query, Action)
            
});