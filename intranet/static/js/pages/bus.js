let checkDisplayWarning = function () {
    let now = new Date();
    let end_time = new Date(now.getFullYear(), now.getMonth(), now.getDate(), parseInt(endHour), parseInt(endMinute), 0, 0);
    let departure_offset = 10; // minutes after end of school until buses depart
    let departure_time = new Date(end_time.getTime() + departure_offset * 60 * 1000);

    let txt = document.querySelector('.text');
    if(now.getTime() < end_time.getTime()) {
        txt.innerText = 'School has not ended yet.';
    }
    else if(now.getTime() < departure_time.getTime()) {
        let remaining = Math.ceil((departure_time.getTime() - now.getTime()) / (60 * 1000));
        txt.innerText = `${remaining} minute${remaining == 1 ? "" : "s"} left until buses depart. Have a great day!`;
    }
    else {
        txt.innerText = 'School buses have already departed.';
    }
};

window.setInterval(checkDisplayWarning, 10 * 1000);
window.addEventListener("load", checkDisplayWarning);
