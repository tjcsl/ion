$(document).ready(function() {
    function scroll() {
        $("body, #welcome-container").animate({ scrollTop: 0 }, 500);
    }

    var tm = 250;

    $("#ion-welcome-continue").click(function(e) {
        e.preventDefault();
        $("#ion-welcome").slideUp(tm);
        $("#step-1").slideDown(tm);
        scroll();
    });

    $(".continue-step-1-mail").click(function() {
        $("#step-1").slideUp(tm);
        $("#mail-forwarding").slideDown(tm);
        scroll();
    });

    $(".continue-step-1-policy").click(function() {
        $("#mail-forwarding").slideUp(tm);
        $("#eighth-policy").slideDown(tm);
        scroll();
    });

    $(".continue-step-1").click(function() {
        $("#step-1").slideUp(tm);
        $("#step-2").slideDown(tm);
        scroll();
    });

    $("#eighth-policy-next").click(function(e) {
        e.preventDefault();
        $("#eighth-policy").slideUp(tm);
        $("#step-2").slideDown(tm);
        scroll();
    });

    $(".continue-step-2").click(function() {
        $("#step-2").slideUp(tm);
        $("#step-3").slideDown(tm);
        scroll();
    });
});
