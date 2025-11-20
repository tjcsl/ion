import { getSocket } from "./bus-shared.js";

$(function() {
    let base_url = window.location.host;
    let socket = getSocket(base_url, location, document, window, "morning");

    $("#a-button").click(function() {sendMorningUpdate({"status":"a"}, socket); });
    $("#o-button").click(function() {sendMorningUpdate({"status":"o"}, socket); });
    $("#d-button").click(function() {sendMorningUpdate({"status":"d"}, socket); });

    $("select").selectize({
        create: false,
        sortField: "text"
    });

    if(isAdmin) {
        $(".bus-announcement-save").click(function() {
            sendMorningUpdate({
                announcement: $(".bus-announcement").text()
            }, socket);
            $(".bus-announcement-save").text("Saved!").css("color", "green");
            setTimeout(function() {
                $(".bus-announcement-save").text("Save").css("color", "");
            }, 1500);
        });
        $(".bus-announcement-clear").click(function() {
            $(".bus-announcement").text("");
            sendMorningUpdate({
                announcement: "",
            }, socket);
            $(".bus-announcement-clear").text("Cleared!").css("color", "green");
            setTimeout(function() {
                $(".bus-announcement-clear").text("Clear").css("color", "");
            }, 1500);
        });
    }
});

function sendMorningUpdate(data, socket) {
    data.id = document.getElementById("buses").value;
    data.time = "morning";
    socket.send(JSON.stringify(data));
}
