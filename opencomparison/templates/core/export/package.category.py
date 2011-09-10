{% for category in categories %}
    category_{{ forloop.counter }} = Category.objects.create(
        title = "{{ category.title }}"[:50],
        slug  = "{{ category.slug }}",
        description = "{{ category.description }}",
        title_plural = "{{ category.title_plural }}"[:50],
        show_pypi = {{ category.show_pypi }}
    )
{% endfor %}