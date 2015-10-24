$(document).ready(function() {
    /* Input */
    var $username = $("input[name=username]");
    var $password = $("input[name=password]");
    if(!$username.hasClass("error") && $password.hasClass("error")) {
        $password.focus();
    } else {
        $username.focus();
    }

    $(".logo").click(function() {
        location.href = (window.osearch ? "/?"+window.osearch.substring(0, window.osearch.length-1) : "/");
    });

    $("#revision").click(function(e) {
        if (e.altKey) {
            location.href = $(this).attr("data-github-url");
        }
    });

    $("input[type=submit]").click(function(e) {
        document.forms["auth_form"].submit();
        $(this).val("  ").prop("disabled", "disabled");
        var spinner = new Spinner(spinnerOptions).spin(document.querySelector(".spinner-container"));
    });

    $(".title h1").dblclick(function() {
        var n = $("span.letter-n", $(this));
        if(n.length == 0) {
            $(this).html("TJ Intra<span class='letter-n'>n</span>et");
            $("body").append("<audio id='tdfw' src='https://www.tjhsst.edu/~2016jwoglom/uploads/tdfw.mp3' preload></audio>");
            $(".title h1 .letter-n").css({"cursor": "pointer"}).click(function() {
                document.querySelector("#tdfw").play();
                $(".logo").addClass("flip180");
                $(this).parent().addClass("scaleflip");
                var e = $("input, .schedule, .footer a");

                var p = $(this).parent().parent();
                var s = $("input[type=submit]");
                p.addClass("bounce");

                setTimeout(function() {
                    e.addClass("pulse");
                    s.removeClass("pulse").addClass("wobble");
                    setTimeout(function() {
                        e.removeClass("pulse");
                        p.removeClass("bounce");
                        s.removeClass("wobble");
                    }, 5000)
                }, 6000);
            });
        }
    });

});