def test_about(db, tp):
    url = tp.reverse("about")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_faq(db, tp):
    url = tp.reverse("faq")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_funding(db, tp):
    url = tp.reverse("funding")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_help(db, tp):
    url = tp.reverse("help")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_login(db, tp):
    url = tp.reverse("login")
    response = tp.client.get(url)
    assert response.status_code == 200
    assert b'<form method="post" action="/auth/login/github/">' in response.content


def test_login_carries_next_as_hidden_input(db, tp):
    url = tp.reverse("login")
    response = tp.client.get(url, {"next": "/profiles/edit/"})
    assert response.status_code == 200
    assert (
        b'<input type="hidden" name="next" value="/profiles/edit/">' in response.content
    )


def test_login_required_view_redirects_to_login(db, tp):
    url = tp.reverse("profile_edit")
    response = tp.client.get(url)
    assert response.status_code == 302
    assert response["Location"] == "/login/?next=/profiles/edit/"


def test_open(db, tp):
    from package.models import Category

    Category.objects.create(
        title="Admin Interface",
        slug="admin-interface",
    )
    url = tp.reverse("open")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_robots_txt(db, tp):
    url = tp.reverse("robots_txt")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_sitemap_index(db, tp):
    url = tp.reverse("sitemap_index")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_sitemap_static_section(db, tp):
    url = tp.reverse("sitemaps", section="static")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_sitemap_packages_section(db, tp):
    url = tp.reverse("sitemaps", section="packages")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_sitemap_grids_section(db, tp):
    url = tp.reverse("sitemaps", section="grids")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_sitemap_blog_section(db, tp):
    url = tp.reverse("sitemaps", section="blog")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_sitemap_invalid_section(db, tp):
    url = tp.reverse("sitemaps", section="invalid")
    response = tp.client.get(url)
    assert response.status_code == 404


def test_syndication(db, tp):
    url = tp.reverse("syndication")
    response = tp.client.get(url)
    assert response.status_code == 200


def test_terms(db, tp):
    url = tp.reverse("terms")
    response = tp.client.get(url)
    assert response.status_code == 200
