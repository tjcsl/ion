/* global $ */
$(function() {
    window.userHide = {};

    $(".student-attendance-row").hover(function() {
        var uid = $(this).children(".user-link[data-user-id]").attr("data-user-id");

        if (window.userHide.hasOwnProperty(uid)) {
            clearTimeout(window.userHide[uid]);
            window.userHide[uid] = null;
        }

        var img = $("img.user-pic[data-user-id='" + uid + "']");

        img.css({
            left: window.mouseX,
            top: window.mouseY,
        });
        img.addClass("active");
        img.fadeIn(25);

    }, function() {
        var uid = $(this).children(".user-link[data-user-id]").attr("data-user-id");
        window.userHide[uid] = setTimeout(function() {
            $(".user-pic[data-user-id='" + uid + "']").fadeOut(50).removeClass("active");
        }, 50);
    });

    $(document).mousemove(function(e) {
        var posx = window.mouseX = e.pageX,
            posy = window.mouseY = e.pageY;
        posx += 30;
        posy -= 215 - 10;
        $("img.user-pic.active").css({
            left: posx,
            top: posy
        });
    });
})