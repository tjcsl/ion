/* Iodine (Intranet2) Snow Script
 * Credits: dmorris, zyaro
 */
//TJHSST Intranet login page snow script

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
    window.requestAnimationFrame = function(f) {
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
    var sinkspeed = fastbrowser ? 0.5 : 1;
}

if (typeof snowmaxsize === "undefined" || typeof snowminsize === "undefined") {
    //Maximum size of snowflakes
    var snowmaxsize = mobile ? 44 : 22;
    //Miniumum size of snowflakes
    var snowminsize = mobile ? 16 : 8;
}

if (typeof snowfps === "undefined") {
    snowfps = 30;
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

    ranges = ranges.map(function(el) {
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
    container.style.marginTop = "-20px";
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
    } else if (fastpile) {
        window.requestAnimationFrame(movesnow_fastpile);
        //setTimeout("movesnow_fastpile()", 30);
    } else {
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

    for (var i = 0; i <= snowmax; i++) {
        snowy[i] += snowflakes[i].fall;

        snowflakes[i].style.top = snowy[i] + "px";
        newx = snowflakes[i].x + 10 * Math.sin(snowy[i] / 9);
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

    setTimeout(function() {
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

    setTimeout(function() {
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

    setTimeout(function() {
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
