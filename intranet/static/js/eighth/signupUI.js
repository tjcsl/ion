// Scripts for initial layout, sticky headers, etc.

function centerCurrentDay(animate) {
    var $day = $(".current-day");
    var dayWidth = $(".day:first").width() + 1;
    var numPrevDays = $day.prevAll().length;
    var containerWidth = $(".days-container").width();
    var scrollCenter =  numPrevDays * dayWidth - (containerWidth - dayWidth) / 2;

    // Scroll to day
    if (animate) {
        $(".days-container").animate({
            scrollLeft: scrollCenter
        }, {
            duration: 150,
            easing: "swing",
        });
    } else {
        $(".days-container").scrollLeft();
    }
}

function centerBlocks() {
    // Scroll to block if more than two blocks on the day

    var $activeBlock = $(".active-block");
    $activeBlock.parents(".blocks.many-blocks").scrollTo($activeBlock);
}

function updateDayNavButtonStatus() {
    var maxScrollLeft = $(".days-container")[0].scrollWidth - $(".days-container").width();
    var scrollLeft = $(".days-container").scrollLeft();

    $(".earlier-days").removeAttr("disabled");
    $(".later-days").removeAttr("disabled");

    if (scrollLeft == 0) {
        $(".earlier-days").attr("disabled", "disabled");
    }

    if (scrollLeft == maxScrollLeft) {
        $(".later-days").attr("disabled", "disabled");
    }


}


$(function() {
    $(".active-block").parents(".day").addClass("current-day");

    centerCurrentDay();
    centerBlocks();
    updateDayNavButtonStatus();

    $(window).resize(function() {
        centerCurrentDay();
        updateDayNavButtonStatus();
    });

    $(".days-container").scroll(function() {
        updateDayNavButtonStatus();
    })


    $(".day-picker-buttons button").click(function(e) {
        var scrollLeft = ($(".day").width() + 1) + "px";
        var $currentDay = $(".current-day");

        if ($(e.target).parents().andSelf().hasClass("later-days")) {
            // Right button clicked
            scrollLeft = "+=" + scrollLeft;

            var $nextCurrentDay = $currentDay.next();
            $
        } else {
            // Left button clicked
            scrollLeft = "-=" + scrollLeft;
            var $nextCurrentDay = $currentDay.prev();
        }

        if ($nextCurrentDay.length != 0) {
            $currentDay.removeClass("current-day")
            $nextCurrentDay.addClass("current-day");
        }

        updateDayNavButtonStatus();
        centerCurrentDay(true);
    });


    // Keep blocks highlighted while loading
    $(".block").click(function() {
        $(".active-block").removeClass("active-block");
        $(this).addClass("active-block");
    });
});

// Sticky headers for activity picker
function stickyHeaders(headers) {
    this.load = function() {
        headers.each(function(i) {
            var id = Math.floor((i + 1) * Math.random() * 99999);
            var stuckCopy = $(this).clone().prependTo($("#activity-picker"));
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

$(function() {
    var sh = new stickyHeaders($(".sticky-header"));
    sh.load();

    $("#activity-list").on("scroll", function() {
        sh.scroll();
    });
});
