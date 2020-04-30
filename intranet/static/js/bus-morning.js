import { getSocket } from "./bus-shared.js";

$(function() {
    let base_url = window.location.host;
    let socket = getSocket(base_url, location, document, window, 'morning');

    $("#a-button").click(function() {sendMorningUpdate({"status":"a"}, socket); });
    $("#o-button").click(function() {sendMorningUpdate({"status":"o"}, socket); });
    $("#d-button").click(function() {sendMorningUpdate({"status":"d"}, socket); });
});

function sendMorningUpdate(data, socket) {
    data.id = document.getElementById("buses").value;
    data.time = "morning";
    socket.send(JSON.stringify(data));
}
