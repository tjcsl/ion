$(function() {
    function eventToggle() {
        var event = $(this).parent().parent().parent();
        var eventContent = $(".event-toggle-content", event);
        var icon = $(this).children(0);
        var id = event.attr("data-id");

        if (!id) {
            console.error("Couldn't toggle invalid event ID");
            return;
        }

        var hidden = event.hasClass("hidden");
        var action = hidden ? "show" : "hide";

        $.post("/events/" + action + "?" + id, {
            event_id: id
        }, function() {
            console.info("event", id, action);
        });

        if (action === "show") {
            icon.removeClass("fa-expand")
                .addClass("fa-compress")
                .attr("title", icon.attr("data-visible-title"));

            setTimeout(function() {
                event.removeClass("hidden");
            }, 450);

            eventContent.css("display", "");
            eventContent.slideDown(350);
        } else {
            icon.removeClass("fa-compress")
                .addClass("fa-expand")
                .attr("title", icon.attr("data-hidden-title"));

            setTimeout(function() {
                event.addClass("hidden");
            }, 450);

            eventContent.css("display", "");
            eventContent.slideUp(350);
        }
    }

    $(".event[data-id] h3").click(function(e) {
        if (e.target !== this) return;
        var btn = $(".event-toggle", $(this));
        eventToggle.call(btn);
    });

    $(".event[data-id] h3 .event-toggle").click(function(e) {
        e.preventDefault();
        eventToggle.call($(this));
    });

    $(".event[data-id] h3 .dashboard-item-icon").click(function(e) {
        e.preventDefault();
        var btn = $(".event-toggle", $(this).parent());
        eventToggle.call(btn);
    });
});
