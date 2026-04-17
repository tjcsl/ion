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

    // turnstile is disabled if the input type is hidden
    if ($("#id_turnstile").attr("type") !== "hidden") {
        var $btn = $("input[type=submit]");
        $btn.data("orig-val", $btn.val()); // "Login"
        $btn.val("Validating CAPTCHA...");
        $("input[type=submit]").attr("disabled", "disabled");
    }
  
    $(".warning-announcement, .login-warning").on("click", function(e) {
        $(this).toggleClass('collapsed');
    });

    $(".sidebar-trigger").on("click", function() {
        if($(".sidebar").hasClass("has-events")){
            if($(this).css("left") !== "5px") {
                $(this).html("<i class=\"far fa-fw fa-calendar-alt\"></i>");
                $(this).css("left", "5px");
            }
            else {
                $(this).html("<i class=\"fas fa-fw fa-times\"></i>");
                $(this).css("left", "267px");
            }
            $(".sidebar").toggle("slide");
            $(".center-wrapper").toggleClass("disable-interaction");
        }
    });

    $(window).on("resize", function() {
        if($(".sidebar").hasClass("has-events")){
            if($(this).width() > 800) {
                $(".center-wrapper").removeClass("disable-interaction");
                $(".sidebar").show("slide");
            }
            else {
                $(".sidebar").hide("slide");
                $(".sidebar-trigger").css("left", "5px");
                $(".sidebar-trigger").html("<i class=\"far fa-fw fa-calendar-alt\"></i>");
            }
        }
    });

    $(".logo").on("click", function() {
        location.href = (window.osearch ? "/?" + window.osearch.substring(0, window.osearch.length - 1) : "/");
    });

    $(".git-version").on("click", function(e) {
        location.href = $(this).attr("data-github-url");
    });

    $("input[type=submit]").on("click", function(e) {
        if (typeof runEgg === 'function' && runEgg($("#id_username").val())) {
            e.preventDefault();
            return;
        }

        if(!($("#id_username").val() && $("#id_password").val())) {
            return;
        }

        document.forms["auth_form"].submit();
        $(this).addClass("load-spinner").val("  ").prop("disabled", true);
        var spinner = new Spinner(spinnerOptions).spin(document.querySelector(".spinner-container"));
    });

    $(".title h1").dblclick(function() {
        var n = $("span.letter-n", $(this));

        if (n.length === 0) {
            $(this).html("TJ Intra<span class='letter-n'>n</span>et");
            $("body").append("<audio id='tdfw' src='https://ion.tjhsst.edu/uploads/tdfw.mp3?1' preload></audio>");
            $(".title h1 .letter-n").css({
                "cursor": "pointer"
            }).dblclick(function() {
                document.querySelector("#tdfw").play();
                var e = $("input, .schedule, .footer a, .events-outer");
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

    function doneTyping () {
        // stop warnings from showing if the username is empty

        // already populated
        if ($("#username-warning").text().indexOf("CAPTCHA") === -1) {
            return;
        }

        if (!$("#id_username").val()) {
            $("#username-warning").text("");
            return;
        }

        let re = /^(\d{4})?[a-zA-Z]+\d?$/;
        if (re.exec($("#id_username").val()) == null) {
            $("#username-warning").text("Username must be in the format 2016jwoglom for students or jbwoglom for staff.");
        } else {
            $("#username-warning").text("");
        }
    }

    var typingTimer;
    $("#id_username").on("keyup", function () {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(doneTyping, 2000);
    });

    $(".warning-content").hide();
    $(".warning-toggle-icon").removeClass("fa-chevron-up").addClass("fa-chevron-down");

});

function onSuccess(_) {
    var $btn = $("input[type=submit]");
    $btn.removeAttr("disabled").val($btn.data("orig-val"));
    // reset text and clear warning to allow for other warnings to show
    $("#username-warning").text("");
}

function onExpired() {
    $("input[type=submit]")
        .attr("disabled", "disabled")
        .val("Expired - Reload Page");
    $("#username-warning").text("CAPTCHA expired. Please reload the page.");
}

function onError() {
    $("input[type=submit]")
        .attr("disabled", "disabled")
        .val("Error - Reload Page");
    $("#username-warning").text("CAPTCHA failed. Please check your connection or disable adblockers.");
}

function onUnsupported() {
    $("input[type=submit]")
        .attr("disabled", "disabled")
        .val("Unsupported - Reload Page");
    $("#username-warning").text("Browser does not support CAPTCHA. Please check your connection or disable adblockers.");
}
