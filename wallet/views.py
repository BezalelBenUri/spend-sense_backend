from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, DateFilter, CharFilter

from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter
from rest_framework import status

from .models import Wallet, DisbursementPlan, Transaction
from .serializers import WalletSerializer, DisbursementPlanSerializer, TransactionSerializer, WalletFundSerializer
from .paystack import initialize_payment, verify_payment

import uuid

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

class TransactionFilter(FilterSet):
    start_date = DateFilter(field_name = 'timestamp', lookup_expr = 'gte')
    end_date = DateFilter(field_name = 'timestamp', lookup_expr = 'lte')
    tx_type = CharFilter(field_name = 'tx_type')
    status = CharFilter(field_name = 'status')

    class Meta:
        model = Transaction
        fields = ['tx_type', 'status', 'start_date', 'end_date']

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
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = TransactionFilter
    ordering_fields = ['timestamp', 'amount']
    ordering = ['-timestamp']

    def get_queryset(self):
        """
        Retrieves the queryset of Transaction objects for the current authenticated user.

        The transactions are filtered by the user and ordered by their timestamp
        in descending order (most recent first).

        Returns:
            QuerySet: A queryset of Transaction instances belonging to
                      `self.request.user`.
        """
        return Transaction.objects.filter(user = self.request.user)
    
class FundWalletView(APIView):
    """
    API view to handle funding of the authenticated user's wallet.

    This view allows an authenticated user to deposit funds into their digital wallet
    via an HTTP POST request. It utilizes a `WalletFundSerializer` to validate
    the incoming data (e.g., the amount to fund) and then processes the transaction.

    Permissions:
        - `IsAuthenticated`: Only authenticated (logged-in) users can access this endpoint.

    Methods:
        post(request):
            Handles the POST request to fund the wallet.
            - Takes the request data, which should include the amount to fund.
            - Validates the data using `WalletFundSerializer`.
            - If valid, calls the serializer's `save()` method to perform the funding logic.
            - Returns a success message with HTTP 200 OK status if funding is successful.
            - Returns validation errors with HTTP 400 Bad Request status if data is invalid.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handles the POST request to fund the user's wallet.

        Args:
            request (HttpRequest): The incoming HTTP request object, containing
                                   request data and user information.

        Returns:
            Response:
                - HTTP 200 OK with a success message if the wallet is funded.
                - HTTP 400 Bad Request with serializer errors if the input data is invalid.
        """
        serializer = WalletFundSerializer(data = request.data, context = {'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Wallet funded successfully."}, status = status.HTTP_200_OK)
        return Response(serializer.errors, status = status.HTTP_400_BAD_REQUEST)
    
class InitializePaystackPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        if not amount:
            return Response({"error": "Amount is required."}, status = status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(amount)
        except ValueError:
            return Response({"error": "Invalid amount format."}, status = status.HTTP_400_BAD_REQUEST)

        reference = str(uuid.uuid4())
        email = request.user.email
        try:
            response = initialize_payment(email = email, amount = amount, reference = reference)
            if response['status']:
                return Response({
                    "authorization_url": response['data']['authorization_url'],
                    "reference": response['data']['reference']
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": response['message']}, status = status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status = status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class VerifyPaystackPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reference = request.data.get("reference")
        if not reference:
            return Response({"error": "Reference is required."}, status=status.HTTP_400_BAD_REQUEST)

        response = verify_payment(reference)

        if not response.get("status"):
            # Handle unexpected error format
            return Response({"error": response.get("message") or response.get("error", "Unknown Paystack error.")}, status=status.HTTP_400_BAD_REQUEST)

        data = response.get("data", {})
        if data.get("status") != "success":
            return Response({"error": f"Payment not successful. Status: {data.get('status')}"}, status=status.HTTP_400_BAD_REQUEST)

        # Payment is valid
        amount = data['amount'] / 100
        user = request.user
        wallet, _ = Wallet.objects.get_or_create(user=user)
        wallet.balance += amount
        wallet.save()

        Transaction.objects.get_or_create(
            user=user,
            tx_type='fund',
            amount=amount,
            reference=reference,
            defaults={"status": "success"}
        )

        return Response({"message": "Payment verified and wallet funded."}, status=status.HTTP_200_OK)
