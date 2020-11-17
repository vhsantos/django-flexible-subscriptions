"""Tests for the _manager module."""
from datetime import datetime
from unittest.mock import patch

import pytest
from django.contrib.auth.models import Group
from subscriptions import models
from subscriptions.management.commands import _manager
from tests.subscriptions import test_forms

pytestmark = pytest.mark.django_db  # pylint: disable=invalid-name

# TODO: remove commented out code.
# TODO: views.py 860 - fix failing tests?
# TODO: rename to create_cost to create_plan_cost
# TODO: Move functions to utils and import


def create_cost(subscription_plan):
    """Creates and returns a PlanCost instance."""
    # TODO: rm commented out code
    # plan = models.SubscriptionPlan.objects.create(
    #     plan_name='Test Plan',
    #     plan_description='This is a test plan',
    #     group=group
    # )

    return test_forms.create_cost(
        plan=subscription_plan,
        period=1,
        unit=models.MONTH,
        cost='1.00',
    )


def create_subscription_plan(group=None):
    return models.SubscriptionPlan.objects.create(
        plan_name='Test Plan',
        plan_description='This is a test plan',
        group=group
    )


def create_due_user_subscription(user, group=None):
    """Creates a standard UserSubscription object due for billing."""
    subscription_plan = create_subscription_plan(group)
    cost = create_cost(subscription_plan)

    return models.UserSubscription.objects.create(
        user=user,
        plan_cost=cost,
        subscription_plan=subscription_plan,
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=None,
        date_billing_last=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_next=datetime(2018, 2, 1, 1, 1, 1),
        active=True,
        cancelled=False,
    )


def test_manager_process_expired_single_group(django_user_model):
    """Tests handling expiry with user with single group."""
    user = django_user_model.objects.create_user(username='a', password='b')
    group = Group.objects.create(name='test')
    group.user_set.add(user)
    user_count = group.user_set.all().count()

    subscription_plan = create_subscription_plan(group)
    cost = create_cost(subscription_plan)
    user_subscription = models.UserSubscription.objects.create(
        user=user,
        plan_cost=cost,
        subscription_plan=cost.plans.all()[0],
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=datetime(2018, 12, 1, 1, 1, 1),
        date_billing_next=None,
        active=True,
        cancelled=False,
    )

    user_subscription_id = user_subscription.id
    manager = _manager.Manager()
    manager.process_expired(user_subscription)
    user_subscription = models.UserSubscription.objects.get(
        id=user_subscription_id)

    assert group.user_set.all().count() == user_count - 1
    assert user_subscription.active is False
    assert user_subscription.cancelled is True


def test_manager_process_expired_multiple_different_groups(django_user_model):
    """Tests handling expiry with user with multiple different groups."""
    user = django_user_model.objects.create_user(username='a', password='b')

    group_1 = Group.objects.create(name='test_1')
    group_1.user_set.add(user)
    user_count_1 = group_1.user_set.all().count()
    subscription_plan_1 = create_subscription_plan(group_1)
    plan_cost_1 = create_cost(subscription_plan_1)

    user_subscription_1 = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost_1,
        subscription_plan=plan_cost_1.plans.all()[0],
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=datetime(2018, 12, 1, 1, 1, 1),
        date_billing_next=None,
        active=True,
        cancelled=False,
    )

    group_2 = Group.objects.create(name='test_2')
    group_2.user_set.add(user)
    user_count_2 = group_1.user_set.all().count()
    subscription_plan_2 = create_subscription_plan(group_2)
    plan_cost_2 = create_cost(subscription_plan_2)

    user_subscription_2 = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost_2,
        subscription_plan=plan_cost_2.plans.all()[0],
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=datetime(2018, 12, 1, 1, 1, 1),
        date_billing_next=None,
        active=True,
        cancelled=False,
    )

    manager = _manager.Manager()
    manager.process_expired(user_subscription_1)

    user_subscription_2_id = user_subscription_2.id
    user_subscription_1_id = user_subscription_1.id

    user_subscription_1 = models.UserSubscription.objects.get(
        id=user_subscription_1_id)
    user_subscription_2 = models.UserSubscription.objects.get(
        id=user_subscription_2_id)

    assert group_1.user_set.all().count() == user_count_1 - 1
    assert group_2.user_set.all().count() == user_count_2
    assert user_subscription_1.active is False
    assert user_subscription_1.cancelled is True
    assert user_subscription_2.active is True
    assert user_subscription_2.cancelled is False


