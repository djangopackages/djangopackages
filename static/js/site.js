// Ajax submit for the package usage
/*
$(".usage-link").live('click', function(e) {
    e.preventDefault();
    var link = $(this),
        container, count_el, usage_icon, icon_src;
        
    $.getJSON(link.attr('href'), function(data) {
        if (data.success === true) {
            container = link.parents('.usage-holder');
            
            // Update the count
            count_el = container.find('.usage-count');
            count_el.html(parseInt(count_el.html(), 10) + data.change);
            
            // Update the image & link
            usage_icon = container.find('.usage-image');
            icon_src = usage_icon.attr('src');
            if (data.change == -1) {
                usage_icon.attr('src', icon_src.replace('_filled.png', '_hollow.png'));
                link.attr('href', link.attr('href').replace('/remove/', '/add/'));
            } else if (data.change == 1) {
                usage_icon.attr('src', icon_src.replace('_hollow.png', '_filled.png'));
                link.attr('href', link.attr('href').replace('/add/', '/remove/'));
            }
        } else {
            if (data.redirect) {
                window.location = data.redirect;
            }
        }
    });
});
*/

$(".messages li a").click(function() {
    $(this).parent().fadeOut();
    return false;
});


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
