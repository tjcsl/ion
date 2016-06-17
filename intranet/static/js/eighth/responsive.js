/* global $ */
window.switchRun = false;
window.eighthSwitchEvent = false;

$(function() {
    window.initEighthResponsive = function() {
        is_small = function() {
            var cssRight = $("#activity-detail").css("right");
            return cssRight ? (cssRight.split(/[^\-\d]+/)[0] < 0) : false;
        }

        $("#activity-list li[data-activity-id]").click(function() {
            if (is_small()) {
                $("#activity-picker").addClass("visible");

                setTimeout(function() {
                    $("#activity-picker .backbtn").addClass("visible");
                }, 200);
            }
        })

        $("#activity-picker .backbtn").click(function() {
            $("#activity-picker").removeClass("visible");
            $("#activity-picker .backbtn").removeClass("visible");
            $("#activity-list li[data-activity-id]").removeClass("selected");
        })

        if (!window.eighthSwitchEvent) {
            $(".middle .switch").click(function() {
                console.debug("Block switch toggle");
                $(".primary-content").toggleClass("viewing");
                activityPickerResize();
            });

            window.eighthSwitchEvent = true;
        }

        var width = $(window).width(),
            height = $(window).height();

        if (width <= 500 && height <= 745 && !window.isDefaultPage && !window.switchRun) {
            setTimeout(function() {
                if (!window.switchRun) {
                    $(".eighth-signup .switch").click();
                }

                window.switchRun = true;

                setTimeout(function() {
                    activityPickerResize();
                }, 450);
            }, 450);
        } else {
            setTimeout(function() {
                activityPickerResize();
            }, 250);
        }

        /*
         * resize #activity-picker to correct size
         * to avoid scrollbar
         */
        $(window).on("resize", function() {
            activityPickerResize();
        });
    }
})

function activityPickerResize() {
    console.debug("activity picker resize");
    var h = $(window).height(),
        w = $(window).width();
    var p = $("#activity-picker");
    var isProfile = $(".primary-content").hasClass("eighth-profile-signup");
    var pixels;

    if (isProfile) {
        var topInfo = $(".middle-wrapper").height() + $(".header").height() + 15; // 163
        var userInfo = $(".user-info-eighth").height() + 13; // 146 with 2
        pixels = h - topInfo - userInfo;
        if (pixels < 475) {
            pixels = 475;
        }
    } else {
        /* regular /eighth/signup page */
        var topInfo = $(".middle-wrapper").height() + $(".header").height() + 15; // 163
        var btnDown = $(".primary-content").hasClass("viewing") && w <= 500 ? 0 : 120; // 120
        pixels = h - topInfo - btnDown;
    }

    if (pixels < 300) {
        // minimum usable height
        pixels = 300;
    }

    p.css({
        height: pixels + "px"
    });
}
