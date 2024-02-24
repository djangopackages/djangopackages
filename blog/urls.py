from django.urls import path

from blog.views import PostList, PostDetail

urlpatterns = [
    path("", PostList.as_view(), name="post_list"),
    path("<slug:slug>/", PostDetail.as_view(), name="post_detail"),
]
