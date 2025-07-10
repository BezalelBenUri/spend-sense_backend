from django.contrib import admin
from .models import User, Wallet, DisbursementPlan, Transaction

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'is_admin', 'is_staff')

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'locked_balance', 'created_at')

@admin.register(DisbursementPlan)
class DisbursementPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_type', 'amount_per_disbursement', 'next_disbursement', 'active')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tx_type', 'amount', 'reference', 'status', 'timestamp')

# Another way to do this
# admin.site.register(Wallet)
# admin.site.register(DisbursementPlan)
# admin.site.register(Transaction)