$(document).ready(function() {
    $("#mail-forwarding-submit").click(function(e){
        e.preventDefault();
        $("#username").removeAttr("disabled");
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
        }).fail(function() {
            Messenger().post({
                message: "Unable to set up forwarding.",
                type: "error"
            });
            $("#username").attr("disabled", "disabled");
        });
    });
});
