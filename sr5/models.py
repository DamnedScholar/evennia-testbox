"""
Models

This file contains custom database models.

"""

from decimal import Decimal
from django.db import models
from django.db.models import Q
import evennia
from evennia.utils.idmapper.models import SharedMemoryModel


class AccountingIcetray(models.Model):
    """
    The long-term storage log, using a Django DB model. This is not supposed to
    be called directly, but will be used by Ledger to offload old data that
    we don't want to cache.

    Attributes:
        db_key: The index of the log in the table.
        db_owner: The character who has gained, spent, or lost something.
        db_currency: The thing being tracked.
        db_value: How much of the thing was involved in the transaction?
        db_reason: The impetus behind the transaction.
        db_origin: Who or what caused the transaction, code-wise?
        db_date_created: The timestamp of the log.

    Methods:
        as_list(args): Receives any number of string arguments matching the
            names of the keys and returns a list of those values in order.
        display(): Shows the values of the current log entry.
    """

    db_key = models.AutoField(primary_key=True)
    db_owner = models.CharField(max_length=80, db_index=True)
    db_currency = models.CharField(max_length=80)
    db_value = models.DecimalField(default=0)
    db_reason = models.TextField(blank=True)
    db_origin = models.CharField(max_length=80)
    db_date_created = models.DateTimeField('date created', editable=False,
                                           auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('db_date_created',)

    def as_list(self, *args):
        "Take any number of field names and output the contents as a list."

        output = []
        for arg in args:
            if arg in ["key", "db_key"]:
                output.append(self.db_key)
            elif arg in ["owner", "db_owner"]:
                output.append(self.db_owner)
            elif arg in ["currency", "db_currency"]:
                output.append(self.db_currency)
            elif arg in ["value", "db_value"]:
                output.append(self.db_value)
            elif arg in ["reason", "db_reason"]:
                output.append(self.db_reason)
            elif arg in ["origin", "db_origin"]:
                output.append(self.db_origin)
            elif arg in ["date_created", "db_date_created", "date", "time",
                         "timestamp"]:
                output.append(self.db_date_created)

        return output

    def display(self, show_owner=False):
        "Display all information about each entry."
        if show_owner:
            owner = evennia.search_object(searchdata=self.db_owner)[0]
        origin = evennia.search_object(searchdata=self.db_origin)[0]

        return "{} | {} {} for {} | {} has {} {}" \
               "".format(self.db_date_created, self.db_value, self.db_currency,
                         self.db_reason, self.db_owner, self.db_accrued,
                         self.db_currency)


class AccountingLog(SharedMemoryModel):
    """
    Cached log entries for the top most recent transactions. These should be
    identical to the most recent AccountingIcetray entries for each person.

    Attributes:
        key: The index of the log in the table.
        owner: The character who has gained, spent, or lost something.
        currency: The thing being tracked.
        value: How much of the thing was involved in the transaction?
        reason: The impetus behind the transaction.
        origin: Who or what caused the transaction, code-wise?
        date_created: The timestamp of the log.

    Methods:
        as_list(args): Receives any number of string arguments matching the
            names of the keys and returns a list of those values in order.
        display(): Shows the values of the current log entry.
    """

    db_key = models.AutoField(primary_key=True)
    db_owner = models.CharField(max_length=80, db_index=True)
    db_currency = models.CharField(max_length=80)
    db_value = models.DecimalField(default=0)
    db_reason = models.TextField(blank=True)
    db_origin = models.CharField(max_length=80)
    db_date_created = models.DateTimeField('date created', editable=False,
                                           auto_now_add=True, db_index=True)

    class Meta:
        ordering = ('db_date_created',)

    def as_list(self, *args):
        "Take any number of field names and output the contents as a list."

        output = []
        for arg in args:
            if arg in ["key", "db_key"]:
                output.append(self.db_key)
            elif arg in ["owner", "db_owner"]:
                output.append(self.db_owner)
            elif arg in ["currency", "db_currency"]:
                output.append(self.db_currency)
            elif arg in ["value", "db_value"]:
                output.append(self.db_value)
            elif arg in ["reason", "db_reason"]:
                output.append(self.db_reason)
            elif arg in ["origin", "db_origin"]:
                output.append(self.db_origin)
            elif arg in ["date_created", "db_date_created", "date", "time",
                         "timestamp"]:
                output.append(self.db_date_created)

        return output

    def display(self, show_owner=False):
        if show_owner:
            owner = evennia.search_object(searchdata=self.db_owner)[0]
        origin = evennia.search_object(searchdata=self.db_origin)[0]

        return "{} | {} {} for {} | {}" \
               "".format(self.db_date_created, self.db_value, self.db_currency,
                         self.db_reason, self.db_accrued)


class Ledger(SharedMemoryModel):
    """
    The manager model for the account system.

    Instantiate this on another object with an owner (usually an object
    with a dbref, but it can be a string; whatever it is, it should be
    unique) and a currency name.

    Attributes:
        owner: The character whose resource is being tracked.
        currency: The thing being tracked.
        initial: How much of the thing was there in the beginning?
        value: How much of the thing is there now?
        accrued: How much of the thing has the character gained?
        date_created: The timestamp of the log.

        Methods:
            __str__()
            __unicode__(): Displays the status of the Ledger.

            configure(owner, currencyName, initialValue=0): Set up the values
                for the Ledger.
            display(): Returns the status of the Ledger.
            record(): Makes logs of a transaction on both log models and
                deletes the oldest AccountingLog transaction for this owner and
                currency.
            ice(): Returns a list of AccountingIcetray logs belonging to this
                Ledger.
            ice_all(): Returns a list of all AccountingIcetray logs.
            log(): Returns a list of AccountingLog logs belonging to this
                Ledger.
            log_all(): Returns a list of all AccountingLog logs.
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

    def record(self, value, reason, origin=""):
        "Record the transaction and alter totals."
        owner = evennia.search_object(searchdata=self.owner)[0]

        if not origin:
            origin = self.owner
        if isinstance(value, float):
            value = Decimal(value)

        # Update the current value, and if the transaction is positive add to
        # the running total.
        self.value += value
        if value > 0:
            self.accrued += value

        # Deposit entries in each of the log tables. AccountingLog is based on
        # SharedMemoryModel and thus cached for rapid retrieval of recent
        # entries, while Accounting Icetray is based on the Django model for
        # long-term storage of every entry ever.
        entry_log = AccountingLog()
        entry_log.owner = self.db_owner
        entry_log.currency = self.db_currency
        entry_log.value = value
        entry_log.reason = reason
        entry_log.origin = origin

        entry_ice = AccountingIcetray(db_owner=self.db_owner,
                                      db_currency=self.db_currency,
                                      db_value=value,
                                      db_reason=reason,
                                      db_origin=origin)
        entry_ice.save()

        # Retrieve the entries in the quick log, so that we can check how many
        # there are and drop old ones that go over the cap.
        quick_log_query = AccountingLog.objects.filter(
            db_owner__iexact=self.db_owner,
            db_currency__iexact=self.db_currency
        )

        i = 0
        for log in quick_log_query:
            i += 1
            if i < len(quick_log_query) - self.log_max:
                log.delete()    # Delete old logs over the max.

        return (entry_log, entry_ice)

    def ice(self):
        "Display all log entries for the owner."
        owner = evennia.search_object(searchdata=self.owner)[0]
        query = AccountingIcetray.objects.filter(
            db_owner__iexact=self.db_owner,
            db_currency__iexact=self.db_currency
        )
        output = []

        for entry in query:
            output.append(entry.as_list("date", "owner", "value", "currency",
                                        "reason", "origin"))

        return output

    def ice_all(self):
        "Display all log entries for everyone."
        owner = evennia.search_object(searchdata=self.owner)[0]
        query = AccountingIcetray.objects.all()
        output = []

        for entry in query:
            output.append(entry.as_list("date", "owner", "value", "currency",
                                        "reason", "origin"))

        return output

    def log(self):
        "Display quick log entries for the owner."
        owner = evennia.search_object(searchdata=self.owner)[0]
        query = AccountingLog.objects.filter(
            db_owner__iexact=self.db_owner,
            db_currency__iexact=self.db_currency
        )
        output = []

        for entry in query:
            output.append(entry.as_list("date", "owner", "value", "currency",
                                        "reason", "origin"))

        return output

    def log_all(self):
        "Display quick log entries for everyone."
        owner = evennia.search_object(searchdata=self.owner)[0]
        query = AccountingLog.objects.all()
        output = []

        for entry in query:
            output.append(entry.as_list("date", "owner", "value", "currency",
                                        "reason", "origin"))

        return output
