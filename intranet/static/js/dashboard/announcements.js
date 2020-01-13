/* global $ */
$(document).ready(function() {

    $("div[data-placeholder]").on("keydown keypress input", function() {
        if (this.textContent) {
            this.dataset.divPlaceholderContent = 'true';
        } else {
            delete this.dataset.divPlaceholderContent;
        }
    });

    function updatePartiallyHidden() {
        if(window.disable_partially_hidden_announcements) {
            return;
        }

        $(".announcement:not(.toggled):not(.hidden).partially-hidden").each(function() {
            var content = $(this).find(".announcement-content");
            if(content.height() <= 200) {
                $(this).removeClass("partially-hidden");
                content.off("click");
            }
        });
        $(".announcement:not(.toggled):not(.hidden):not(.partially-hidden)").each(function() {
            var content = $(this).find(".announcement-content");
            if(content.height() > 200) {
                $(this).addClass("partially-hidden");
                content.click(function() {
                    announcementToggle.call($(this).closest(".announcement"));
                });
            }
            else {
                content.off("click");
            }
        });
    }
    updatePartiallyHidden();
    $(window).resize(function() {setTimeout(updatePartiallyHidden, 0);});

    function announcementToggle() {
        var announcement = $(this).closest(".announcement");
        var announcementContent = $(".announcement-toggle-content", announcement);
        var icon = $(this).children(0);
        var id = announcement.attr("data-id");

        if(announcement.hasClass("partially-hidden")) {
            announcement.addClass("toggled");

            announcement.find(".announcement-content").off("click");

            announcementContent.animate(
                {"max-height": announcement.find(".announcement-content").height()},
                {
                    "duration": 350,
                    complete: function() {
                        announcement.removeClass("partially-hidden");
                        announcementContent.css("max-height", "");
                    }
                }
            );
            return;
        }

        if (!id) {
            console.error("Couldn't toggle invalid announcement ID");
            return;
        }

        var hidden = announcement.hasClass("hidden");
        var action = hidden ? "show" : "hide";

        $.post("/announcements/" + action + "?" + id, {
            announcement_id: id
        }, function() {
            console.info("Announcement", id, action);
        });

        announcement.addClass("toggled");

        if (action === "show") {
            icon.removeClass("fa-expand")
                .addClass("fa-compress")
                .attr("title", icon.attr("data-visible-title"));

            setTimeout(function() {
                announcement.removeClass("hidden");
            }, 450);

            announcementContent.css("display", "");
            announcementContent.slideDown(350);
        } else {
            icon.removeClass("fa-compress")
                .addClass("fa-expand")
                .attr("title", icon.attr("data-hidden-title"));

            setTimeout(function() {
                announcement.addClass("hidden");
            }, 450);
            announcementContent.css("display", "");
            announcementContent.slideUp(350);
        }
    };

    $(".announcement[data-id] h3").click(function(e) {
        if (e.target !== this) return;
        var btn = $(".announcement-toggle", $(this));
        announcementToggle.call(btn);
    });

    $(".announcement[data-id] h3 .announcement-toggle").click(function(e) {
        e.preventDefault();
        announcementToggle.call($(this));
    });

    $(".announcement[data-id] h3 .dashboard-item-icon").click(function(e) {
        e.preventDefault();
        var btn = $(".announcement-toggle", $(this).parent());
        announcementToggle.call(btn);
    });
});
