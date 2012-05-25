$.fn.checkRTD = function(options){
    var settings = $.extend( {
      'yes': 'Yes',
      'no' : 'No'
    }, options);
    return this.each(function(){
        var ele = $(this);
        var slug = ele.attr('rel');
        var url = "http://readthedocs.org/api/v1/build/" + slug + "/?format=jsonp";
        $.ajax({
            url: url,
            dataType: 'jsonp',
            success: function(data){
                if (data.objects.length > 0){
                    ele.html('<a href="http://' + slug + '.rtfd.org">' + settings.yes + '</a>');
                } else {
                    ele.text(settings.no);
                }
            },
            error: function(){
                ele.text(settings.no);
            }
        });
    });
}