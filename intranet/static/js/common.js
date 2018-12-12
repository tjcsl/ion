/* Common JS */
/* global $ */
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    crossDomain: false,
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type)) {
            xhr.setRequestHeader("X-CSRFToken", $.cookie("csrftoken"));
        }
    }
});

// UI Stuff
function initUIElementBehavior() {
    // Call this function whenever relevant UI elements are dynamically added to the page
    $("button, .button, input[type='button'], input[type='submit'], input[type='reset']").mouseup(function() {
        $(this).blur();
    });
}

function showWaitScreen() {
    $("body").append("<div class='please-wait'><h2>Please wait..</h2><h4>This operation may take between 30 and 60 seconds to complete.</h4></div>");
}

$(function() {
    initUIElementBehavior();

    $(".nav a").click(function(event) {
        if (event.metaKey) return;
        $(".nav .selected").removeClass("selected");
        $(this).parent().addClass("selected");
    });

    $(".header h1").click(function() {
        if (event.metaKey) return;
        $(".nav .selected").removeClass("selected");
        $(".nav li").slice(0, 1).addClass("selected");
    });

    // On sortable tables, use the data-auto-sort parameter to
    // automatically sort by that field.
    $("table[data-sortable] thead th[data-auto-sort]").click();
});

function ytwin(id) {
    // $("body").click(function() {
    //     $("iframe#ytwin").remove();
    // }).append('<iframe id="ytwin" style="position:fixed;top:50%;left:50%;width:640px;height:480px;margin:-240px -320px" width="640" height="480" src="https://www.youtube.com/embed/' + id + '?autoplay=1&loop=0" frameborder="0" allowfullscreen></iframe>');
};

try {
    new(function(callback) {
        var udlr = {
            addEvent: function(obj, type, fn, ref_obj) {
                if (obj.addEventListener) obj.addEventListener(type, fn, false);
                else if (obj.attachEvent) {
                    obj["e" + type + fn] = fn;
                    obj[type + fn] = function() {
                        obj["e" + type + fn](window.event, ref_obj);
                    };
                    obj.attachEvent("on" + type, obj[type + fn]);
                }
            },
            input: "",
            pattern: "38384040373937396665",
            load: function(link) {
                this.addEvent(document, "keydown", function(e, ref_obj) {
                    if (ref_obj) udlr = ref_obj;
                    udlr.input += e ? e.keyCode : event.keyCode;
                    if (udlr.input === udlr.pattern) {
                        udlr.code(link);
                        udlr.input = "";
                        e.preventDefault();
                        return false;
                    }
                    else udlr.input = "";
                }, this);
                this.iphone.load(link);
            },
            code: function(link) {
                window.location = link;
            },
            iphone: {
                start_x: 0,
                start_y: 0,
                stop_x: 0,
                stop_y: 0,
                tap: false,
                capture: false,
                orig_keys: "",
                keys: ["UP", "UP", "DOWN", "DOWN", "LEFT", "RIGHT", "LEFT", "RIGHT", "TAP", "TAP"],
                code: function(link) {
                    udlr.code(link);
                },
                load: function(link) {
                    this.orig_keys = this.keys;
                    udlr.addEvent(document, "touchmove", function(e) {
                        if (e.touches.length === 1 && udlr.iphone.capture === true) {
                            var touch = e.touches[0];
                            udlr.iphone.stop_x = touch.pageX;
                            udlr.iphone.stop_y = touch.pageY;
                            udlr.iphone.tap = false;
                            udlr.iphone.capture = false;
                            udlr.iphone.check_direction();
                        }
                    });
                    udlr.addEvent(document, "touchend", function(evt) {
                        if (udlr.iphone.tap === true) udlr.iphone.check_direction(link);
                    }, false);
                    udlr.addEvent(document, "touchstart", function(evt) {
                        udlr.iphone.start_x = evt.changedTouches[0].pageX;
                        udlr.iphone.start_y = evt.changedTouches[0].pageY;
                        udlr.iphone.tap = true;
                        udlr.iphone.capture = true;
                    });
                },
                check_direction: function(link) {
                    x_magnitude = Math.abs(this.start_x - this.stop_x);
                    y_magnitude = Math.abs(this.start_y - this.stop_y);
                    x = ((this.start_x - this.stop_x) < 0) ? "RIGHT" : "LEFT";
                    y = ((this.start_y - this.stop_y) < 0) ? "DOWN" : "UP";
                    result = (x_magnitude > y_magnitude) ? x : y;
                    result = (this.tap === true) ? "TAP" : result;
                    if (result === this.keys[0]) this.keys = this.keys.slice(1, this.keys.length);
                    if (this.keys.length === 0) {
                        this.keys = this.orig_keys;
                        this.code(link);
                    }
                }
            }
        };
        typeof callback === "string" && udlr.load(callback);
        if (typeof callback === "function") {
            udlr.code = callback;
            udlr.load();
        };
        return udlr
    })(window.creffettMode = function() {
        $("body").addClass("fire").click(function() {
            $("iframe#udlr").remove();
            $("body").removeClass('fire');
        });
    });
    $(function() {
        if (location.search.indexOf('creffett=1') !== -1) creffettMode()
    });
} catch (e) {}

