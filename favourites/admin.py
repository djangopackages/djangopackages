from django.contrib import admin
from favourites.models import Favourite

# Register your models here.


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    raw_id_fields = ["favourited_by", "package"]
