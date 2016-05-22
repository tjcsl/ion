/* global $ */
$(function() {
    /* Input */
    var $username = $("input[name=username]"),
        $password = $("input[name=password]");

    if (!$username.hasClass("error") && $password.hasClass("error")) {
        $password.focus();
    } else {
        $username.focus();
    }

    $(".logo").click(function() {
        location.href = (window.osearch ? "/?"+window.osearch.substring(0, window.osearch.length-1) : "/");
    });

    $(".git-version").click(function(e) {
        location.href = $(this).attr("data-github-url");
    });

    $("input[type=submit]").click(function(e) {
        if (typeof runEgg === 'function' && runEgg($("#id_username").val())) {
            e.preventDefault();
            return;
        }

        document.forms["auth_form"].submit();
        $(this).addClass("load-spinner").val("  ").prop("disabled", "disabled");
        var spinner = new Spinner(spinnerOptions).spin(document.querySelector(".spinner-container"));
    });

    $(".title h1").dblclick(function() {
        var n = $("span.letter-n", $(this));

        if (n.length === 0) {
            $(this).html("TJ Intra<span class='letter-n'>n</span>et");
            $("body").append("<audio id='tdfw' src='https://www.tjhsst.edu/~2016jwoglom/uploads/tdfw.mp3?1' preload></audio>");
            $(".title h1 .letter-n").css({"cursor": "pointer"}).dblclick(function() {
                document.querySelector("#tdfw").play();
                var e = $("input, .schedule, .footer a");
                var ip = $(this).parent();
                var p = ip.parent();
                var s = $("input[type=submit]");
                p.addClass("bounce");

                setTimeout(function() {
                    $(".logo").addClass("flip180");

                    var i = setInterval(function() {
                        $(".logo").toggleClass("flip180");
                    }, 500);

                    ip.addClass("scaleflip");
                    e.addClass("pulse");
                    s.removeClass("pulse").addClass("wobble");

                    setTimeout(function() {
                        e.removeClass("pulse");
                        p.removeClass("bounce");
                        s.removeClass("wobble");
                        clearInterval(i);
                        $(".logo").removeClass("flip180");
                        ip.removeClass("scaleflip");
                    }, 5000)
                }, 6000);
            });
        }
    });

});
