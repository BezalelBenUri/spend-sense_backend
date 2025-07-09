from rest_framework import serializers

from .models import User, Wallet, DisbursementPlan, Transaction

class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model, used for reading and representing user data.

    This serializer exposes the 'id', 'email', 'username', and 'is_admin' fields
    of the User model. It is typically used when retrieving user information
    and does not include sensitive fields like 'password'.

    Attributes:
        Meta (class): Inner class defining metadata options for the serializer.
            model (Model): The Django model that this serializer will serialize.
            fields (list): A list of field names from the model to be included
                           in the serialized representation.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'is_admin']

class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new User instances, specifically for user registration.

    This serializer handles the creation of new users, including the secure handling
    of passwords by marking the 'password' field as write-only and using Django's
    `create_user` method for proper password hashing.

    Attributes:
        Meta (class): Inner class defining metadata options for the serializer.
            model (Model): The Django model that this serializer will serialize.
            fields (list): A list of field names from the model to be included
                           in the serialized representation.
            extra_kwargs (dict): A dictionary to specify additional options for
                                 individual fields. Here, 'password' is set to
                                 'write_only' to prevent it from being returned
                                 in API responses.

    Methods:
        create(validated_data): Overrides the default create method to use
                                `User.objects.create_user`, ensuring passwords
                                are correctly hashed before saving.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        """
        Creates and returns a new `User` instance, given the validated data.

        This method ensures that the password is properly hashed using Django's
        built-in `create_user` method.

        Args:
            validated_data (dict): A dictionary containing the validated data
                                   for creating a user (email, username, password).

        Returns:
            User: The newly created User instance.
        """
        user = User.objects.create_user(
            email = validated_data['email'],
            username = validated_data.get('username', ''),
            password = validated_data['password']
        )
        return user

class WalletSerializer(serializers.ModelSerializer):
    """
    Serializer for the Wallet model.

    This serializer is used to represent a user's digital wallet, exposing
    its balance, locked balance, and creation timestamp.

    Attributes:
        Meta (class): Inner class defining metadata options for the serializer.
            model (Model): The Django model that this serializer will serialize.
            fields (list): A list of field names from the model to be included
                           in the serialized representation.
    """
    class Meta:
        model = Wallet
        fields = ['balance', 'locked_balance', 'created_at']

class DisbursementPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for the DisbursementPlan model.

    This serializer represents a user's financial disbursement plan,
    including details like income amount, plan type, disbursement amount,
    activity status, and next disbursement date.

    Attributes:
        Meta (class): Inner class defining metadata options for the serializer.
            model (Model): The Django model that this serializer will serialize.
            fields (list): A list of field names from the model to be included
                           in the serialized representation.
    """
    class Meta:
        model = DisbursementPlan
        fields = [
            'id',
            'income_amount',
            'plan_type',
            'amount_per_disbursement',
            'active',
            'next_disbursement',
            'created_at'
        ]

class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Transaction model.

    This serializer is used to represent financial transactions within the system,
    providing details such as transaction type, amount, timestamp, reference, and status.

    Attributes:
        Meta (class): Inner class defining metadata options for the serializer.
            model (Model): The Django model that this serializer will serialize.
            fields (list): A list of field names from the model to be included
                           in the serialized representation.
    """
    class Meta:
        model = Transaction
        fields = [
            'id',
            'tx_type',
            'amount',
            'timestamp',
            'reference',
            'status'
        ]

class WalletFundSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits = 12, decimal_places = 2)
    reference = serializers.CharField(max_length = 64)

    def validate_reference(self, value):
        if Transaction.objects.filter(reference = value).exists():
            raise serializers.ValidationError("This reference has already been used.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        amount = validated_data['amount']
        reference = validated_data['reference']

        # Update wallet
        wallet, created = Wallet.objects.get_or_create(user = user)
        wallet.balance += amount
        wallet.save()

        # Create transaction
        Transaction.objects.create(
            user = user,
            tx_type = 'fund',
            amount = amount,
            reference = reference,
            status = 'success'
        )
        return {"message": "Wallet funded successfully."}
