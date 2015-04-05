$(document).ready(function() {
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
    })
})
