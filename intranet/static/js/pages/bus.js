let checkDisplayWarning = function () {
    let now = new Date();
    let hours = now.getHours();
    let minutes = now.getMinutes();
    let departTime = endMinute + 10; // minutes after end of school until buses depart
    let txt = document.querySelector('.text');
    if (hours === endHour && minutes < departTime) {
        let remaining = departTime - minutes;
        txt.innerText = `${remaining} minutes left until buses depart. Have a great day!`;
    } else if (hours < endHour) {
        txt.innerText = 'School has yet to end.';
    } else {
        txt.innerText = 'School buses have already departed';
    }
};

window.setTimeout(checkDisplayWarning, 30 * 1000);
