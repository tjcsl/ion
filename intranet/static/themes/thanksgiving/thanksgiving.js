/* Ion Thanksgiving Theme
 * Falling leaves and a turkey.
 * Leaves don't stack because it's super laggy with emojis.
 * Begins a week before Thanksgiving until the end of Thanksgiving day.
 */

$(function () {
    //leaves
    var leaves   = ['\uD83C\uDF42', '\uD83C\uDF41', '\uD83C\uDF43']; // these emojis 🍂 🍁 🍃
    var anims    = ['leaf-fall', 'leaf-fall-2'];
    var leafCount = 22;

    var cols = 12;
    var pileHeights = [];
    for (var c = 0; c < cols; c++) {
        pileHeights[c] = 0;
    }
    //rotation of the leaves randomized
    for (var i = 0; i < leafCount; i++) {
        (function(idx) {
            var leaf = document.createElement('span');
            leaf.className = 'tg-leaf';
            leaf.textContent = leaves[Math.floor(Math.random() * leaves.length)];

            var col = Math.floor(Math.random() * cols);
            var startX = (col / cols * 100) + (Math.random() * (100 / cols));
            leaf.style.left = startX + 'vw';

            var duration = 8 + Math.random() * 8;
            var delay    = Math.random() * 20;
            var anim     = anims[Math.floor(Math.random() * anims.length)];
            var size     = 1.0 + Math.random() * 1.3;

            var floorVh = 92 - pileHeights[col];
            pileHeights[col] += 2.5;
            if (pileHeights[col] > 32) pileHeights[col] = 0;

            leaf.style.setProperty('--leaf-floor', floorVh + 'vh');
            leaf.style.animationName     = anim;
            leaf.style.animationDuration = duration + 's';
            leaf.style.animationDelay    = '-' + delay + 's';
            leaf.style.fontSize          = size + 'em';

            document.body.appendChild(leaf);
        })(i);
    }

//turkey
    var turkey = document.createElement('span');
    turkey.className = 'tg-turkey';
    turkey.textContent = '\uD83E\uDD83'; // this emoji 🦃
    document.body.appendChild(turkey);

    //toggle thanksgiving theme
    $('.header > .right > ul').prepend(
        '<a class="toggle-thanksgiving-theme" onclick="toggleThanksgivingCookie()">&#127810; Turn Off Thanksgiving Theme</a>'
    );

    if (window.innerWidth < 1000) {
        $('.toggle-thanksgiving-theme').first().hide();
        var liOff = document.createElement('li');
        liOff.innerHTML = '<a class="toggle-thanksgiving-theme" onclick="toggleThanksgivingCookie()">' +
            '<i class="fas fa-leaf" style="font-size:16pt;position:relative;top:3px;left:6px;"></i>' +
            '<span style="position:relative;bottom:9px;left:15px;">Turn Off<br>Thanksgiving Theme</span>' +
            '</a>';
        document.querySelector('ul.nav').appendChild(liOff);
    }
});

function toggleThanksgivingCookie() {
    var enabled = Cookies.get('disable-thanksgiving') == '1' ? '0' : '1';
    Cookies.set('disable-thanksgiving', enabled, { expires: 7 });
    location.reload();
}