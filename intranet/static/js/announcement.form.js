$(function() {
    $("select#id_groups").selectize({
        plugins: ["remove_button"],
        placeholder: "Everyone"
    });

    var reset = $("#id_expiration_date").val() != "3000-01-01 00:00:00";
    $("#id_expiration_date").click(function() {
        if(!reset) {
            var d = new Date();
            date_str = (d.getFullYear()) + "-" + 
                       (d.getMonth() < 9 ? "0"+(d.getMonth()+1) : d.getMonth()+1) + "-" +
                       (d.getDate() < 10 ? "0"+d.getDate() : d.getDate()) + " " + 
                       (d.getHours() < 10 ? "0"+d.getHours() : d.getHours()) + ":" +
                       (d.getMinutes() < 10 ? "0"+d.getMinutes() : d.getMinutes()) + ":" + 
                       "00";
            $(this).val(date_str);
            reset = true;
        }
    }).datetimepicker({
        lazyInit: true,
        format: "Y-m-d H:i:s"
    });


    // for approval page
    $("select#id_teachers_requested").selectize({
        plugins: ["remove_button"]
    });
});