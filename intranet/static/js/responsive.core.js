$(document).ready(function() {
    /* left menu nav icon */
    $(".left > .dropdown-taparea").click(function() {
        $n = $(".main > .nav");
        $n.css({
            "left": ($n.css('left') == '0px' ? '-202px': '0px')
        });
    })
})