/* Iodine (Intranet2) Snow Script
 * Credits: dmorris, zyaro
 * Modified for Ion (Intranet3) by: 2016jwoglom, 2025azhu
 */
$(function () {
    $("head").first().append("<script nomodule src='/static/js/vendor/js.cookie.min.js'></script>");
    let enabled = Cookies.get("disable-theme") == "1" ? false : true;

    if (enabled) {
        // Snow streak - How many days in a row the user has seen the theme. Controls size and speed of snow.
        let dayStreak = Cookies.get("dayStreak");
        if (dayStreak == null) {
            Cookies.set("dayStreak", 1, { expires: 5 * 7 });
            dayStreak = 1;
        }

        let day = new Date().getDate();
        let prevDay = Cookies.get("prevDay");
        if (prevDay == null) {
            Cookies.set("prevDay", day, { expires: 5 * 7 });
            prevDay = day;
        }
        if (prevDay < day) {
            Cookies.set("dayStreak", parseInt(dayStreak) + 1, { expires: 5 * 7 });
            dayStreak = parseInt(dayStreak) + 1;
            Cookies.set("prevDay", day, { expires: 5 * 7 });
        }

        // Option to disable theme
        $(".header > .right > ul").prepend(`
            <div class="snow-info-container" style="display: inline;">
                <p class="snow-nav-append streak-info" style="display: inline">
                    Snow streak: ${dayStreak}
                    <i title="Snow streak controls the size and speed of the snow. Each day you login to Ion, your snow streak will increase by 1. Click for more info."
                        class="snow-streak-info fas fa-info-circle"
                        onclick="alert('About Snow Streak:\\n❆ Snow streak controls how large the snowflakes are and how fast the snow falls.\\n❆ Each day you login to Ion increases your snow streak by 1.\\n❆ Disabling the snow theme resets your snow streak.\\n❆ If the snow is too fast, you can decrease your snow streak by clicking the down arrow next to your snow streak (if your snow streak is greater than 1).')">
                    </i>
                    <i class="decrease-snow-streak fas fa-long-arrow-alt-down"
                        title="Decrease snow streak by 1"
                        onclick="handleDecreaseSnowStreak()">
                    </i>
                    &nbsp;&nbsp;
                </p>
                <a class='disable-snow snow-nav-append toggle-theme btn-link'
                    onclick='if(confirm("Are you sure you want to disable the winter theme? Your snow streak will be reset.")) toggleTheme();'>
                    ❄ Turn Off Winter Theme
                </a>
            </div>
        `);

        if(dayStreak <= 1) {
            $(".decrease-snow-streak").hide();
        }

        // if screen size is less than 1000 px
        if (window.innerWidth < 1000) {
            $(".snow-info-container").hide();
            let navbar = $("ul.nav");
            $(navbar).append($(`
                <li>
                    <a class='disable-snow'
                        onclick='if(confirm("Are you sure you want to disable the winter theme? Your snow streak will be reset.")) toggleTheme();'>
                            <i class="far fa-snowflake snow-nav-icon"></i>
                            <span class="nav-toggle-snow-text">
                                Turn Off <br>
                                Winter Theme
                            </span>
                    </a>
                </li>
            `));
            $(navbar).append($(`
                <li>
                    <a>
                    <i class="far fa-snowflake snow-nav-icon"></i>
                    <span class="nav-toggle-snow-text">
                        Snow streak: ${dayStreak}
                    </span>
                    <i title="Snow streak controls the size and speed of the snow. Each day you login to Ion, your snow streak will increase by 1. Click for more info."
                        class="snow-nav-info-icon-1 snow-streak-info fas fa-info-circle"
                        onclick="alert('About Snow Streak:\\n❆ Snow streak controls how large the snowflakes are and how fast the snow falls.\\n❆ Each day you login to Ion increases your snow streak by 1.\\n❆ Disabling the snow theme resets your snow streak.\\n❆ If the snow is too fast, you can decrease your snow streak by clicking the down arrow next to your snow streak.')">
                    </i>
                    <i title="Decrease snow streak by 1"
                        class="snow-nav-info-icon-2 decrease-snow-streak fas fa-long-arrow-alt-down"
                        onclick="handleDecreaseSnowStreak()">
                    </i>
                    </a>
                </li>
            `));

            if(dayStreak <= 1) {
                $(".decrease-snow-streak").hide();
            }
        }


        /*************************** Snow **************************/
        var snowroot = "/static/themes/snow/";
        var ie = (navigator.appName === 'Microsoft Internet Explorer');
        var android = (navigator.userAgent.toLowerCase().indexOf("android") !== -1);
        var mobile = android;
        var fastbrowser = !ie;

        //Config
        //Number of flakes

        if (typeof snowmax === "undefined") {
            var snowmax = mobile ? 15 : 100;
        }

        if (!window.requestAnimationFrame) {
            window.requestAnimationFrame = function (f) {
                return f();
            }
        }

        //Colors possible for flakes
        var snowcolor = ["#aac", "#ddF", "#ccD"];
        //Number of snowflake characters in following array
        var numsnowletters = 3;
        //Fonts possible for flakes
        var snowtype = ["Arial Black", "Arial Narrow", "Times", "Comic Sans MS"];

        //Character to be used for flakes
        if (typeof snowletter === "undefined") {
            //IE doesnt' like it for some reason
            var snowletter = ie ? "*" : ["❄", "❅", "❆"];
        }

        //Speed multiplier for the snow falling
        if (typeof sinkspeed === "undefined") {
            //They have more elements and do piling. This increases the amount of time it takes for significant slowdown.
            var sinkspeed = fastbrowser ? dayStreak / 6 : 0.5;
        }

        if (typeof snowmaxsize === "undefined" || typeof snowminsize === "undefined") {
            //Maximum size of snowflakes
            var snowmaxsize = mobile ? 44 : 20 + 2*parseInt(dayStreak);
            //Miniumum size of snowflakes
            var snowminsize = mobile ? 16 : 8;
        }

        if (typeof snowfps === "undefined") {
            snowfps = 60;
        }

        //Should the snow pile up?
        //Use real piling in faster browsers
        var pile = fastbrowser;
        //Should we use fast piling?
        var fastpile = !fastbrowser;

        //IE cannot do canvas
        fastpile = fastpile && !ie;
        //Resolution of snow depth data
        var heightbuckets = 200;
        //End Config


        //Range of snow flake sizes
        var snowsizerange = snowmaxsize - snowminsize;
        //Array for snowflakes
        var snowflakes = [];
        //Array of snow flake y coordinates
        var snowy = [];

        //Screen width (set to default)
        var screenwidth = 1000;
        //Screen height (set to default)
        var screenheight = 1000;
        //Real Screen width
        var realscreenwidth;
        //Real Screen height
        var realscreenheight;

        //The array of the depths of the snow
        var snowheight = [];
        //The height of the fast fill snow
        var fastfillheight;
        //Graphics control
        var graphics;
        //The multiplier to find the correct bucket
        var heightacc = heightbuckets / screenwidth;
        //Temporary variables
        var newx, bucket, snowsize;
        //Div holding everything, removes scroll bars.
        var container;

        var today = new Date(); // what day is it?

        //Non-denominational Red Deer-Pulled Guy
        //Do not show Red Deer-Pulled Guy after the 25th
        //It's true! I've met him. He's a pretty cool guy.
        var santaexists = (today.getMonth() === 11 && today.getDate() <= 25);
        var santalink = snowroot + "santa_xsnow.gif";
        var santawidth = 210;
        var santaheight = 83;
        var santaspeed = 5;
        var santax = -santawidth;
        var santa;

        function set_urlvars() {
            var regex = /[\?&]flake=([^&#]*)/;
            var results = regex.exec(window.location.href);

            if (results !== null)
                snowletter = urlDecode(results[1]);

            regex = /[\?&]colors=([^&#]*)/;
            results = regex.exec(window.location.href);

            if (results !== null)
                snowcolor = extract_color(urlDecode(results[1]));
        }

        function urlDecode(utftext) {
            /*
             * Credit for the base for this function
             * goes to the people at webtoolkit
             * http://www.webtoolkit.info/javascript_url_decode_encode.html
             * Pretty cool code, imho.
             */
            utftext = unescape(utftext);
            var string = "";
            var i = 0;
            var c = 0,
                c1 = 0,
                c2 = 0;

            while (i < utftext.length) {
                c = utftext.charCodeAt(i);
                if (c < 128) {
                    string += String.fromCharCode(c);
                } else if ((224 > c) && (c > 191)) {
                    c2 = utftext.charCodeAt(++i);
                    string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                } else {
                    c2 = utftext.charCodeAt(++i);
                    c3 = utftext.charCodeAt(++i);
                    string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                }
                i++;
            }

            //return escape(string)
            return string.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        function extract_color(urlstr) {
            var hex = "0123456789abcdef";
            var ranges = urlstr.split(',');

            ranges = ranges.map(function (el) {
                return el.split(':');
            });

            var outarr = [];
            var r, c, pos, j;

            for (var i = 0; i < 500 * ranges.length; i++) {
                r = ranges[Math.floor(Math.random() * ranges.length)];
                if (!r[1]) {
                    outarr.push('#' + r[0]);
                    continue;
                }

                c = '';
                pos = Math.random();
                for (j = 0; j < r[0].length; j++) {
                    var a = parseInt(r[0][j], 16),
                        b = parseInt(r[1][j], 16);
                    c += hex[(Math.floor(pos * a + (1.0 - pos) * b))];
                }

                outarr.push('#' + c);
            }

            return outarr;
        }

        function resize() {
            //realscreenwidth = document.all ? document.documentElement.clientWidth : window.innerWidth;
            realscreenwidth = $(window).width();
            //realscreenheight = document.all ? document.documentElement.clientHeight : window.innerHeight;
            realscreenheight = $(window).height();
            screenwidth = realscreenwidth - 40;
            screenheight = realscreenheight - (pile ? 5 : 37);

            if (pile) heightacc = heightbuckets / screenwidth;
            if (fastpile) fastfillheight = 150;
        }

        window.onresize = resize;
        resize();

        function initsnow() {
            set_urlvars();

            /*if (document.body.classList) {
            document.body.classList.add("has-snow");
            } else {
            document.body.className += " has-snow";
            }*/
            $(document.body).addClass("has-snow");

            container = document.createElement("div");
            container.id = "snowcontainer";
            container.style.position = "fixed";
            container.style.top = "0";
            container.style.left = "0";
            container.style.width = "100%";
            container.style.height = "100%";
            container.style.overflow = "hidden";
            container.style.zIndex = "-1";
            document.body.appendChild(container);

            if (santaexists) {
                santa = document.createElement("img");
                santa.src = santalink;
                santa.style.position = "absolute";
                santa.style.top = Math.floor(Math.random() * screenheight - santaheight) + "px";
                santa.style.zIndex = "-1";
                container.appendChild(santa);
            }

            if (pile) {
                for (var i = 0; i < heightbuckets; i++) {
                    snowheight[i] = screenheight;
                }
            }

            if (fastpile) {
                if (!ie) {
                    var background = document.createElement("canvas");
                    background.style.position = "absolute";
                    background.style.left = "0";
                    background.style.top = "0";
                    background.style.width = realscreenwidth + "px";
                    background.style.height = realscreenheight + "px";
                    background.style.zIndex = "-1";
                    graphics = background.getContext("2d");
                    document.body.appendChild(background);
                    graphics.lineWidth = 2;
                    graphics.strokeStyle = 'white';
                }
            }

            for (var i = 0; i <= snowmax; i++) {
                snowflakes[i] = document.createElement("span");
                //snowflakes[i].id = "flake_" + i;

                if (snowletter instanceof Array) {
                    snowflakes[i].innerHTML = snowletter[Math.floor(Math.random() * numsnowletters)];
                } else {
                    snowflakes[i].innerHTML = snowletter;
                }

                snowflakes[i].style.color = snowcolor[Math.floor(Math.random() * snowcolor.length)];
                snowflakes[i].style.fontFamily = snowtype[Math.floor(Math.random() * snowtype.length)];
                snowsize = Math.floor(Math.random() * snowsizerange) + snowminsize;

                snowflakes[i].size = snowsize;
                if (pile) snowflakes[i].size -= 5;

                snowflakes[i].style.fontSize = snowsize + "pt";
                //console.log(snowflakes[i].style.fontSize);
                snowflakes[i].style.position = "absolute";
                snowflakes[i].x = Math.floor(Math.random() * screenwidth);
                snowy[i] = Math.floor(Math.random() * screenheight);
                snowflakes[i].style.left = snowflakes[i].x + "px";
                snowflakes[i].style.top = snowy[i] + "px";
                snowflakes[i].fall = sinkspeed * snowsize / 5;
                snowflakes[i].style.zIndex = "-2";
                container.appendChild(snowflakes[i]);
            }

            if (pile) {
                window.requestAnimationFrame(movesnow_pile)
                //setTimeout("movesnow_pile()", 30);
            }
            else if (fastpile) {
                window.requestAnimationFrame(movesnow_fastpile);
                //setTimeout("movesnow_fastpile()", 30);
            }
            else {
                window.requestAnimationFrame(movesnow_nopile);
                //setTimeout("movesnow_nopile()", 30);
            }
        }

        function movesnow_pile() {
            if (santaexists) {
                santax += santaspeed;
                if (santax >= screenwidth + santawidth) {
                    santax = -santawidth;
                    santa.style.top = Math.floor(Math.random() * screenheight - santaheight) + "px";
                }
                santa.style.left = santax + "px";
            }

            dayStreakMultiplier = dayStreak * 10;
            for (var i = 0; i <= snowmax; i++) {
                snowy[i] += snowflakes[i].fall;

                snowflakes[i].style.top = snowy[i] + "px";
                newx = snowflakes[i].x + 10 * Math.sin(snowy[i] / dayStreakMultiplier);
                snowflakes[i].style.left = newx + "px";
                bucket = Math.floor(heightacc * (newx + (snowflakes[i].size / 2)));

                if (snowy[i] + snowflakes[i].size > snowheight[bucket]) {
                    var tempsnowletter = snowflakes[i].innerHTML;

                    if ((snowheight[bucket + 1] - snowheight[bucket] < 5 && snowheight[bucket - 1] - snowheight[bucket] < 5) || snowy[i] >= screenheight) {
                        snowheight[bucket] = (snowy[i] < snowheight[bucket]) ? snowy[i] : snowheight[bucket];
                        snowflakes[i] = document.createElement("span");
                        snowflakes[i].innerHTML = tempsnowletter;
                        snowflakes[i].style.color = snowcolor[Math.floor(Math.random() * snowcolor.length)];
                        snowflakes[i].style.fontFamily = snowtype[Math.floor(Math.random() * snowtype.length)];
                        snowsize = Math.floor(Math.random() * snowsizerange) + snowminsize;
                        snowflakes[i].size = snowsize - 5;
                        snowflakes[i].style.fontSize = snowsize + "pt";
                        snowflakes[i].style.position = "absolute";
                        snowflakes[i].x = Math.floor(Math.random() * screenwidth);
                        snowy[i] = -snowflakes[i].size;
                        snowflakes[i].style.left = snowflakes[i].x + "px";
                        snowflakes[i].style.top = snowy[i] + "px";
                        snowflakes[i].fall = sinkspeed * snowsize / 5;
                        snowflakes[i].style.zIndex = "-1";
                        container.appendChild(snowflakes[i]);
                    }
                }
            }

            setTimeout(function () {
                window.requestAnimationFrame(movesnow_pile);
            }, 1000 / snowfps);
            //setTimeout("movesnow_pile()", 60);
        }

        function movesnow_nopile() {
            if (santaexists) {
                santax += santaspeed;
                if (santax >= screenwidth + santawidth) {
                    santax = -santawidth;
                    santa.style.top = Math.floor(Math.random() * screenheight - santaheight) + "px";
                }
                santa.style.left = santax + "px";
            }

            for (var i = 0; i <= snowmax; i++) {
                snowy[i] += snowflakes[i].fall;
                if (snowy[i] >= screenheight) {
                    snowy[i] = -snowflakes[i].size;
                }
                snowflakes[i].style.top = snowy[i] + "px";
                snowflakes[i].style.left = (snowflakes[i].x + 10 * Math.sin(snowy[i] / 9)) + "px";
            }
            setTimeout(function () {
                window.requestAnimationFrame(movesnow_nopile);
            }, 1000 / snowfps);
            //setTimeout("movesnow_nopile()", 60);
        }

        function movesnow_fastpile() {
            if (santaexists) {
                santax += santaspeed;
                if (santax >= screenwidth + santawidth) {
                    santax = -santawidth;
                    santa.style.top = Math.floor(Math.random() * screenheight - santaheight) + "px";
                }
                santa.style.left = santax + "px";
            }
            for (var i = 0; i <= snowmax; i++) {
                snowy[i] += snowflakes[i].fall;
                if (snowy[i] >= screenheight) {
                    snowy[i] = -snowflakes[i].size;
                    //incrementsnowheight;
                    setTimeout("iterfastpile()", 10);
                }
                snowflakes[i].style.top = snowy[i] + "px";
                snowflakes[i].style.left = (snowflakes[i].x + 10 * Math.sin(snowy[i] / 9)) + "px";
            }

            setTimeout(function () {
                window.requestAnimationFrame(movesnow_fastpile);
            }, 1000 / snowfps);
            //setTimeout("movesnow_fastpile()",60);
        }

        var count = 0;
        function iterfastpile() {
            if (count < 5) {
                count++;
                return;
            }
            count = 0;
            if (!ie) {
                fastfillheight -= 0.02 * 5;
                graphics.moveTo(0, fastfillheight);
                graphics.lineTo(realscreenwidth, fastfillheight);
                graphics.stroke();
            }
        }

        window.onload = initsnow;
    }
    // Snow not enabled
    else {
        $(".header > .right > ul").prepend(`
            <a class='enable-snow toggle-theme btn-link' onclick='toggleTheme()'>
                ❄ Turn On Winter Theme
            </a>
        `);
        if (window.innerWidth < 1000) {
            $(".enable-snow").hide();
            $("ul.nav").append($(`
                <li>
                    <a class='enable-snow'
                        onclick='toggleTheme()'>
                            <i class="far fa-snowflake snow-nav-icon"></i>
                            <span class="nav-toggle-snow-text">
                                Turn On <br>
                                Winter Theme
                            </span>
                    </a>
                </li>
            `));
        }
        Cookies.remove("dayStreak");
        Cookies.remove("prevDay");
    }
});

function toggleTheme() {
    let enabled = Cookies.get("disable-theme") == "1" ? "0" : "1";
    Cookies.set("disable-theme", enabled, { expires: 5 * 7 });
    location.reload();
}

function handleDecreaseSnowStreak() {
    if(confirm("Are you sure you want to decrease your snow streak by 1?")) {
        let dayStreak = Cookies.get("dayStreak");
        if(dayStreak <= 1) {
            alert("Your snow streak is already 1 and cannot be decreased further.");
            return;
        }
        Cookies.set("dayStreak", parseInt(dayStreak) - 1, { expires: 5 * 7 });
        location.reload();
    }
}