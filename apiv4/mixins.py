class MultiLookupFieldMixin:
    lookup_url_kwarg = "pk_or_slug"

    @property
    def lookup_field(self):
        assert self.lookup_url_kwarg, "The `lookup_url_kwarg` field is required."

        obj_ident = self.kwargs[self.lookup_url_kwarg]
        return "pk" if obj_ident.isdigit() else "slug"
