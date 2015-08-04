$(document).ready(function() {
    window.initEighthResponsive = function() {
        is_small = function() {
            return $("#activity-detail").css("right").split(/[^\-\d]+/)[0] < 0;;
        }

        $("#activity-list li[data-activity-id]").click(function() {
            if(is_small()) {
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

        $(".middle .switch").click(function() {
            $(".primary-content").toggleClass("viewing");
            activityPickerResize();
        });

        var width = $(window).width();
        var height = $(window).height();
        if(width <= 500 && height <= 745 && !window.isDefaultPage) {
            setTimeout(function() {
                $(".eighth-signup .switch").click();

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
    console.debug("activity picker resize")
    var h = $(window).height();
    var w = $(window).width();
    var p = $("#activity-picker");
    var topInfo = $(".middle-wrapper").height() + $(".header").height() + 15; // 163
    var btnDown = $(".primary-content").hasClass("viewing") && w <= 500 ? 0 : 120; // 120
    var pixels = h - topInfo - btnDown;
    if(pixels < 300) {
        // minimum usable height
        pixels = 300;
    }
    p.css({ height: (pixels)+"px" });
}