def test_manager_process_expired_multiple_same_groups(django_user_model):
    """Tests handling expiry with user with multiple same groups."""
    user = django_user_model.objects.create_user(username='a', password='b')
    group = Group.objects.create(name='test_1')
    user_count = group.user_set.all().count()

    subscription_plan_1 = create_subscription_plan(group)
    plan_cost_1 = create_cost(subscription_plan_1)
    user_subscription_1 = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost_1,
        subscription_plan=subscription_plan_1,
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=datetime(2018, 12, 1, 1, 1, 1),
        date_billing_next=None,
        active=True,
        cancelled=False,
    )

    subscription_plan_2 = create_subscription_plan(group)
    plan_cost_2 = create_cost(subscription_plan_2)
    user_subscription_2 = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost_2,
        subscription_plan=subscription_plan_2,
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=datetime(2018, 12, 1, 1, 1, 1),
        date_billing_next=None,
        active=True,
        cancelled=False,
    )

    manager = _manager.Manager()
    manager.process_expired(user_subscription_1)

    user_subscription_1_id = user_subscription_1.id
    user_subscription_2_id = user_subscription_2.id

    user_subscription_1 = models.UserSubscription.objects.get(
        id=user_subscription_1_id)
    user_subscription_2 = models.UserSubscription.objects.get(
        id=user_subscription_2_id)

    assert group.user_set.all().count() == user_count
    assert user_subscription_1.active is False
    assert user_subscription_1.cancelled is True
    assert user_subscription_2.active is True
    assert user_subscription_2.cancelled is False


def test_manager_process_new_with_group(django_user_model):
    """Tests processing of new subscription with group."""
    user = django_user_model.objects.create_user(username='a', password='b')
    group = Group.objects.create(name='test')
    user_count = group.user_set.all().count()

    subscription_plan = create_subscription_plan(group)
    plan_cost = create_cost(subscription_plan)
    user_subscription = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost,
        subscription_plan=subscription_plan,
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=datetime(2018, 12, 1, 1, 1, 1),
        date_billing_next=None,
        active=False,
        cancelled=False,
    )

    manager = _manager.Manager()
    manager.process_new(user_subscription)

    user_subscription_id = user_subscription.id
    user_subscription = models.UserSubscription.objects.get(
        id=user_subscription_id)

    assert group.user_set.all().count() == user_count + 1
    assert user_subscription.active is True
    assert user_subscription.cancelled is False


def test_manager_process_new_without_group(django_user_model):
    """Tests processing of new subscription without group."""
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_cost(subscription_plan)
    user_subscription = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost,
        subscription_plan=subscription_plan,
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=datetime(2018, 12, 1, 1, 1, 1),
        date_billing_next=None,
        active=False,
        cancelled=False,
    )

    manager = _manager.Manager()
    manager.process_new(user_subscription)

    user_subscription_id = user_subscription.id
    user_subscription = models.UserSubscription.objects.get(
        id=user_subscription_id)

    assert user_subscription.active is True
    assert user_subscription.cancelled is False


def test_manager_process_new_next_date(django_user_model):
    """Tests that next billing date uses billing start date."""
    user = django_user_model.objects.create_user(username='a', password='b')
    group = Group.objects.create(name='test')

    subscription_plan = create_subscription_plan(group)
    plan_cost = create_cost(subscription_plan)
    user_subscription = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost,
        subscription_plan=subscription_plan,
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=None,
        date_billing_last=None,
        date_billing_next=datetime(2018, 1, 1, 1, 1, 1),
        active=False,
        cancelled=False,
    )

    manager = _manager.Manager()
    manager.process_new(user_subscription)

    user_subscription_id = user_subscription.id
    user_subscription = models.UserSubscription.objects.get(
        id=user_subscription_id)
    next_date = datetime(2018, 1, 31, 11, 30, 0, 520000)

    assert user_subscription.date_billing_next == next_date


@patch(
    'subscriptions.management.commands._manager.Manager.process_payment',
    lambda self, **kwargs: False
)
def test_manager_process_new_payment_error(django_user_model):
    """Tests handlig of new subscription payment error."""
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_cost(subscription_plan)
    user_subscription = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost,
        subscription_plan=subscription_plan,
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=datetime(2018, 12, 1, 1, 1, 1),
        date_billing_next=None,
        active=False,
        cancelled=False,
    )

    manager = _manager.Manager()
    manager.process_new(user_subscription)

    user_subscription_id = user_subscription.id
    user_subscription = models.UserSubscription.objects.get(
        id=user_subscription_id)

    assert user_subscription.date_billing_next is None
    assert user_subscription.active is False
    assert user_subscription.cancelled is False


@patch(
    'subscriptions.management.commands._manager.timezone.now',
    lambda: datetime(2018, 2, 1, 2, 2, 2)
)
def test_manager_process_due_billing_dates(django_user_model):
    """Tests that last and next billing dates are updated properly.

        Patching the timezone module to ensure consistent test results.
    """
    user = django_user_model.objects.create_user(username='a', password='b')
    user_subscription = create_due_user_subscription(user)
    user_subscription_id = user_subscription.id

    manager = _manager.Manager()
    manager.process_due(user_subscription)

    user_subscription = models.UserSubscription.objects.get(
        id=user_subscription_id)
    next_date = datetime(2018, 3, 3, 11, 30, 0, 520000)

    assert user_subscription.date_billing_next == next_date
    assert user_subscription.date_billing_last == datetime(2018, 2, 1, 2, 2, 2)


