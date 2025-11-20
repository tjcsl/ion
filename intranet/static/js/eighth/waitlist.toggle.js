$(function() {
    $("#toggle-waitlist").click(function(e) {
        e.preventDefault();
        var target = $( e.target );
        target.attr("disabled", true);

        if(confirm(target.attr("title") + "?")) {
            $.ajax(toggle_waitlist_endpoint, {
                success: function() {
                    if(target.attr("title").indexOf("Disable") === -1) {
                        target.attr("title", "Disable Waitlist");
                        target.text("Disable Waitlist");
                    }
                    else {
                        target.attr("title", "Enable Waitlist");
                        target.text("Enable Waitlist");
                    }
                    target.attr("disabled", false);
                },
                error: function() {
                    alert("There was an error toggling the waitlist for the current session.");
                }
            });
        }
    });
});
