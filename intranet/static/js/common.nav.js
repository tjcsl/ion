/* global $ */
$(function() {
    $.extend($.expr[":"], {
        horizontallyscrollable(element) {
            var e = $(element);
            return (e.css("overflow") === "scroll" || e.css("overflowX") === "scroll" || e.css("overflow") === "auto" || e.css("overflowX") === "auto");
        }
    });

    $(".main *:horizontallyscrollable").on("touchstart", function(e) {
        var scrollPos = $(this).scrollLeft();
        if (scrollPos !== 0) {
            e.stopPropagation();
        }
    });

    var initX = null,
        initY = null,
        listening = false;

    $(window).on({
        "touchstart": function(e) {
            initX = e.originalEvent.touches[0].clientX;
            initY = e.originalEvent.touches[0].clientY;
            listening = true;
        },
        "touchend": function(e) {
            listening = false;
        },
        "touchmove": function(e) {
            if (!listening) return;

            var nowX = e.originalEvent.touches[0].clientX,
                nowY = e.originalEvent.touches[0].clientY;

            if (Math.abs(nowY - initY) > 30) {
                listening = false;
                return;
            }

            var diffX = nowX - initX;
            var nav, g, shown;

            if (Math.abs(diffX) > 30) {
                nav = $(".main > .nav").eq(0);
                g = $(".nav-g");
                shown = nav.css("left").split(/[^\-\d]+/)[0] === "0";

                if (diffX > 0 && !shown) {
                    nav.animate({
                        left: "0"
                    }, 200);
                    g.addClass("close-l").fadeIn(200);
                    $("body").addClass("disable-scroll").addClass("mobile-nav-show");
                    $(".c-hamburger").addClass("is-active");
                    listening = false;
                } else if (diffX < 0 && shown) {
                    nav.animate({
                        left: "-202px"
                    }, 200);
                    g.removeClass("close-l").fadeOut(200);
                    $("body").removeClass("disable-scroll").removeClass("mobile-nav-show");
                    $(".c-hamburger").removeClass("is-active");
                    listening = false;
                }
            }
        }
    });
});