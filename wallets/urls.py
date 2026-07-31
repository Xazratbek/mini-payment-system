from django.urls import path

from .views import WalletDetailView, WalletTopUpView


urlpatterns = [
    path("", WalletDetailView.as_view(), name="wallet-detail"),
    path("top-up/", WalletTopUpView.as_view(), name="wallet-top-up"),
]

