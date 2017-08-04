"""
Models

This file contains custom database models.

"""

from django.db import models
from evennia.utils.idmapper.models import SharedMemoryModel


class AccountingIcetray(models.Model):
    """
    The long-term storage log, using a Django DB model. This is not supposed to
    be called directly, but will be used by Ledger to offload old data that
    we don't want to cache.
    """

    db_key = models.AutoField(primary_key=True)
    db_owner = models.CharField(max_length=80, db_index=True)
    db_currency = models.CharField(max_length=80)
    db_value = models.DecimalField(default=0)
    db_reason = models.TextField(blank=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                           auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('db_date_created',)


class AccountingLog(SharedMemoryModel):
    """
    Cached log entries for the top most recent transactions. These should be
    identical to the most recent AccountingIcetray entries for each person.
    """

    db_key = models.AutoField(primary_key=True)
    db_owner = models.CharField(max_length=80, db_index=True)
    db_currency = models.CharField(max_length=80)
    db_value = models.DecimalField(default=0)
    db_reason = models.TextField(blank=True)
    db_date_created = models.DateTimeField('date created', editable=False,
                                           auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('db_date_created',)


class AccountingJournal(SharedMemoryModel):
    """
    The database-facing side of the account system.
    """

    db_owner = models.CharField(max_length=80, db_index=True)
    db_currency = models.CharField(max_length=80)
    db_initial = models.DecimalField(default=0)
    db_value = models.DecimalField(default=0)
    db_accrued = models.DecimalField(default=0)
    db_date_created = models.DateTimeField('date created', editable=False,
                                           auto_now_add=True)
