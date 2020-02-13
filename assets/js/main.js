$(document).ready(function() {
    if (!Cookies.get('ctrs-cookie')) {
        $("#cookie-disclaimer").removeClass('hide');
    }
    // Set cookie and hide the box
    $('#cookie-disclaimer .close').on("click", function() {
        Cookies.set('ctrs-cookie', 'ctrs-cookie-set', { expires: 30 });
        $("#cookie-disclaimer").addClass('hide');
    });
});