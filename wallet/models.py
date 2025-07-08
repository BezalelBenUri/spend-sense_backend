from django.db import models

from django.contrib.auth.models import AbstractUser

# Create your models here.
class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.

    This model customizes the default user behavior by:
    - Adding an `is_admin` boolean field to indicate administrative privileges.
    - Setting the `email` field as the primary unique identifier for authentication.
    - Making the `username` field optional and non-unique, while still being a required field
      during user creation (e.g., via `createsuperuser`).

    Attributes:
        is_admin (BooleanField): A boolean indicating if the user has administrative rights.
                                 Defaults to False.
        email (EmailField): The user's email address, used as the unique identifier for login.
                            Must be unique.
        username (CharField): The user's username. Can be blank and is not required to be unique.
                              It is, however, a required field when creating a user via Django's
                              management commands.

    Meta:
        USERNAME_FIELD (str): Specifies 'email' as the field to be used for authentication.
        REQUIRED_FIELDS (list): A list of field names that will be prompted for when creating
                                a user via `createsuperuser` command, in addition to the
                                `USERNAME_FIELD` and password.

    Methods:
        __str__(): Returns the user's email address, providing a human-readable representation
                   of the user object.
    """
    is_admin = models.BooleanField(default = False)
    email = models.EmailField(unique = True)
    username = models.CharField(max_length = 255, unique = False, blank = True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username'] 

    def __str__(self):
        """
        Returns the email address of the user.
        """
        return self.email

class Wallet(models.Model):
    """
    Represents a user's digital wallet, storing their balance and locked funds.

    Each user has a single wallet associated with their account.

    Attributes:
        user (OneToOneField): A one-to-one relationship to the `User` model.
                              If the user is deleted, the wallet is also deleted (CASCADE).
                              Allows access from User via `user_instance.wallet`.
        balance (DecimalField): The available balance in the wallet.
                                Stores up to 12 digits with 2 decimal places. Defaults to 0.00.
        locked_balance (DecimalField): Funds that are temporarily unavailable (e.g., pending
                                       transactions, held for disbursement).
                                       Stores up to 12 digits with 2 decimal places. Defaults to 0.00.
        created_at (DateTimeField): The timestamp when the wallet was created.
                                    Automatically set upon creation.
    """
    user = models.OneToOneField('User', on_delete = models.CASCADE, related_name = 'wallet')
    balance = models.DecimalField(max_digits = 12, decimal_places = 2, default = 0.00)
    locked_balance = models.DecimalField(max_digits = 12, decimal_places = 2, default = 0.00)
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        """
        Returns a string representation of the wallet, typically the user's email and balance.
        """
        return f"Wallet for {self.user.email} (Balance: {self.balance})"

class DisbursementPlan(models.Model):
    """
    Defines a plan for how a user's income or funds are disbursed (e.g., daily or weekly).

    Each user can have one disbursement plan.

    Attributes:
        PLAN_CHOICES (list): A list of tuples defining the available disbursement plan types:
                             'daily' and 'weekly'.
        user (OneToOneField): A one-to-one relationship to the `User` model.
                              If the user is deleted, the plan is also deleted (CASCADE).
        income_amount (DecimalField): The total income amount associated with this plan.
                                      Stores up to 12 digits with 2 decimal places.
        plan_type (CharField): The type of disbursement plan, chosen from `PLAN_CHOICES`.
                               e.g., 'daily' or 'weekly'.
        amount_per_disbursement (DecimalField): The amount of money disbursed in each interval.
                                                Stores up to 12 digits with 2 decimal places.
        active (BooleanField): A boolean indicating if the disbursement plan is currently active.
                               Defaults to True.
        next_disbursement (DateTimeField): The timestamp for the next scheduled disbursement.
        created_at (DateTimeField): The timestamp when the disbursement plan was created.
                                    Automatically set upon creation.
    """
    PLAN_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ]
    user = models.OneToOneField('User', on_delete = models.CASCADE)
    income_amount = models.DecimalField(max_digits = 12, decimal_places = 2)
    plan_type = models.CharField(max_length = 10, choices = PLAN_CHOICES)
    amount_per_disbursement = models.DecimalField(max_digits = 12, decimal_places = 2)
    active = models.BooleanField(default = True)
    next_disbursement = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add = True)

class Transaction(models.Model):
    """
    Records all financial transactions within the system.

    Each transaction is linked to a specific user and has a unique reference.

    Attributes:
        TRANSACTION_TYPE (list): A list of tuples defining the types of transactions:
                                 'fund' (Fund Wallet), 'disburse' (Daily/Weekly Disbursement),
                                 and 'withdraw' (Withdrawal to Bank).
        user (ForeignKey): A foreign key relationship to the `User` model.
                           If the user is deleted, their transactions are also deleted (CASCADE).
        tx_type (CharField): The type of transaction, chosen from `TRANSACTION_TYPE`.
                             e.g., 'fund', 'disburse', 'withdraw'.
        amount (DecimalField): The monetary amount involved in the transaction.
                               Stores up to 12 digits with 2 decimal places.
        timestamp (DateTimeField): The timestamp when the transaction occurred.
                                   Automatically set upon creation.
        reference (CharField): A unique identifier for the transaction.
                               Must be unique across all transactions.
        status (CharField): The current status of the transaction (e.g., "success").
                            Defaults to "success".
    """
    TRANSACTION_TYPE = [
        ('fund', 'Fund Wallet'),
        ('disburse', 'Daily/Weekly Disbursement'),
        ('withdraw', 'Withdrawal to Bank'),
    ]
    user = models.ForeignKey('User', on_delete = models.CASCADE)
    tx_type = models.CharField(max_length = 20, choices = TRANSACTION_TYPE)
    amount = models.DecimalField(max_digits = 12, decimal_places = 2)
    timestamp = models.DateTimeField(auto_now_add = True)
    reference = models.CharField(max_length = 64, unique = True)
    status = models.CharField(max_length = 20, default = "success")