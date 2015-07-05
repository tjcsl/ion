$(function() {
    window.userImgs = [];
    window.userHide = {};
    $(".user-link").each(function() {
        var uid = $(this).attr("data-user-id");
        var i = new Image();
        i.src = "/profile/picture/" + uid;
        console.debug("PRELOAD", uid);
        userImgs.push(i);
    });

    $(".user-link").hover(function() {
        var uid = $(this).attr("data-user-id");
        if(userHide.hasOwnProperty(uid)) {
            clearTimeout(userHide[uid]);
        }
        console.debug(uid, "IN");
        var img = $("img.user-pic[data-user-id='" + uid + "']");

        if(img.length > 0) {
            img.show();
        } else {
            var img = $("<img class='user-pic' />");
            img.attr("data-user-id", uid);
            img.attr("src", "/profile/picture/" + uid);
            img.css({
                position: "absolute",
                left: window.mouseX,
                top: window.mouseY
            });
            $("body").append(img);
        }

    }, function() {
        var uid = $(this).attr("data-user-id");
        userHide[uid] = setTimeout(function() {
            console.debug(uid, "OUT");
            $(".user-pic[data-user-id='" + uid + "']").fadeOut(100);
        }, 200);
    });

    $(document).mousemove(function(e){
        window.mouseX = e.pageX;
        window.mouseY = e.pageY;
        $("img.user-pic").css({left: e.pageX, top: e.pageY});
    });
})