/* global $ */
function toggleNavbar() {
    $n = $(".main > .nav").eq(0);
    $g = $(".nav-g");
    // get css left, remove px ending if it exists, and check if 0 (-202px if hidden)
    if ($n.css('left').split(/[^\-\d]+/)[0] === "0") { // hide
        $n.animate({
            left: "-202px"
        }, 200);
        $g.removeClass("close-l").fadeOut(200);
        $("body").removeClass("disable-scroll").removeClass("mobile-nav-show");
        $(".c-hamburger").removeClass("is-active");
    } else { // show
        $n.animate({
            left: "0"
        }, 200);
        $g.addClass("close-l").fadeIn(200);
        $("body").addClass("disable-scroll").addClass("mobile-nav-show");
        $(".c-hamburger").addClass("is-active");
    }
}

$(function() {
    /* left menu nav icon */
    $(".left > .dropdown-taparea").click(toggleNavbar);

    $(".nav-g").click(function() {
        $(this).fadeOut(200);
        if ($(this).hasClass("close-l")) {
            $(".left > .dropdown-taparea").click();
        }
    });
});
