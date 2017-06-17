$(document).ready(function(){
    var clipboard = new Clipboard('.btn');

    clipboard.on('success', function(e) {
        alert('Copied');
    });
})
