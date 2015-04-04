$(document).ready(function() {
    is_small = function() {
        return $("#activity-detail").css("right").split(/[^\-\d]+/)[0] < 0;;
    }

    $("#activity-list li[data-activity-id]").click(function() {
        if(is_small()) {
            $("#activity-detail").addClass("visible");
            setTimeout(function() {
                $("#activity-list").addClass("hidden");
            }, 100);
        }
    })

    $("#activity-list .backbtn").click(function() {
        $("#activity-detail").removeClass("visible");
        $("#activity-list").removeClass("hidden");
        $("#activity-list li[data-activity-id]").removeClass("selected");
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
