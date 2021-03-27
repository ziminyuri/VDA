from django.contrib import admin

from .models import (Criterion, HistoryAnswer, Model, Option, PairsOfOptions,
                     PairsOfOptionsPARK, RangeValue, Value,
                     ValueOfPerfectAlternativePARK)

admin.site.register(Model)
admin.site.register(Criterion)
admin.site.register(Option)
admin.site.register(Value)
admin.site.register(PairsOfOptions)
admin.site.register(HistoryAnswer)
admin.site.register(RangeValue)
admin.site.register(ValueOfPerfectAlternativePARK)
admin.site.register(PairsOfOptionsPARK)
