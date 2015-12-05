$(function() {
    $("select#id_groups").selectize({
        plugins: ["remove_button"],
        placeholder: "Everyone"
    });

    var reset = $("#id_expiration_date").val() != "3000-01-01 00:00:00";
    $("#id_expiration_date").datetimepicker({
        lazyInit: true,
        format: "Y-m-d H:i:s"
    });


    // for approval page
    $("select#id_teachers_requested").selectize({
        plugins: ["remove_button"],
        maxItems: 2
    });
});