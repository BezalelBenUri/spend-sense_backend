from celery import shared_task

from django.utils import timezone
import uuid

from .models import DisbursementPlan, Wallet, Transaction

import logging

logger = logging.getLogger(__name__)

@shared_task
def process_disbursements():
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