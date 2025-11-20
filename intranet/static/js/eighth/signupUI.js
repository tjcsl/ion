// Scripts for initial layout, sticky headers, etc.
/* global $ */
var calcMaxScrollLeft = function() {
    var $daysContainer = $(".days-container");
    return $daysContainer[0].scrollWidth - $daysContainer.width();
}

var centerCurrentDay = function(animate) {
    var $day = $(".current-day");
    var dayWidth = $(".day:first").width() + 1;
    var numPrevDays = $day.prevAll().length;
    var $daysContainer = $(".days-container");
    var containerWidth = $daysContainer.width();
    var scrollCenter = numPrevDays * dayWidth - (containerWidth - dayWidth) / 2;

    // Scroll to day
    if (animate) {
        $daysContainer.animate({
            scrollLeft: scrollCenter
        }, {
            duration: 150,
            easing: "swing"
        });
    } else {
        $daysContainer.scrollLeft(scrollCenter);
    }
}

var centerBlocks = function() {
    // Scroll to block if there are more than two blocks on any given day
    var $activeBlock = $(".active-block");
    $activeBlock.parents(".blocks.many-blocks").scrollTo($activeBlock);
}

var updateDayNavButtonStatus = function() {
    // Update the state of buttons to reflect whether it is possible to
    // move left or right
    var maxScrollLeft = calcMaxScrollLeft();
    var scrollLeft = $(".days-container").scrollLeft();

    var $earlierDays = $(".earlier-days");
    var $laterDays = $(".later-days");
    $earlierDays.removeAttr("disabled");
    $laterDays.removeAttr("disabled");

    if (scrollLeft === 0) {
        $earlierDays.attr("disabled", true);
    }

    if (Math.abs(scrollLeft - maxScrollLeft) <= 1) {
        // Weird stuff sometimes happens when resizing/zooming window
        // so sometimes these scrollLeft and maxScrollLeft get off by a pixel
        // when they are supposed to be equal
        $laterDays.attr("disabled", "disabled");
    }
}

var scrollBlockChooser = function(dir) {
    // The left and right arrows are used to select which day should be centered
    // in the block chooser, but sometimes adjacent blocks at the far left and right
    // can not be centered. In this case, the user still expects the arrows to slide
    // the blocks left and right, so we keep selecting the next/previous block until
    // the block chooser is able to scroll and center the selected block
    var $daysContainer = $(".days-container");
    var initialScrollLeft = $daysContainer.scrollLeft();
    var tries = 10;

    var $currentDay = $(".current-day");
    while (tries-- && $daysContainer.scrollLeft() === initialScrollLeft) {
        var $nextCurrentDay = $currentDay[dir]();

        if ($nextCurrentDay.length !== 0) {
            $currentDay.removeClass("current-day");
            $nextCurrentDay.addClass("current-day");
        }

        $currentDay = $nextCurrentDay;
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
var StickyHeaders = function(headers) {
    this.load = function() {
        var firstEmpty = false;
        headers.each(function(i) {
            var id = Math.floor((i + 1) * Math.random() * 99999);
            var stuckCopy = $(this).clone().prependTo($("#activity-picker"));
            var empty = $(this).hasClass("empty");

            if (i === 0 && empty) {
                firstEmpty = true;
            }

            if (i === 0 && !empty || i === 1 && firstEmpty) {
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

            if (prevHeader.hasClass("empty")) {
                prevHeader = thrdHeader;
            }

            if (top <= 0) {
                if (!thisHeader.hasClass("empty")) {
                    $("#" + thisHeader.attr("id") + "-stuck").removeClass("hidden");
                }

                headers.each(function(j) {
                    var loopHeader = $(this);

                    if (j !== i) {
                        $("#" + loopHeader.attr("id") + "-stuck").addClass("hidden");
                    }
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
    var sh = new StickyHeaders($(".sticky-header"));
    sh.load();

    $("#activity-list").on("scroll", function() {
        sh.scroll();
    });

    var initX = null,
        initY = null,
        listening = false;

    $(".day-picker").on({
        "touchstart": function(e) {
            e.stopPropagation();
            initX = e.originalEvent.touches[0].clientX;
            initY = e.originalEvent.touches[0].clientY;
            listening = true;
        },
        "touchend": function(e) {
            e.stopPropagation();
            listening = false;
        },
        "touchmove": function(e) {
            e.stopPropagation();

            if (!listening) return;

            var nowX = e.originalEvent.touches[0].clientX,
                nowY = e.originalEvent.touches[0].clientY;

            if (Math.abs(nowY - initY) > 30) {
                listening = false;
                return;
            }

            var diffX = nowX - initX;

            if (Math.abs(diffX) > 30) {
                if (diffX > 0) $(".earlier-days").click();
                else $(".later-days").click();

                listening = false;
            }
        }
    });

    $("#activityPicker").on({
        "touchstart": function(e) {
            if ($("#activity-picker > .backbtn").hasClass("visible")) {
                e.stopPropagation();
                initX = e.originalEvent.touches[0].clientX;
                initY = e.originalEvent.touches[0].clientY;
                listening = true;
            }
        },
        "touchend": function(e) {
            if ($("#activity-picker > .backbtn").hasClass("visible")) {
                e.stopPropagation();
                listening = false;
            }
        },
        "touchmove": function(e) {
            var back = $("#activity-picker > .backbtn");

            if (back.hasClass("visible")) {
                e.stopPropagation();

                if (!listening) return;

                var nowX = e.originalEvent.touches[0].clientX,
                    nowY = e.originalEvent.touches[0].clientY;

                if (Math.abs(nowY - initY) > 30) {
                    listening = false;
                    return;
                }

                var diffX = nowX - initX;

                if (Math.abs(diffX) > 30) {
                    if (diffX > 0) back.click();

                    listening = false;
                }
            }
        }
    });

    $(window).keydown(function(e) {
        var selected = $("#activity-list li.selected:not(.search-hide)");

        if (selected.length > 0) {
            var flag = false;

            if (e.which === 38) {
                // up arrow key
                selected.prevAll("li:not(.search-hide)").first().click();
                e.preventDefault();
                flag = true;
            } else if (e.which === 40) {
                // down arrow key
                selected.nextAll("li:not(.search-hide)").first().click();
                e.preventDefault();
                flag = true;
            }

            if (flag) {
                var scrollParent = $("#activity-list");
                selected = $("#activity-list li.selected");
                scrollParent.scrollTop(scrollParent.scrollTop() + selected.position().top - scrollParent.height() / 2 + selected.height() / 2);
            }
        }
    });
});
