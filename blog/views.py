from django.views.generic import ListView, DetailView

from blog.models import Post


class PostDetail(DetailView):
    model = Post
    template_name = "new/post_detail.html"
    context_object_name = "post"


class PostList(ListView):
    context_object_name = "posts"
    model = Post
    ordering = ["-published_date"]
    template_name = "new/post_list.html"
