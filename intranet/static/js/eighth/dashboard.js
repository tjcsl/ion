$(document).ready(function() {
    var heights = $(".eighth-activities").map(function() {
        return $(this).children(".eighth-activity").length * 20;
    }).get();

    var max_height = Math.max.apply(null, heights);
    if (max_height > 90) {
        max_height = 90;
    }

    $(".eighth-widget").data("max-height", max_height);

    $(".block-header").bind( "touchstart", function(e){e.click()} );
    $(".block-header").click(function() {
        var time = 200;
        var opened = $(".eighth-block.open .eighth-activities");
        opened.stop().animate({height: 0}, time);
        opened.parent().removeClass("open");

        var block = $(this).parent();
        var height = $(".eighth-widget").data("max-height");
        block.children(".eighth-activities").stop().animate({height: height}, time);
        block.addClass("open");
    });

    $(".eighth-activity").click(function() {
        var time = 300;
        $(this).stop().animate({ backgroundColor: "rgb(78,185,0)" }, time, function() {
            $(this).stop().delay(500).animate({ backgroundColor: "rgb(220,220,220)" }, time, function() {
                $(this).removeAttr("style");
            })
        });

        var icon = $(this).children("i");
        icon.stop().animate({ color: "rgb(72,72,72)" }, time, function() {
            icon.stop().delay(500).animate({ color: "rgb(78,185,0)" }, time, function() {
                // icon.removeAttr("style");
            })
        });
    });
});