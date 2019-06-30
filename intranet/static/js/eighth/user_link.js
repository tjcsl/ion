/* global $ */
$(function() {
    window.userImgs = [];
    window.userHide = {};
    // window.defaultPic = "data:image/png;base64,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";
    /*$(".user-link").each(function() {
        var uid = $(this).attr("data-user-id");
        var i = new Image();
        i.src = "/profile/picture/" + uid;
        console.debug("PRELOAD", uid);
        userImgs.push(i);
    });*/

    $("body").append("<div class='user-pic-container'></div>");

    $(".user-link[data-user-id]").hover(function() {
        var uid = $(this).attr("data-user-id");

        if (window.userHide.hasOwnProperty(uid)) {
            clearTimeout(window.userHide[uid]);
            window.userHide[uid] = null;
        }

        var img = $("img.user-pic[data-user-id='" + uid + "']");

        if (img.length > 0) {
            img.fadeIn(100);
            img.addClass("active");
            console.debug(uid, "IN");
        } else {
            console.debug(uid, "LOAD");
            var img = $("<img class='user-pic'>");
            img.attr("data-user-id", uid);
            img.attr("src", "/profile/picture/" + uid);
            img.attr("width", 172);
            img.attr("height", 215);
            img.css({
                position: "absolute",
                left: window.mouseX,
                top: window.mouseY,
                border: "2px solid black",
                backgroundColor: 'rgb(57, 105, 146)',
                backgroundClip: "content-box",
                backgroundSize: "172px 215px",
                backgroundRepeat: "no-repeat",
                zIndex: 9001
            });
            img.addClass("active");
            img.fadeIn(100);
            $(".user-pic-container").append(img);
        }

    }, function() {
        var uid = $(this).attr("data-user-id");
        window.userHide[uid] = setTimeout(function() {
            console.debug(uid, "OUT");
            $(".user-pic[data-user-id='" + uid + "']").fadeOut(100).removeClass("active");
        }, 350);
    });

    $(document).mousemove(function(e) {
        var posx = window.mouseX = e.pageX,
            posy = window.mouseY = e.pageY;
        posx += 75;
        posy -= 215 - 10;
        $("img.user-pic.active").css({
            left: posx,
            top: posy
        });
    });
})