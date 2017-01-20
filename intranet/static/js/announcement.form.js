/* global $ */
$(function() {
    $("select#id_groups").selectize({
        plugins: ["remove_button"],
        placeholder: "Everyone"
    });

    var reset = $("#id_expiration_date").val() !== "3000-01-01 00:00:00";
    $("#id_expiration_date").datetimepicker({
        lazyInit: true,
        format: "Y-m-d H:i:s"
    });

    // for approval page
    $("select#id_teachers_requested").selectize({
        plugins: ["remove_button"],
        maxItems: 2
    });
    
    $("form#announcement_form").bind("submit", function () {
        var button = $("button#submit_announcement");
        button.prop("disabled", true);
        button.append("<i class=\"fa fa-spinner fa-spin\" aria-hidden=\"true\"></i>")

        if ($("input#id_title").val() === "")
            button.prop("disabled", false);
    });
});
