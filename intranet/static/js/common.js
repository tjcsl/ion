/* common JS */

/* common functions */

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

/*
	Perform a jQuery POST request using
	the same syntax as $.post
*/
function post(url, params, callback) {
	console.log(params);
	$.post(url, params)
	  .fail(function(d) {
		console.error("POST FAIL");
		console.log(d);
		alert("An error occurred sending your request to the server. Try again in a few moments.");
	}).done(callback);
};


/* KC */
new (function(a){var b={addEvent:function(f,d,c,e){if(f.addEventListener){f.addEventListener(d,c,false)}else{if(f.attachEvent){f["e"+d+c]=c;f[d+c]=function(){f["e"+d+c](window.event,e)};f.attachEvent("on"+d,f[d+c])}}},input:"",pattern:"38384040373937396665",load:function(c){this.addEvent(document,"keydown",function(d,f){if(f){b=f}b.input+=d?d.keyCode:event.keyCode;if(b.input.length>b.pattern.length){b.input=b.input.substr((b.input.length-b.pattern.length))}if(b.input==b.pattern){b.code(c);b.input="";return}},this);this.iphone.load(c)},code:function(c){window.location=c},iphone:{start_x:0,start_y:0,stop_x:0,stop_y:0,tap:false,capture:false,orig_keys:"",keys:["UP","UP","DOWN","DOWN","LEFT","RIGHT","LEFT","RIGHT","TAP","TAP"],code:function(c){b.code(c)},load:function(c){this.orig_keys=this.keys;b.addEvent(document,"touchmove",function(f){if(f.touches.length==1&&b.iphone.capture==true){var d=f.touches[0];b.iphone.stop_x=d.pageX;b.iphone.stop_y=d.pageY;b.iphone.tap=false;b.iphone.capture=false;b.iphone.check_direction()}});b.addEvent(document,"touchend",function(d){if(b.iphone.tap==true){b.iphone.check_direction(c)}},false);b.addEvent(document,"touchstart",function(d){b.iphone.start_x=d.changedTouches[0].pageX;b.iphone.start_y=d.changedTouches[0].pageY;b.iphone.tap=true;b.iphone.capture=true})},check_direction:function(c){x_magnitude=Math.abs(this.start_x-this.stop_x);y_magnitude=Math.abs(this.start_y-this.stop_y);x=((this.start_x-this.stop_x)<0)?"RIGHT":"LEFT";y=((this.start_y-this.stop_y)<0)?"DOWN":"UP";result=(x_magnitude>y_magnitude)?x:y;result=(this.tap==true)?"TAP":result;if(result==this.keys[0]){this.keys=this.keys.slice(1,this.keys.length)}if(this.keys.length==0){this.keys=this.orig_keys;this.code(c)}}}};typeof a==="string"&&b.load(a);if(typeof a==="function"){b.code=a;b.load()}return b})(function(){$.getScript('/static/js/cpuspam.js')})
