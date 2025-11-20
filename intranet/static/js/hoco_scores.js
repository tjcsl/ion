$(document).ready(function() {
    let hocoScoresRef;  // stores a reference to the scores div when disconnected
    let numDisconnected = 0;
    let didConnect = false;  // whether we've successfully connected at least once
    function loadScores() {
        $.get("https://homecoming.tjhsst.edu/api/", function(data) {
            didConnect = true;
            if (hocoScoresRef) {  // on reconnect
                $("#hoco-scores").replaceWith(hocoScoresRef).fadeTo("slow", 1);  // restore the backup
                hocoScoresRef = null;
            }
            $("#score-senior").text(data.senior_total ? data.senior_total : 0);
            $("#score-sophomore").text(data.sophomore_total ? data.sophomore_total : 0);
            $("#score-junior").text(data.junior_total ? data.junior_total : 0);
            $("#score-freshman").text(data.freshman_total ? data.freshman_total : 0);
            removeRibbons();
            giveRibbons();
            $("#hoco-scores").delay(1500).fadeTo("slow", 1);
        }).fail(function() {
            if (didConnect) {  // only track failed attempts after first successful attempt
                numDisconnected += 1;
                if (numDisconnected < 5) {
                    return;  // don't hide yet
                }
            }
            if (!hocoScoresRef) {  // on disconnect, after 5 failed attempts
                hocoScoresRef = $("#hoco-scores").clone().hide();  // save a hidden backup
                $("#hoco-scores").fadeOut(function() {
                    $(this).empty();  // keep the div but remove its contents
                });
            }
        });
    }
    window.setInterval(loadScores, 5 * 60 * 1000);  // every 5 minutes
    loadScores();
});
function giveRibbons() {
    var arr = [];
    $("#hoco-scores .box").each(function() {
        var score = parseFloat($(this).find(".score").text());
        arr.push([$(this), score]);
    });
    arr.sort(function(a, b) {
        return b[1] - a[1];
    });
    var place = 0;
    $.each(arr, function(k, v) {
        if (k > 0 && arr[k - 1][1] != v[1]) {
            place += 1;
        }
        if (place == 0) {
            v[0].find(".corner-ribbon").addClass("gold").text("1st");
        }
        else if (place == 1) {
            v[0].find(".corner-ribbon").addClass("silver").text("2nd");
        }
        else if (place == 2) {
            v[0].find(".corner-ribbon").addClass("bronze").text("3rd");
        }
    });
}

function removeRibbons() {
    $("#hoco-scores .corner-ribbon").removeClass("gold silver bronze").text("");
}
