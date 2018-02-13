function package_form(data){
	var get_slug_from_repo_data = function (repo_root_url, repo_branch_url) {
		var slug = null;
		for (i=0;i<data.length;i++) {
			if (data[i].url == repo_root_url) {
				var regexp_title = new RegExp(data[i].repo_regex);
				var match_obj = regexp_title.exec(repo_branch_url);
				if (match_obj !== null) {
					slug = match_obj[1]
				}
				break;
			}
		}
		return slug;
	}
	var REPLACEMENTS = {
		'https://github.com': [
			'http://github.com',
			'git@github.com:',
			'git://github.com'
		],
		'https://bitbucket.org': [
			'http://bitbucket.org'
		],
		'https://code.launchpad.net/': [
			'lp:'
		]
	};

	var repo_url = $("#id_repo_url");
	var pypi_url = $("#id_pypi_url");

	String.prototype.starts_with = function(str){
		return (this.length > 0 && this.indexOf(str) === 0);
	}

	String.prototype.ends_with = function(str){
		return (this.length > 0 && this.lastIndexOf(str) === this.length-str.length);
	}

	repo_url.focus();

	pypi_url_g = "http://pypi.python.org/pypi/";

	pypi_url.val(pypi_url.val().replace(pypi_url_g,""));

	pypi_url.change(function(e){
		pypi_url.val(pypi_url.val().replace(pypi_url_g,""));
	});

	repo_url.keyup(function(e) {
		var url = repo_url.val();
		return url
	});

	repo_url.change(function(e) {

		$("#target").text(repo_url.val());

		var url = repo_url.val();

		// this fixes the problem with trailing slashes
		while (1==1){
			if (url.ends_with('/')){
				url = url.slice(0, url.length-1);
				repo_url.val(url);
				}
			else {
				break;
			};
		};

		$.each(REPLACEMENTS, function(key, value){
			$.each(value, function(index, prefix){
				if (url.starts_with(prefix)){
					url = key + url.slice(prefix.length);
				}
            });
		});
		if (url.ends_with('.git')){
			url = url.slice(0, url.length-4);
			repo_url.val(url);
		};
		repo_url.val(url);

		var url_array = url.split('/');
		$.each(data, function(index, item) {
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
					pypi_url.val(slug);
					for (i=0;i<10;i++) {
					    slug = slug.replace('.','-');
				    };
				    $("#id_slug").val(slug);
					$("#package-form-message").text("Your package is hosted at " + item.title)
				};
			};
		});
	});

	var slug = $("#id_slug");
	slug.change(function(e) {
		for (i=0;i<10;i++) {
		    slug.val(slug.val().replace('.','-'));
	    };
	});

	$("#package-form").submit(function(e) {
		// hack to get around some database vs front end weirdness
		var url = pypi_url.val();
		if (url.length > 0){
		  pypi_url.attr("name", "nuke");
		  $("#temp").val(pypi_url_g + url);
		  $("#temp").attr("name", "pypi_url");
		};

		return true
	});
}
