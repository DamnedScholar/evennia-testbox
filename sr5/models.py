"""
Models

This file contains custom database models.

"""

from django.db import models
from django.db.models import Q
import evennia
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


class Ledger(SharedMemoryModel):
    """
    The manager model for the account system.

    Instantiate this on another object with an owner (usually an object
    with a dbref, but it can be a string; whatever it is, it should be
    unique) and a currency name.
    """

    db_owner = models.CharField(max_length=80, db_index=True)
    db_currency = models.CharField(max_length=80)
    db_initial = models.DecimalField(default=0)
    db_value = models.DecimalField(default=0)
    db_accrued = models.DecimalField(default=0)
    db_date_created = models.DateTimeField('date created', editable=False,
                                           auto_now_add=True)

    log_max = 5

    def __str__(self):
        return self.display()

    def __unicode__(self):
        return unicode(self.display())

    def configure(self, owner, currencyName, initialValue=0):
        try:
            self.owner = owner.dbref
        except AttributeError:
            self.owner = owner
        self.currency = currencyName
        self.initial = initialValue
        self.value = initialValue
        self.accrued = initialValue

    def display(self):
        owner = evennia.search_object(searchdata=self.db_owner)[0]

        return "{}'s {} Ledger:\n" \
               "{} / {}".format(str(owner).title(), self.db_currency,
                                self.db_value, self.db_accrued)

    def record(self, value, reason):
        "Record the transaction and alter totals."
        owner = evennia.search_object(searchdata=self.owner)[0]

        # Update the current value, and if the transaction is positive add to
        # the running total.
        self.value += value
        if value > 0:
            self.accrued += value

        # Deposit entries in each of the log tables. AccountingLog is based on
        # SharedMemoryModel and thus cached for rapid retrieval of recent
        # entries, while Accounting Icetray is based on the Django model for
        # long-term storage of every entry ever.
        entry = AccountingLog()
        entry.owner = self.db_owner
        entry.currency = self.db_currency
        entry.value = value
        entry.reason = reason

        entry = AccountingIcetray(db_owner=self.db_owner,
                                  db_currency=self.db_currency,
                                  db_value=value,
                                  db_reason=reason)
        entry.save()

        # Retrieve the entries in the quick log, so that we can check how many
        # there are and drop old ones that go over the cap.
        quick_log_query = AccountingLog.objects.filter(
            db_owner__iexact=self.db_owner,
            db_currency__iexact=self.db_currency
        )
        output = "This is what I see:\n"

        i = 0
        for log in quick_log_query:
            text = "({}) {}: {} {} {}".format(i, log.db_owner, log.db_currency, log.db_value, log.db_reason)

            if i < len(quick_log_query) - self.log_max:
                log.delete()
                text += "<-- This is getting deleted."

            i += 1

            output += "{}\n".format(text)

        return output

    def ice(self):
        "Display all log entries for the owner."
        owner = evennia.search_object(searchdata=self.owner)[0]
        query = AccountingIcetray.objects.filter(
            db_owner__iexact=self.db_owner,
            db_currency__iexact=self.db_currency
        )

        for entry in query:
            owner.msg(entry.db_reason)

    def ice_all(self):
        "Display all log entries for everyone."
        owner = evennia.search_object(searchdata=self.owner)[0]
        query = AccountingIcetray.objects.all()

        for entry in query:
            owner.msg(entry.db_reason)

    def log(self):
        "Display quick log entries for the owner."
        owner = evennia.search_object(searchdata=self.owner)[0]
        query = AccountingLog.objects.filter(
            db_owner__iexact=self.db_owner,
            db_currency__iexact=self.db_currency
        )

        for entry in query:
            owner.msg(entry.reason)

    def log_all(self):
        "Display quick log entries for everyone."
        owner = evennia.search_object(searchdata=self.owner)[0]
        query = AccountingLog.objects.all()

        for entry in query:
            owner.msg(entry.reason)
