// need to add 'is_other' to repos so we can make this work

var repo_data = eval({{ repo_data|safe }});
var get_slug_from_repo_data = function (repo_root_url, repo_branch_url) {
    var slug = null;
    for (i=0;i<repo_data.length;i++) {
        if (repo_data[i].url == repo_root_url) {
            var regexp_title = new RegExp(repo_data[i].repo_regex);
            var match_obj = regexp_title.exec(repo_branch_url);
            if (match_obj !== null) {
                slug = match_obj[1]
            }
            break;
        }
    }
    return slug;
}

String.prototype.starts_with = function(str){
    return (this.indexOf(str) === 0);
}

String.prototype.ends_with = function(str){
    return (this.lastIndexOf(str) === this.length-str.length);
}

$("#id_repo_url").focus();

pypi_url_g = "http://pypi.python.org/pypi/";

$("#id_pypi_url").val($("#id_pypi_url").val().replace(pypi_url_g,""));

$("#id_pypi_url").change(function(e){
    $("#id_pypi_url").val($("#id_pypi_url").val().replace(pypi_url_g,""));
});

$("#id_repo_url").keyup(function(e) {
    var url = $("#id_repo_url").val();
    return url
});
    
$("#id_repo_url").change(function(e) {
 
    $("#target").text($("#id_repo_url").val());
    
    var url = $("#id_repo_url").val();
    
    // this fixes the problem with trailing slashes
    while (1==1){
            if (url.ends_with('/')){
                url = url.slice(0, url.length-1);
                $("#id_repo_url").val(url);
                }
            else {
                break;
            };
        };
    // for github
    if (url.starts_with('http://github.com')){
        url = url.replace('http://github.com','https://github.com');
        $("#id_repo_url").val(url);
    };
    if (url.starts_with('git@github.com:')){
        url = url.replace("git@github.com:","https://github.com/");
    };
    if (url.starts_with('git://github.com/')){
        url = url.replace("git://github.com/","https://github.com/");
        $("#id_repo_url").val(url);                
    };
    if (url.ends_with('.git')){
        url = url.slice(0, url.length-4);
        $("#id_repo_url").val(url);                
    };
    // for bitbucket
    if (url.starts_with('http://bitbucket.org')){
        url = url.replace('http://bitbucket.org','https://bitbucket.org');
        $("#id_repo_url").val(url);        
    };
    // for launchpad
    if (url.starts_with('lp:')){
        url = url.replace('lp:', 'https://code.launchpad.net/');
        $("#id_repo_url").val(url);
    };
    
    var url_array = url.split('/');
    $.each(repo_data, function(index, item) {
        if (url.starts_with(item.url)){
            if (url !== item.url){
                var slug = null;
                if ($("#id_title").val().length === 0) {
                    // determine title/slug automagically
                    slug = get_slug_from_repo_data(item.url, url);
                    $("#id_title").val(slug);
                };
                if (slug === null) {
                    // fallback slug detector
                    slug = DPSlugify(url_array[url_array.length-1]);
                }
                $("#id_slug").val(slug);
                $("#id_pypi_url").val(slug);
                $("#package-form-message").text("Your package is hosted at " + item.title)
            };
        };
    });
});

$("#package-form").submit(function(e) {
    // hack to get around some database vs front end weirdness
    var pypi_url = $("#id_pypi_url").val();
    if (pypi_url.length > 0){
      $("#id_pypi_url").attr("name", "nuke");
      $("#temp").val(pypi_url_g + pypi_url);
      $("#temp").attr("name", "pypi_url");     
    };
    
    return true
});
