import pytest
from django.urls.exceptions import NoReverseMatch

# def test_homepage_view(db, tp, homepage_data):
#     url = reverse("home")
#     response = tp.client.get(url)
#     assert response.status_code == 200
#     assertTemplateUsed(response, "homepage.html")

#     soup = BeautifulSoup(response.content, "html.parser")
#     assert soup.find("meta", property="og:image")["content"] == "https://todo"
#     assert soup.find("meta", property="og:title")["content"] == "Django Packages : Reusable apps, sites and tools directory"
#     assert soup.find("meta", property="og:type")["content"] == "website"
#     assert soup.find("meta", property="og:url")["content"] == "https://djangopackages.org/"

#     assert Package.objects.all().exists()
#     for p in Package.objects.all():
#         assert p.title in str(response.content)
#         assert p.repo_description in str(response.content)

#     assert response.context["package_count"] == Package.objects.count()


# def test_categories_on_homepage(db, tp, homepage_data):
#     url = reverse("home")
#     response = tp.client.get(url)
#     assert response.status_code == 200
#     assertTemplateUsed(response, "homepage.html")

#     for c in Category.objects.all():
#         assert c.title_plural in str(response.content)
#         assert c.description in str(response.content)


# def test_homepage_view_without_packages(db, tp, homepage_data):
#     Package.objects.all().delete()
#     url = reverse("home")
#     response = tp.client.get(url)
#     assert response.status_code == 200
#     assertTemplateUsed(response, "homepage.html")


def test_homepage(db, tp, django_assert_num_queries):
    url = tp.reverse("home")
    with django_assert_num_queries(11):
        response = tp.client.get(url)
    assert response.status_code == 200


def test_404_test(db, tp):
    response = tp.client.get("/404")
    assert response.status_code == 404


def test_500_test(db, tp):
    response = tp.client.get("/500")
    assert response.status_code == 500


def test_readiness(db, tp, django_assert_num_queries, product, release):
    url = tp.reverse("readiness")
    with django_assert_num_queries(7):
        response = tp.client.get(url)
    assert response.status_code == 200


@pytest.mark.xfail(raises=NoReverseMatch)
def test_readiness_detail(db, tp, django_assert_num_queries, product, release):
    url = tp.reverse(
        "readiness_detail",
        kwargs={"product_slug": str(release.product.slug), "cycle": str(release.cycle)},
    )
    with django_assert_num_queries(0):
        response = tp.client.get(url)
    assert response.status_code == 200
