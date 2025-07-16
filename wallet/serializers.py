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
        Also creates a Wallet for the user.

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
        # Wallet.objects.create(user = user)
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
    """
    Serializer for handling the funding of a user's wallet.

    This serializer defines the expected input fields for a wallet funding operation
    (amount and a unique reference). It performs custom validation to ensure the
    reference is not duplicated and encapsulates the business logic for updating
    the wallet balance and creating a transaction record.

    Attributes:
        amount (DecimalField): The amount of money to fund the wallet.
                               Requires up to 12 digits total with 2 decimal places.
        reference (CharField): A unique string identifier for the funding transaction.
                               Maximum length of 64 characters.

    Methods:
        validate_reference(value): Custom validation to ensure the provided
                                   reference has not been used before.
        create(validated_data): Performs the actual wallet funding and transaction
                                creation logic after data validation.
    """
    amount = serializers.DecimalField(max_digits = 12, decimal_places = 2)
    reference = serializers.CharField(max_length = 64)

    def validate_reference(self, value):
        """
        Custom validation method for the 'reference' field.

        Checks if a transaction with the given reference already exists in the database.
        If a duplicate is found, a validation error is raised.

        Args:
            value (str): The reference string provided in the request.

        Raises:
            serializers.ValidationError: If the reference has already been used.

        Returns:
            str: The validated reference value if it is unique.
        """
        if Transaction.objects.filter(reference = value).exists():
            raise serializers.ValidationError("This reference has already been used.")
        return value

    def create(self, validated_data):
        """
        Performs the wallet funding operation and creates a new transaction record.

        This method is called after the serializer's data has been validated.
        It retrieves the authenticated user, updates their wallet balance,
        and creates a new 'fund' type transaction.

        Args:
            validated_data (dict): A dictionary containing the validated data
                                   (amount and reference) from the serializer.

        Returns:
            dict: A dictionary indicating the success of the operation.
                  (Note: The view typically handles the final HTTP Response).
        """
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
