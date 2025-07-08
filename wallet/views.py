from django.shortcuts import render

from rest_framework import generics, permissions
from .models import Wallet, DisbursementPlan, Transaction
from .serializers import WalletSerializer, DisbursementPlanSerializer, TransactionSerializer

# Create your views here.
class WalletDetailView(generics.RetrieveAPIView):
    """
    API view to retrieve the authenticated user's wallet details.

    This view provides a read-only endpoint (`GET`) for a single Wallet instance.
    It ensures that only the authenticated user can access their own wallet information.

    Attributes:
        serializer_class (Serializer): The serializer class used for validating
                                       and serializing the Wallet data.
        permission_classes (list): A list of permission classes that a user must
                                   satisfy to access this view. `IsAuthenticated`
                                   ensures only logged-in users can access.

    Methods:
        get_object(): Overrides the default method to fetch the Wallet instance
                      associated with the current authenticated user.
    """
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Retrieves the Wallet object associated with the current authenticated user.

        Returns:
            Wallet: The Wallet instance belonging to `self.request.user`.
        """
        return self.request.user.wallet

class DisbursementPlanView(generics.RetrieveUpdateAPIView):
    """
    API view to retrieve or update the authenticated user's disbursement plan.

    This view provides both read (`GET`) and update (`PUT`/`PATCH`) functionalities
    for a single DisbursementPlan instance. If a plan does not exist for the user,
    it will be created automatically upon access.

    Attributes:
        serializer_class (Serializer): The serializer class used for validating
                                       and serializing the DisbursementPlan data.
        permission_classes (list): A list of permission classes that a user must
                                   satisfy to access this view. `IsAuthenticated`
                                   ensures only logged-in users can access.

    Methods:
        get_object(): Overrides the default method to fetch or create the
                      DisbursementPlan instance for the current authenticated user.
    """
    serializer_class = DisbursementPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """
        Retrieves or creates the DisbursementPlan object for the current authenticated user.

        If a DisbursementPlan for the user does not exist, it will be created.

        Returns:
            DisbursementPlan: The DisbursementPlan instance belonging to
                              `self.request.user`.
        """
        return DisbursementPlan.objects.get_or_create(user = self.request.user)[0]

class TransactionListView(generics.ListAPIView):
    """
    API view to list all transactions for the authenticated user.

    This view provides a read-only endpoint (`GET`) to retrieve a list of
    Transaction instances. It ensures that users can only view their own
    transaction history, ordered by timestamp in descending order (most recent first).

    Attributes:
        serializer_class (Serializer): The serializer class used for validating
                                       and serializing the Transaction data.
        permission_classes (list): A list of permission classes that a user must
                                   satisfy to access this view. `IsAuthenticated`
                                   ensures only logged-in users can access.

    Methods:
        get_queryset(): Overrides the default method to filter transactions
                        by the current authenticated user and order them.
    """
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Retrieves the queryset of Transaction objects for the current authenticated user.

        The transactions are filtered by the user and ordered by their timestamp
        in descending order (most recent first).

        Returns:
            QuerySet: A queryset of Transaction instances belonging to
                      `self.request.user`.
        """
        return Transaction.objects.filter(user = self.request.user).order_by('-timestamp')