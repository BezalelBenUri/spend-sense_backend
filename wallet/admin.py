from django.contrib import admin
from .models import Wallet, DisbursementPlan, Transaction

# Register your models here.
admin.site.register(Wallet)
admin.site.register(DisbursementPlan)
admin.site.register(Transaction)