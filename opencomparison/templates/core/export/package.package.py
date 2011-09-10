from django.contrib.auth.models import User



{% for p in packages %}
    package_{{ forloop.counter }} = Package.objects.create(
        title           = "{{ p.title }}"[:100],
        slug            = "{{ p.slug }}",
        category_id     = "{{ p.category.id }}",
        repo_description= "{{ p.repo_description }}"
        repo_url        = "{{ p.repo_url }}",
        repo_watchers   = {{ p.repo_watchers }},
        repo_forks      = {{ p.repo_forks }},
        repo_commits    = {{ p.repo_commits }},
        pypi_url        = "{{ p.pypi_url }}",
        pypi_downloads  = {{ p.pypi_downloads }},
        participants    = "{{ p.participants }}",
        {% if p.created_by.username.strip %}        
            created_by = User.objects.get(username = "{{ p.created_by.username }}"),
        {% endif %}
        {% if p.last_modified_by.username.strip %}
            last_modified_by = User.objects.get(username = "{{ p.last_modified_by.username }}"),
        {% endif %}
        pypi_home_page  = "{{ p.pypi_home_page }}"
        
    )
    package_{{ forloop.counter }}.save()
    {% if p.usage.count %}
    usage = [{% for u in p.usage.all %}User.objects.get(username = "{{ u.username }}"),{% endfor %}]
    package_{{ forloop.counter }}.usage.add(usage)
    {% endif %}
    
{% endfor %}