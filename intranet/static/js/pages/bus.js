let checkDisplayWarning = function () {
    let now = new Date();
    let end_time = new Date(now.getFullYear(), now.getMonth(), now.getDate(), parseInt(endHour), parseInt(endMinute), 0, 0);
    let departure_offset = 10; // minutes after end of school until buses depart
    let departure_time = new Date(end_time.getTime() + departure_offset * 60 * 1000);

    let txt = document.querySelector('.text');
    if(now.getTime() < end_time.getTime()) {
        txt.innerHTML = '<i class="fas fa-clock"></i> School is in session.';
        txt.classList.add("blue");

        txt.classList.remove("red");
        txt.classList.remove("green");
        txt.classList.remove("orange");
        txt.classList.remove("dark-red");
    }
    else if(now.getTime() < departure_time.getTime()) {
        let remaining = Math.ceil((departure_time.getTime() - now.getTime()) / (60 * 1000));

        if(remaining <= 2) {
            txt.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Buses depart in ${remaining} minute${remaining === 1 ? "" : "s"}.`;
            txt.classList.add("dark-red");

            txt.classList.remove("green");
            txt.classList.remove("orange");
        }
        else if(remaining <= 5) {
            txt.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Buses depart in ${remaining} minute${remaining === 1 ? "" : "s"}.`;
            txt.classList.add("orange");

            txt.classList.remove("dark-red");
            txt.classList.remove("green");
        }
        else {
            txt.innerHTML = `<i class="fas fa-exclamation-circle"></i> Buses depart in ${remaining} minute${remaining === 1 ? "" : "s"}.`;
            txt.classList.add("green");

            txt.classList.remove("dark-red");
            txt.classList.remove("orange");
        }

        txt.classList.remove("blue");
        txt.classList.remove("red");
    }
    else {
        let remaining = Math.ceil((departure_time.getTime() - now.getTime()) / (60 * 1000));

        if(remaining > -10) {
            txt.innerHTML = "<i class='fas fa-exclamation-triangle'></i> Buses have departed.";
            txt.classList.add("red");
            txt.classList.remove("blue");
        }
        else {
            txt.innerHTML = "<i class='fas fa-info-circle'></i> School has ended.";
            txt.classList.add("blue");
            txt.classList.remove("red");
        }

        txt.classList.remove("dark-red");
        txt.classList.remove("green");
        txt.classList.remove("orange");
    }
};

window.setInterval(checkDisplayWarning, 10 * 1000);
window.addEventListener("load", checkDisplayWarning);
