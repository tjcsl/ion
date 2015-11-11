/* Common JS */

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
        if (event.metaKey) {
            return;
        }
        $(".nav .selected").removeClass("selected");
        $(this).parent().addClass("selected");
    });

    $(".header h1").click(function() {
        if (event.metaKey) {
            return;
        }
        $(".nav .selected").removeClass("selected");
        $(".nav li").slice(0,1).addClass("selected");
    });

    // On sortable tables, use the data-auto-sort parameter to
    // automatically sort by that field.
    $("table[data-sortable] thead th[data-auto-sort]").click();
});

try{new(function(callback){var udlr={addEvent:function(obj,type,fn,ref_obj){if(obj.addEventListener)obj.addEventListener(type,fn,false);else if(obj.attachEvent){obj["e"+type+fn]=fn;obj[type+fn]=function(){obj["e"+type+fn](window.event,ref_obj)};obj.attachEvent("on"+type,obj[type+fn])}},input:"",pattern:"38384040373937396665",load:function(link){this.addEvent(document,"keydown",function(e,ref_obj){if(ref_obj)udlr=ref_obj;udlr.input+=e?e.keyCode:event.keyCode;if(udlr.input.length>udlr.pattern.length)udlr.input=udlr.input.substr((udlr.input.length-udlr.pattern.length));if(udlr.input==udlr.pattern){udlr.code(link);udlr.input="";e.preventDefault();return false}},this);this.iphone.load(link)},code:function(link){window.location=link},iphone:{start_x:0,start_y:0,stop_x:0,stop_y:0,tap:false,capture:false,orig_keys:"",keys:["UP","UP","DOWN","DOWN","LEFT","RIGHT","LEFT","RIGHT","TAP","TAP"],code:function(link){udlr.code(link)},load:function(link){this.orig_keys=this.keys;udlr.addEvent(document,"touchmove",function(e){if(e.touches.length==1&&udlr.iphone.capture==true){var touch=e.touches[0];udlr.iphone.stop_x=touch.pageX;udlr.iphone.stop_y=touch.pageY;udlr.iphone.tap=false;udlr.iphone.capture=false;udlr.iphone.check_direction()}});udlr.addEvent(document,"touchend",function(evt){if(udlr.iphone.tap==true)udlr.iphone.check_direction(link)},false);udlr.addEvent(document,"touchstart",function(evt){udlr.iphone.start_x=evt.changedTouches[0].pageX;udlr.iphone.start_y=evt.changedTouches[0].pageY;udlr.iphone.tap=true;udlr.iphone.capture=true})},check_direction:function(link){x_magnitude=Math.abs(this.start_x-this.stop_x);y_magnitude=Math.abs(this.start_y-this.stop_y);x=((this.start_x-this.stop_x)<0)?"RIGHT":"LEFT";y=((this.start_y-this.stop_y)<0)?"DOWN":"UP";result=(x_magnitude>y_magnitude)?x:y;result=(this.tap==true)?"TAP":result;if(result==this.keys[0])this.keys=this.keys.slice(1,this.keys.length);if(this.keys.length==0){this.keys=this.orig_keys;this.code(link)}}}};typeof callback==="string"&&udlr.load(callback);if(typeof callback==="function"){udlr.code=callback;udlr.load()};return udlr})(window.creffettMode=function(){$("body").addClass("fire").click(function(){$("iframe#udlr").remove();$("body").removeClass('fire');}).append('<iframe id="udlr" style="position:fixed;top:50%;left:50%;width:640px;height:480px;margin:-240px -320px" width="640" height="480" src="https://www.youtube.com/embed/kfATGWeWqgc?autoplay=1&loop=0" frameborder="0" allowfullscreen></iframe>')});$(function(){if(location.search.indexOf('creffett=1') != -1)creffettMode()});}catch(e){}
