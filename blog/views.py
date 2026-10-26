from django.views.generic import DetailView, ListView

from blog.models import Post


class PostDetail(DetailView):
    model = Post
    template_name = "blog/post_detail.html"
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.published()


class PostOpenGraphView(DetailView):
    model = Post
    template_name = "partials/opengraph_card.html"
    context_object_name = "post"

    def get_queryset(self):
        return Post.objects.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        context.update(
            card_kind="Changelog",
            card_title=post.title,
            card_description=post.summary,
            card_path=post.get_absolute_url(),
        )
        return context


class PostList(ListView):
    context_object_name = "posts"
    model = Post
    ordering = ["-published_date"]
    template_name = "blog/post_list.html"

    def get_queryset(self):
        return Post.objects.published()
