from django.contrib import admin

from .models import ModelModification, CriterionModification, TypeModification, ModificationValue, ModificationOption, \
    ModificationPairsOfOptions

admin.site.register(ModelModification)
admin.site.register(CriterionModification)
admin.site.register(TypeModification)
admin.site.register(ModificationValue)
admin.site.register(ModificationOption)
admin.site.register(ModificationPairsOfOptions)