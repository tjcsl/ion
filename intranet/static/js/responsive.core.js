$(document).ready(function() {
    /* left menu nav icon */
    $(".left > .dropdown-taparea").click(function() {
        $n = $(".main > .nav").eq(0);
        $g = $(".nav-g");
        if($n.css('left') == "0px") { // hide
            $n.animate({ left: "-202px" }, 200);
            $g.removeClass("close-l").fadeOut(200);
            $("body").removeClass("disable-scroll");
        } else { // show
            $n.animate({ left: "0px" }, 200);
            $g.addClass("close-l").fadeIn(200);
            $("body").addClass("disable-scroll");
        }
    });

    $(".nav-g").click(function() {
        $(this).fadeOut(200);
        if($(this).hasClass("close-l")) {
            $(".left > .dropdown-taparea").click();
        }
    })
})
