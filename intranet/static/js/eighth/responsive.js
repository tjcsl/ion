$(document).ready(function() {
    is_small = function() {
        return $("#activity-detail").css("right").split(/[^\-\d]+/)[0] < 0;;
    }

    $("#activity-list li[data-activity-id]").click(function() {
        if(is_small()) {
            $("#activity-detail").addClass("visible");
            setTimeout(function() {
                $("#activity-picker .backbtn").addClass("visible");
            }, 200);
        }
    })

    $("#activity-picker .backbtn").click(function() {
        $("#activity-detail").removeClass("visible");
        $("#activity-picker .backbtn").removeClass("visible");
        $("#activity-list li[data-activity-id]").removeClass("selected");
    })

    $(".search-wrapper input").focus(function() {
        if (is_small()) {
            $("#activity-list li[data-activity-id]").removeClass("selected");
        }
        $("#activity-detail").removeClass("visible");
        $("#activity-picker .backbtn").removeClass("hidden");
    })

    eighthResize = function() {
        var height = document.documentElement.clientHeight;
        if(height < 650 && height - 90 > 250) {
            $("#activity-picker").css("height",  height - 90);
            $(".primary-content").addClass("viewing");

        }
    }
    $(document).bind("resize", eighthResize);
    eighthResize();
    /*$("html,body").animate({
        scrollTop: $("#activity-picker").offset().top
    }, 500);*/

    $(".middle .switch").click(function() {
        $(".primary-content").toggleClass("viewing");
    })
})
