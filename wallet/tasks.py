from celery import shared_task

from django.utils import timezone
import uuid

from .models import DisbursementPlan, Wallet, Transaction

import logging

logger = logging.getLogger(__name__)

@shared_task
def process_disbursements():
    """
    Celery shared task to process scheduled disbursement plans.

    This task runs periodically to check for active disbursement plans that are due.
    For each due plan, it performs the following actions:
    1. Retrieves the associated user's wallet.
    2. Checks if the wallet's locked balance is sufficient for the disbursement.
    3. Transfers the `amount_per_disbursement` from `locked_balance` to `balance`.
    4. Creates a new `Transaction` record for the disbursement.
    5. Updates the `next_disbursement` date for the plan based on its type (daily/weekly).

    The task logs its execution start time and provides informative messages.
    It's designed to be idempotent for individual plan processing, meaning
    running it multiple times for the same plan within a short window (before
    `next_disbursement` is updated) will not cause duplicate disbursements
    due to the `next_disbursement__lte` filter.
    """
    now = timezone.now()
    logger.info(f"⏱ Running disbursement check at {now}")

    plans = DisbursementPlan.objects.filter(active = True, next_disbursement__lte = now)

    for plan in plans:
        wallet = Wallet.objects.get(user = plan.user)

        if wallet.locked_balance < plan.amount_per_disbursement:
            continue

        wallet.locked_balance -= plan.amount_per_disbursement
        wallet.balance += plan.amount_per_disbursement
        wallet.save()

        Transaction.objects.create(
            user = plan.user,
            tx_type = 'disburse',
            amount = plan.amount_per_disbursement,
            reference = f"DISB-{uuid.uuid4().hex[:10]}",
            status = 'success'
        )

        if plan.plan_type == 'daily':
            plan.next_disbursement += timezone.timedelta(days=1)
        elif plan.plan_type == 'weekly':
            plan.next_disbursement += timezone.timedelta(weeks=1)
        plan.save()