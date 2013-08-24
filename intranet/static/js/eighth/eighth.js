// Scripts for initial layout, sticky headers, etc.

// Center current day in day picker
$(document).ready(function() {
    var containerWidth = $(".day-picker").width();
    var blocksWidth = $(".days-container").width();
    $(".days-container").css("margin-left", (containerWidth - blocksWidth) / 2);


    $(".day-nav").click(function(e) {
        var offset = ($(".day").width() + 1) + "px"
        if ($(e.target).parents().andSelf().hasClass("later-days")) {
            offset = "-=" + offset;
        } else {
            offset = "+=" + offset;
        }

        $(".days-container").animate({
            marginLeft: offset
        }, {
            duration: 200,
            easing: "swing"
        });
    });
});

// Sticky headers for activity picker
function stickyHeaders(headers) {
    this.load = function() {
        headers.each(function(i) {
            var id = Math.floor((i + 1) * Math.random() * 99999);
            var stuckCopy = $(this).clone().prependTo($(".activity-picker"));
            if (i == 0) {
                stuckCopy.addClass("stuck");
            } else {
                stuckCopy.addClass("hidden stuck");
            }
            stuckCopy.removeClass("sticky-header");
            $(this).attr("id", id);
            stuckCopy.attr("id", id + "-stuck");
        });
    }

    this.scroll = function() {
        headers.each(function(i) {
            var thisHeader = $(this),
                prevHeader = headers.eq(i - 1);
            var top = thisHeader.position().top;

            if (top <= 0) {
                $("#" + thisHeader.attr("id") + "-stuck").removeClass("hidden");
                $("#" + prevHeader.attr("id") + "-stuck").addClass("hidden");
            } else if (top < 31) {
                $("#" + prevHeader.attr("id") + "-stuck").css("top", top);
            } else {
                $("#" + prevHeader.attr("id") + "-stuck").css("top", 31);
            }
        });
    }


}

$(document).ready(function() {
    var sh = new stickyHeaders($(".sticky-header"));
    sh.load();

    $("#activity-list").on("scroll", function() {
        sh.scroll();
    });
});