from django.contrib import admin

from .models import (Criterion, Model, Option,
                     Value)

admin.site.register(Model)
admin.site.register(Criterion)
admin.site.register(Option)
admin.site.register(Value)
