from django.contrib import admin

from .models import (PairsOfOptionsPARK, RangeValue,
                     ValueOfPerfectAlternativePARK)

admin.site.register(RangeValue)
admin.site.register(ValueOfPerfectAlternativePARK)
admin.site.register(PairsOfOptionsPARK)