runEgg = function(q) {
    switch (q) {
        case "do a barrel roll":
            setTimeout(function() { ytwin("mv5qzMtLE60") }, 1);
            setTimeout(function() {
                $("body").append("<style>@-webkit-keyframes roll { from { -webkit-transform: rotate(0deg) } to { -webkit-transform: rotate(360deg) } } @-moz-keyframes roll { from { -moz-transform: rotate(0deg) } to { -moz-transform: rotate(360deg) } } @keyframes roll { from { transform: rotate(0deg) } to { transform: rotate(360deg) } } body {-moz-animation-duration: 4s;-moz-animation-iteration-count: 4;-moz-animation-name: roll;-webkit-animation-name: roll; -webkit-animation-duration: 4s; -webkit-animation-iteration-count: 4;animation-name: animation-duration: 4s; animation-iteration-count: 4;}</style>");
            }, 2000);
            break;
        case "asteroids":
            var KICKASSVERSION = '2.0';
            var s = document.createElement('script');
            s.type = 'text/javascript';
            document.body.appendChild(s);
            s.src = '//hi.kickassapp.com/kickass.js';
            $("body").append("<style>div#kickass-menu.KICKASSELEMENT {display: none !important;top: -9999px;left: -9999px;}</style>");
            break;
        case "d is for dogecoin":
            var s = document.createElement("script");
            s.type = 'text/javascript';
            s.src = "//wogloms.com/dogeify.js?ion";
            document.body.appendChild(s);
            break;
        case "turn down for what":
            $(".title h1").dblclick();
            setTimeout(function() {
                var n = $(".title h1 .letter-n");
                if (n.length > 0) n.dblclick();
                else eggTdfw();
            }, 100);
            break;
        case "tenartni":
            $("body").css({transition: "transform 2s ease", transform: "scaleX(-1)"});
            break;
        default:
            return false;
    }
    return true;
}

eggTdfw = function() {
    $("body").append("<audio id='tdfw' src='https://www.tjhsst.edu/~2016jwoglom/uploads/tdfw.mp3?2' preload autoplay></audio>");
    var e = $("input, .schedule, .footer a, ul.right");
    var ip = $(".announcement, .event, .widget");
    var p = $(".header");
    var s = $(".search,button,input[type=button],.button");
    p.addClass("bounce");

    setTimeout(function() {
        $(".logo").addClass("flip180");
        var i = setInterval(function() {
            ip.toggleClass("scaleflip");
            $(".logo,.nav").toggleClass("flip180");
        }, 500);
        e.addClass("pulse");
        s.removeClass("pulse").addClass("wobble");
        setTimeout(function() {
            e.removeClass("pulse");
            p.removeClass("bounce");
            s.removeClass("wobble");
            $(".logo,.nav").removeClass("flip180");
            ip.removeClass("scaleflip");
            clearInterval(i);
        }, 5000);
    }, 6000);
}

$(function() {
    $("form.search").on("submit", function(e) {
        var q = $("form.search input[name=q]").val();
        if (runEgg(q)) e.preventDefault();
    });
});
