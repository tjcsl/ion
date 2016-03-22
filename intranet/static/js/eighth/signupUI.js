// Scripts for initial layout, sticky headers, etc.

function calcMaxScrollLeft() {
    return $(".days-container")[0].scrollWidth - $(".days-container").width();
}

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
        $(".days-container").scrollLeft(scrollCenter);
    }
}

function centerBlocks() {
    // Scroll to block if there are more than two blocks on any given day
    var $activeBlock = $(".active-block");
    $activeBlock.parents(".blocks.many-blocks").scrollTo($activeBlock);
}

function updateDayNavButtonStatus() {
    // Update the state of buttons to reflect whether it is possible to
    // move left or right
    var maxScrollLeft = calcMaxScrollLeft();
    var scrollLeft = $(".days-container").scrollLeft();

    $(".earlier-days").removeAttr("disabled");
    $(".later-days").removeAttr("disabled");

    if (scrollLeft == 0) {
        $(".earlier-days").attr("disabled", "disabled");
    }

    if (Math.abs(scrollLeft - maxScrollLeft) <= 1) {
        // Weird stuff sometimes happens when resizing/zooming window
        // so sometimes these scrollLeft and maxScrollLeft get off by a pixel
        // when they are supposed to be equal
        $(".later-days").attr("disabled", "disabled");
    }


}

function scrollBlockChooser(dir) {
    // The left and right arrows are used to select which day should be centered
    // in the block chooser, but sometimes adjacent blocks at the far left and right
    // can not be centered. In this case, the user still expects the arrows to slide
    // the blocks left and right, so we keep selecting the next/previous block until
    // the block chooser is able to scroll and center the selected block
    var $daysContainer = $(".days-container");
    var initialScrollLeft = $daysContainer.scrollLeft();
    var tries = 10;


    while(tries-- && $daysContainer.scrollLeft() == initialScrollLeft) {
        var $currentDay = $(".current-day");
        var $nextCurrentDay = $currentDay[dir]();
        if ($nextCurrentDay.length != 0) {
            $currentDay.removeClass("current-day")
            $nextCurrentDay.addClass("current-day");
        }

        centerCurrentDay(false);
    }

    var newScrollLeft = $daysContainer.scrollLeft();
    $daysContainer.scrollLeft(initialScrollLeft);

    $(".days-container").animate({
        scrollLeft: newScrollLeft
    }, {
        duration: 150,
        easing: "swing",
        done: updateDayNavButtonStatus
    });
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

    $(".day-picker-buttons button").click(function(e) {
        var $currentDay = $(".current-day");

        if ($(e.target).parents().andSelf().hasClass("later-days")) {
            // Right button clicked
            scrollBlockChooser("next");
        } else {
            // Left button clicked
            scrollBlockChooser("prev");
        }
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
        var firstEmpty = false;
        headers.each(function(i) {
            var id = Math.floor((i + 1) * Math.random() * 99999);
            var stuckCopy = $(this).clone().prependTo($("#activity-picker"));
            var empty = $(this).hasClass("empty");
            if(i == 0 && empty) {
                firstEmpty = true;
            }
            if ((i == 0 && !empty) || (i == 1 && firstEmpty)) {
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
                prevHeader = headers.eq(i - 1),
                thrdHeader = headers.eq(i - 2);
            var top = thisHeader.position().top;

            if(prevHeader.hasClass("empty")) {
                prevHeader = thrdHeader;
            }

            if (top <= 0) {
                if(!thisHeader.hasClass("empty")) {
                    $("#" + thisHeader.attr("id") + "-stuck").removeClass("hidden");
                }
                headers.each(function(j) {
                    var loopHeader = $(this);
                    if(j != i) $("#" + loopHeader.attr("id") + "-stuck").addClass("hidden");
                });
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

    var initX = null, initY = null, listening = false;
    $(".day-picker").on("touchstart", function(e) {
        e.stopPropagation();
        initX = e.originalEvent.touches[0].clientX;
        initY = e.originalEvent.touches[0].clientY;
        listening = true;
    });
    $(".day-picker").on("touchend", function(e) {
        e.stopPropagation();
        listening = false;
    });
    $(".day-picker").on("touchmove", function(e) {
        e.stopPropagation();
        if (!listening) {
            return;
        }
        var nowX = e.originalEvent.touches[0].clientX;
        var nowY = e.originalEvent.touches[0].clientY;
        if (Math.abs(nowY - initY) > 30) {
            listening = false;
            return;
        }
        var diffX = nowX - initX;
        if (Math.abs(diffX) > 30) {
            if (diffX > 0) {
                $(".earlier-days").click();
            }
            else {
                $(".later-days").click();
            }
            listening = false;
        }
    });
});
