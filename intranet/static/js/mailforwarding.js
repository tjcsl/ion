$(document).ready(function() {
    $("#mail-forwarding-submit").click(function(e){
        e.preventDefault();
        $(this).addClass("load-spinner").val("  ").prop("disabled", "disabled");
        var spinner = new Spinner(spinnerOptions).spin(document.querySelector(".spinner-container"));
        $("#username").removeAttr("disabled");
        $("#mail-forwarding-submit").hide();
        $(".spinner-container").show();
        $.post("https://mailforwarding.tjhsst.edu", $("#mail-forwarding-form").serialize(), function(data) {
            if (data.error) {
                Messenger().post({
                    message: "Unable to set up forwarding. " + data.message,
                    type: "error"
                });
            }
            else {
                Messenger().post({
                    message: "Successfully configured forwarding from " + data.from + " to " + data.to + ".",
                    type: "success"
                });
            }
            $("#username").attr("disabled", "disabled");
            $("#mail-forwarding-submit").show();
            $(".spinner-container").hide();
        }).fail(function() {
            Messenger().post({
                message: "Unable to set up forwarding.",
                type: "error"
            });
            $("#username").attr("disabled", "disabled");
            $("#mail-forwarding-submit").show();
            $(".spinner-container").hide();
        });
    });
});
