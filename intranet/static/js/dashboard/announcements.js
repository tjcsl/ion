$(document).ready(function() {

    $("div[data-placeholder]").on("keydown keypress input", function() {
        if(this.textContent) {
            this.dataset.divPlaceholderContent = 'true';
        } else {
            delete(this.dataset.divPlaceholderContent);
        }
    });

    $(".announcement .announcement-toggle").click(function(e) {
        e.preventDefault();
        var announcement = $(this).parent().parent().parent();
        var icon = $(this).children(0);
        var id = announcement.attr("data-id");

        var hidden = announcement.hasClass("hidden");
        var action = hidden ? "show" : "hide";
        $.post("/announcements/" + action + "?" + id, {id: id}, function(d) {
            console.info("Announcement "+id+" "+action);
        });
        if(action == "show") {
            announcement.removeClass("hidden");
            icon.removeClass("fa-toggle-off").addClass("fa-toggle-on");
        } else {
            announcement.addClass("hidden");
            icon.removeClass("fa-toggle-on").addClass("fa-toggle-off");
        }
    })
});
