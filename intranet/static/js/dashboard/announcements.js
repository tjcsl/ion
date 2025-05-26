/* global $ */
$(document).ready(function() {
    updatePartiallyHidden();

    filterClubAnnouncements();

    $(".club-announcements-header").click(function () {
        let content = $(".club-announcements-content");
        if (!content.is(":visible")) {  // Avoid FOUC
            content.show();
            updatePartiallyHidden();
            content.hide();
        }
        content.slideToggle();
        $(".club-announcements-toggle-icon").toggleClass("fa-chevron-down fa-chevron-up");
    });

    $(".club-announcements-content").on("click", ".announcement[data-id] h3", function (e) {
        if (e.target !== this) return;
        var btn = $(".announcement-toggle", $(this));
        announcementToggle.call(btn);
    });

    $(".club-announcements-content").on("click", ".announcement[data-id] h3 .announcement-toggle", function (e) {
        e.preventDefault();
        announcementToggl
l($(this));
    });
    
    $(".club-announcements-content").on("click", ".announcement[data-id] h3 .dashboard-item-icon", function (e) {
        e.preventDefault();
        var btn = $(".announcement-toggle", $(this).parent());
        announcementToggle.call(btn);
    });

    $(window).resize(function () { setTimeout(updatePartiallyHidden, 0); });

    $("div[data-placeholder]").on("keydown keypress input", function () {
        if (this.textContent) {
            this.dataset.divPlaceholderContent = 'true';
        } else {
            delete this.dataset.divPlaceholderContent;
        }
    });

    $(".subscribed-filter").click(function () {
        $(".unsubscribed-filter").removeClass("active");
        $("#non-subscriptions-pagination").hide();

        $("#subscriptions-pagination").show();
        $(this).addClass("active");

        filterClubAnnouncements();
    });

    $(".unsubscribed-filter").click(function () {
        $(".subscribed-filter").removeClass("active");
        $("#subscriptions-pagination").hide();

        $("#non-subscriptions-pagination").show();
        $(this).addClass("active");

        filterClubAnnouncements();
    });

    const params = new URLSearchParams(window.location.search);
    if (params.get("flip_to") == "unsubscribed") {
      $(".unsubscribed-filter").click();
    }
});

function updatePartiallyHidden() {
    if (window.disable_partially_hidden_announcements) {
        return;
    }

    $(".announcement:not(.toggled):not(.hidden).partially-hidden").each(function () {
        var content = $(this).find(".announcement-content");
        if (content.height() <= 200) {
            $(this).removeClass("partially-hidden");
            content.off("click");
        }
    });
    $(".announcement:not(.toggled):not(.hidden):not(.partially-hidden)").each(function () {
        var content = $(this).find(".announcement-content");
        if (content.height() > 200) {
            $(this).addClass("partially-hidden");
            content.click(function () {
                announcementToggle.call($(this).closest(".announcement"));
            });
        }
        else {
            content.off("click");
        }
    });
}

function loadMoreClubAnnouncements(fetchLimit, offset) {
    $.ajax({
        url: "/api/announcements/load-more-club-announcements",
        type: "GET",
        data: { fetch_limit: fetchLimit, offset },
        success: function(data) {
            if (data.next_announcements.length > 0) {
                data.next_announcements.forEach(function(annHtml) {
                    const $wrapper = $("<div>").html(annHtml);

                    $wrapper.find(".announcement").addClass("next-club-announcement-to-show");

                    const $filtered = $wrapper.contents().filter(function () {
                        return this.nodeType === 1 && (this.tagName === "DIV" || this.tagName === "SCRIPT");
                    });

                    $(".club-announcements-content").append($filtered);
                });
                updatePartiallyHidden();
            }
        },
        error: function(xhr, status, error) {
            console.error("AJAX error:", status, error);
            console.error("Response:", xhr.responseText);
        }
    })
}

function announcementToggle() {
    var announcement = $(this).closest(".announcement");
    var announcementContent = $(".announcement-toggle-content", announcement);
    var icon = $(this).children(0);
    var id = announcement.attr("data-id");

    if (announcement.hasClass("partially-hidden")) {
        announcement.addClass("toggled");

        announcement.find(".announcement-content").off("click");

        announcementContent.animate(
            { "max-height": announcement.find(".announcement-content").height() },
            {
                "duration": 350,
                complete: function () {
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
    });

    announcement.addClass("toggled");

    if (action === "show") {
        icon.removeClass("fa-expand")
            .addClass("fa-compress")
            .attr("title", icon.attr("data-visible-title"));

        setTimeout(function () {
            announcement.removeClass("hidden");
        }, 450);

        announcementContent.css("display", "");
        announcementContent.slideDown(350);
    } else {
        icon.removeClass("fa-compress")
            .addClass("fa-expand")
            .attr("title", icon.attr("data-hidden-title"));

        if (announcement.hasClass("remove-on-collapse")) {
            announcement.slideUp(350);
            setTimeout(function () {
                announcement.remove();
                const numAnnouncementsSpan = $(".num-club-announcements");
                const numAnnouncements = numAnnouncementsSpan.text().match(/\d+/);

                if(!announcement.hasClass("announcement-read")) {
                    numAnnouncementsSpan.text(numAnnouncements - 1);
                    announcement.addClass("announcement-read");
                    let newAnnouncement = $(".next-club-announcement-to-show").first();
                    newAnnouncement.toggleClass("next-club-announcement-to-show");
                    newAnnouncement.fadeIn(350);
                }

                const fetchLimit = 15
                const offset = 5

                if(numAnnouncements > fetchLimit - offset && $(".next-club-announcement-to-show").length === offset) {
                    loadMoreClubAnnouncements(fetchLimit, offset);
                }

                $(".club-announcements:has(.club-announcements-content:not(:has(.announcement)))").slideUp(350);
            }, 450);
        } else {
            setTimeout(function () {
                announcement.addClass("hidden");
            }, 450);
            announcementContent.css("display", "");
            announcementContent.slideUp(350);
        }
    }
};

function filterClubAnnouncements() {
    if ($(".subscribed-filter").hasClass("active")) {
        $(".announcement").each(function () {
            if ($(this).hasClass("exclude-subscribed-filer")) {
                $(this).fadeIn();
                return;
            }
            if ($(this).hasClass("subscribed")) {
                $(this).fadeIn();
            } else {
                $(this).hide();
            }
        });
    } else if ($(".unsubscribed-filter").hasClass("active")) {
        $(".announcement").each(function () {
            if ($(this).hasClass("exclude-subscribed-filer")) {
                $(this).fadeIn();
                return;
            }
            if ($(this).hasClass("subscribed")) {
                $(this).hide();
            } else {
                $(this).fadeIn();
            }
        });
    }
    updatePartiallyHidden();
}