@patch(
    'subscriptions.management.commands._manager.Manager.process_payment',
    lambda self, **kwargs: False
)
def test_manager_process_due_payment_error(django_user_model):
    """Tests handling of due subscription payment error."""
    user = django_user_model.objects.create_user(username='a', password='b')
    user_subscription = create_due_user_subscription(user)
    user_subscription_id = user_subscription.id

    manager = _manager.Manager()
    manager.process_due(user_subscription)

    user_subscription = models.UserSubscription.objects.get(
        id=user_subscription_id)

    assert user_subscription.date_billing_last == datetime(2018, 1, 1, 1, 1, 1)
    assert user_subscription.date_billing_next == datetime(2018, 2, 1, 1, 1, 1)


@patch(
    'subscriptions.management.commands._manager.timezone.now',
    lambda: datetime(2019, 1, 1)
)
def test_manager_process_subsriptions_with_expired(django_user_model):
    """Tests that process_susbscriptions processes expiries."""
    user = django_user_model.objects.create_user(username='a', password='b')
    group = Group.objects.create(name='test')
    group.user_set.add(user)
    user_count = group.user_set.all().count()

    subscription_plan = create_subscription_plan(group)
    plan_cost = create_cost(subscription_plan)
    user_subscription = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost,
        subscription_plan=subscription_plan,
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=datetime(2018, 12, 1, 1, 1, 1),
        date_billing_next=None,
        active=True,
        cancelled=False,
    )

    manager = _manager.Manager()
    manager.process_subscriptions()

    user_subscription_id = user_subscription.id
    user_subscription = models.UserSubscription.objects.get(
        id=user_subscription_id)

    assert group.user_set.all().count() == user_count - 1
    assert user_subscription.active is False
    assert user_subscription.cancelled is True


@patch(
    'subscriptions.management.commands._manager.timezone.now',
    lambda: datetime(2018, 1, 2)
)
def test_manager_process_subscriptions_with_new(django_user_model):
    """Tests processing of new subscription via process_subscriptions."""
    user = django_user_model.objects.create_user(username='a', password='b')
    group = Group.objects.create(name='test')
    user_count = group.user_set.all().count()

    subscription_plan = create_subscription_plan(group)
    plan_cost = create_cost(subscription_plan)
    user_subscription = models.UserSubscription.objects.create(
        user=user,
        plan_cost=plan_cost,
        subscription_plan=subscription_plan,
        date_billing_start=datetime(2018, 1, 1, 1, 1, 1),
        date_billing_end=datetime(2018, 12, 31, 1, 1, 1),
        date_billing_last=None,
        date_billing_next=None,
        active=False,
        cancelled=False,
    )
    print('User Subscription:', user_subscription.subscription_plan.group)
    print('Group:', dir(group))
    subscription_id = user_subscription.id
    print('User Subscription Look Up', group.user_set.all())

    manager = _manager.Manager()
    manager.process_subscriptions()

    user_subscription = models.UserSubscription.objects.get(id=subscription_id)
    assert group.user_set.all().count() == user_count + 1
    assert user_subscription.active is True
    assert user_subscription.cancelled is False


@patch(
    'subscriptions.management.commands._manager.timezone.now',
    lambda: datetime(2018, 12, 2)
)
def test_manager_process_subscriptions_with_due(django_user_model):
    """Tests processing of subscriptions with billing due."""
    user = django_user_model.objects.create_user(username='a', password='b')
    group = Group.objects.create(name='test')
    user_count = group.user_set.all().count()

    user_subscription = create_due_user_subscription(user, group=group)
    user_subscription_id = user_subscription.id

    manager = _manager.Manager()
    manager.process_subscriptions()

    user_subscription = models.UserSubscription.objects.get(
        id=user_subscription_id)

    assert group.user_set.all().count() == user_count
    assert user_subscription.active is True
    assert user_subscription.cancelled is False


@patch(
    'subscriptions.management.commands._manager.timezone.now',
    lambda: datetime(2018, 1, 1, 1, 1, 1)
)
def test_manager_record_transaction_without_date(django_user_model):
    """Tests handling of record_transaction without providing a date.

        Patching the timezone module to ensure consistent test results.
    """
    transaction_count = models.SubscriptionTransaction.objects.all().count()

    user = django_user_model.objects.create_user(username='a', password='b')
    user_subscription = create_due_user_subscription(user)

    manager = _manager.Manager()
    transaction = manager.record_transaction(user_subscription)

    assert models.SubscriptionTransaction.objects.all().count() == (
        transaction_count + 1
    )
    assert transaction.date_transaction == datetime(2018, 1, 1, 1, 1, 1)


def test_manager_record_transaction_with_date(django_user_model):
    """Tests handling of record_transaction with date provided."""
    transaction_count = models.SubscriptionTransaction.objects.all().count()

    user = django_user_model.objects.create_user(username='a', password='b')
    user_subscription = create_due_user_subscription(user)
    transaction_date = datetime(2018, 1, 2, 1, 1, 1)

    manager = _manager.Manager()
    transaction = manager.record_transaction(
        user_subscription,
        transaction_date
    )

    assert models.SubscriptionTransaction.objects.all().count() == (
        transaction_count + 1
    )
    assert transaction.date_transaction == transaction_date
