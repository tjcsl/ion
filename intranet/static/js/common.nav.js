/* global $ */
$(function() {
    $.extend($.expr[":"], {
        horizontallyscrollable: function(element) {
            var e = $(element);
            if (e.css("overflow") == "scroll" || e.css("overflowX") == "scroll" || e.css("overflow") == "auto" || e.css("overflowX") == "auto") {
                return true;
            }
            return false;
        }
    });

    $(".main *:horizontallyscrollable").on("touchstart", function(e) {
        var scrollPos = $(this).scrollLeft();
        if (scrollPos != 0) {
            e.stopPropagation();
        }
    });

    var initX = null, initY = null, listening = false;
    $(window).on("touchstart", function(e) {
        initX = e.originalEvent.touches[0].clientX;
        initY = e.originalEvent.touches[0].clientY;
        listening = true;
    });
    $(window).on("touchend", function(e) {
        listening = false;
    });
    $(window).on("touchmove", function(e) {
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
        if (diffX > 30) {
            var nav = $(".main > .nav").eq(0);
            var g = $(".nav-g");
            // get css left, remove px ending if it exists, and check if 0 (-202px if hidden)
            var shown = nav.css('left').split(/[^\-\d]+/)[0] == 0;
            if (!shown) {
                nav.animate({ left: "0px" }, 200);
                g.addClass("close-l").fadeIn(200);
                $("body").addClass("disable-scroll").addClass("mobile-nav-show");
                $(".c-hamburger").addClass("is-active");
                listening = false;
            }
        } else if (diffX < -30) {
            var nav = $(".main > .nav").eq(0);
            var g = $(".nav-g");
            // get css left, remove px ending if it exists, and check if 0 (-202px if hidden)
            var shown = nav.css('left').split(/[^\-\d]+/)[0] == 0;
            if (shown) {
                nav.animate({ left: "-202px" }, 200);
                g.removeClass("close-l").fadeOut(200);
                $("body").removeClass("disable-scroll").removeClass("mobile-nav-show");
                $(".c-hamburger").removeClass("is-active");
                listening = false;
            }
        }
    });
});
