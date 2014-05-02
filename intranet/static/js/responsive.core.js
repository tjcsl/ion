$(document).ready(function() {
    /* left menu nav icon */
    $(".left > .dropdown-taparea").click(function() {
        $n = $(".main > .nav").eq(0);
        $g = $(".nav-g");
        if($n.css('left') == "0px") { // hide
            $n.css({ "left": "-202px" });
            $g.removeClass("close-l").hide();
        } else { // show
            $n.css({ "left": "0px" });
            $g.addClass("close-l").show();
        }
    });

    $(".nav-g").click(function() {
        $(this).hide();
        if($(this).hasClass("close-l")) {
            $(".left > .dropdown-taparea").click();
        }
    })
})