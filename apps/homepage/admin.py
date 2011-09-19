from django.contrib import admin

from homepage.models import Dpotw, Gotw, Tab


class TabAdmin(admin.ModelAdmin):
    
    list_display = ('grid', 'order', )
    list_editable = ('order', )
    
admin.site.register(Tab, TabAdmin)    

admin.site.register(Dpotw)
admin.site.register(Gotw)

