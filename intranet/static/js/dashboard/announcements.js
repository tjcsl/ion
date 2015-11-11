$(document).ready(function() {

    $("div[data-placeholder]").on("keydown keypress input", function() {
        if(this.textContent) {
            this.dataset.divPlaceholderContent = 'true';
        } else {
            delete(this.dataset.divPlaceholderContent);
        }
    });

    function announcementToggle() {
        var announcement = $(this).parent().parent().parent();
        var announcementContent = $(".announcement-toggle-content", announcement);
        var icon = $(this).children(0);
        var id = announcement.attr("data-id");

        if(!id) {
            console.error("Couldn't toggle invalid announcement ID");
            return;
        }

        var hidden = announcement.hasClass("hidden");
        var action = hidden ? "show" : "hide";
        $.post("/announcements/" + action + "?" + id, {announcement_id: id}, function() {
            console.info("Announcement "+id+" "+action);
        });
        if(action === "show") {
            icon.removeClass("fa-toggle-off")
                    .addClass("fa-toggle-on")
                    .attr("title", icon.attr("data-visible-title"));
            setTimeout(function() {
                announcement.removeClass("hidden");
            }, 450);
            announcementContent.slideDown(350);
        } else {
            icon.removeClass("fa-toggle-on")
                    .addClass("fa-toggle-off")
                    .attr("title", icon.attr("data-hidden-title"));
            setTimeout(function() {
                announcement.addClass("hidden");
            }, 450);
            announcementContent.slideUp(350);
        }
    };

    $(".announcement[data-id] h3").click(function(e) {
        if(e.target !== this) {
            return;
        }
        var btn = $(".announcement-toggle", $(this));
        announcementToggle.call(btn);
    });

    $(".announcement[data-id] h3 .announcement-toggle").click(function() {
        announcementToggle.call($(this));
    });
});
