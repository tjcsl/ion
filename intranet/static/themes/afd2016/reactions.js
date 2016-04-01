$(function() {
    $(".react-button").click(function() {
        var p = $(this).parent();
        var ro = $(".reactions-outer", p);
        var vis = ro.attr("data-visible");

        if(vis == "true") {
            ro.animate({
                "opacity": 0
            }, 200).css({
                "transform": "scale(1, 1) translate(0, 0)",
                "transition": "transform 200ms ease"
            }, 350);
            setTimeout(function() {
                ro.hide();
            }, 500);
            ro.attr("data-visible", false);
        } else {
            ro.show().animate({
                "opacity": 1
            }, 200).css({
                "transform": "scale(.8, .8) translate(0, 0)",
                "transition": "transform 200ms ease"
            }, 250);
            ro.attr("data-visible", true);
        }
    });

    giveReaction = function(icon) {
        var react = icon.attr("data-reaction");
        var outer = icon.parent().parent();
        $.post(outer.attr("data-endpoint"), {"reaction": react}, function(res) {
            location.href = outer.attr("data-view");
        });
    }

    $(".reactions-box .reaction-icon").click(function() {
        var t = $(this);
        t.addClass("click");
        giveReaction(t);
        setTimeout(function() {
            t.removeClass("click");
            t.addClass("click-out");
            setTimeout(function() {
                t.removeClass("click-out");
            }, 200);
        }, 1000);
    })
})