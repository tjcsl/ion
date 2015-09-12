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

    footerCheck = function() {
        var win = $(window).height();
        var pg = $(document).height();

        if(pg - win > 20) {
            $(".footer").css({
                position: "absolute",
                top: (pg - 20)+"px"
            });
        } else {
            $(".footer").css({
                position: "fixed",
                top: "auto"
            });
        }
    }

    $(window).resize(function() {
        footerCheck();
    });
    footerCheck();

});