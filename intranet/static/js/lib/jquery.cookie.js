/*!
 * jQuery Cookie Plugin v1.3.1
 * https://github.com/carhartl/jquery-cookie
 *
 * Copyright 2013 Klaus Hartl
 * Released under the MIT license
 */
 (function(e,t,n){function i(e){return e}function s(e){return o(decodeURIComponent(e.replace(r," ")))}function o(e){if(e.indexOf('"')===0){e=e.slice(1,-1).replace(/\\"/g,'"').replace(/\\\\/g,"\\")}return e}function u(e){return a.json?JSON.parse(e):e}var r=/\+/g;var a=e.cookie=function(r,o,f){if(o!==n){f=e.extend({},a.defaults,f);if(o===null){f.expires=-1}if(typeof f.expires==="number"){var l=f.expires,c=f.expires=new Date;c.setDate(c.getDate()+l)}o=a.json?JSON.stringify(o):String(o);return t.cookie=[encodeURIComponent(r),"=",a.raw?o:encodeURIComponent(o),f.expires?"; expires="+f.expires.toUTCString():"",f.path?"; path="+f.path:"",f.domain?"; domain="+f.domain:"",f.secure?"; secure":""].join("")}var h=a.raw?i:s;var p=t.cookie.split("; ");var d=r?null:{};for(var v=0,m=p.length;v<m;v++){var g=p[v].split("=");var y=h(g.shift());var b=h(g.join("="));if(r&&r===y){d=u(b);break}if(!r){d[y]=u(b)}}return d};a.defaults={};e.removeCookie=function(t,n){if(e.cookie(t)!==null){e.cookie(t,null,n);return true}return false}})(jQuery,document)
