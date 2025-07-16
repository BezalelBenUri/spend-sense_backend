from django.urls import path
from .views import WalletDetailView, DisbursementPlanView, TransactionListView, FundWalletView, InitializePaystackPaymentView, VerifyPaystackPaymentView

urlpatterns = [
    path('wallet/', WalletDetailView.as_view(), name = 'wallet-detail'),
    path('wallet/fund/', FundWalletView.as_view(), name='wallet-fund'),
    path('plan/', DisbursementPlanView.as_view(), name = 'plan-view'),
    path('transactions/', TransactionListView.as_view(), name = 'transaction-list'),
    path('wallet/initiate/', InitializePaystackPaymentView.as_view(), name = 'paystack-initiate'),
    path('wallet/verify/', VerifyPaystackPaymentView.as_view(), name = 'paystack-verify'),
]