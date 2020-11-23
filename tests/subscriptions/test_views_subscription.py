"""Tests for the django-flexible-subscriptions UserSubscription views."""
import pytest

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages import get_messages
from django.urls import reverse

from subscriptions import models

from ..factories import PlanCostLinkFactory


def create_subscription_plan(plan_name='1', plan_description='2'):
    """Creates and returns SubscriptionPlan instance."""
    return models.SubscriptionPlan.objects.create(
        plan_name=plan_name, plan_description=plan_description
    )


def create_plan_cost(plan=None, period=1, unit=models.MONTH, cost='1.00'):
    """Creates and returns PlanCost instance."""
    pc = models.PlanCost.objects.create(
        recurrence_period=period, recurrence_unit=unit, cost=cost
    )
    if plan:
        pc.plans.add(plan)
    return pc


# TODO: move to utils, rename create_user_subscription
def create_user_subscription(user, cost, sub_plan):
    """Creates and returns a UserSubscription instance."""
    return models.UserSubscription.objects.create(
        user=user, plan_cost=cost, subscription_plan=sub_plan)

# SubscriptionListView
# -----------------------------------------------------------------------------


@pytest.mark.django_db
def test_subscription_list_template(admin_client):
    """Tests for proper subscription_list template."""
    response = admin_client.get(reverse('dfs_subscription_list'))

    assert (
        'subscriptions/subscription_list.html' in [
            t.name for t in response.templates
        ]
    )


@pytest.mark.django_db
def test_subscription_list_403_if_not_authorized(client, django_user_model):
    """Tests for 403 error for subscription list if inadequate permissions."""
    django_user_model.objects.create_user(username='user', password='password')
    client.login(username='user', password='password')

    response = client.get(reverse('dfs_subscription_list'))

    assert response.status_code == 403


@pytest.mark.django_db
def test_subscription_list_200_if_authorized(client, django_user_model):
    """Tests 200 response for subscription list with adequate permissions."""
    # Retrieve proper permission, add to user, and login
    content = ContentType.objects.get_for_model(models.SubscriptionPlan)
    permission = Permission.objects.get(
        content_type=content, codename='subscriptions'
    )
    user = django_user_model.objects.create_user(
        username='user', password='password'
    )
    user.user_permissions.add(permission)
    client.login(username='user', password='password')

    response = client.get(reverse('dfs_subscription_list'))

    assert response.status_code == 200


@pytest.mark.django_db
def test_subscription_list_retrives_all_users(admin_client, django_user_model):
    """Tests that the list view retrieves all the subscriptions."""
    # Create subscriptons to retrieve
    user_1 = django_user_model.objects.create_user(
        username='user_1', password='password'
    )
    user_2 = django_user_model.objects.create_user(
        username='user_2', password='password'
    )
    user_3 = django_user_model.objects.create_user(
        username='user_3', password='password'
    )

    plan_cost = create_plan_cost(plan=create_subscription_plan())
    subscription_plan = create_subscription_plan()

    create_user_subscription(user_3, plan_cost, subscription_plan)
    create_user_subscription(user_1, plan_cost, subscription_plan)
    create_user_subscription(user_2, plan_cost, subscription_plan)

    response = admin_client.get(reverse('dfs_subscription_list'))

    assert len(response.context['users']) == 3
    assert response.context['users'][0].username == 'user_1'
    assert response.context['users'][1].username == 'user_2'
    assert response.context['users'][2].username == 'user_3'


# SubscriptionCreateView
# -----------------------------------------------------------------------------
@pytest.mark.django_db
def test_subscription_create_template(admin_client):
    """Tests for proper subscription_create template."""
    response = admin_client.get(reverse('dfs_subscription_create'))

    assert (
        'subscriptions/subscription_create.html' in [
            t.name for t in response.templates
        ]
    )


@pytest.mark.django_db
def test_subscription_create_403_if_not_authorized(client, django_user_model):
    """Tests 403 error for subscription create if inadequate permissions."""
    django_user_model.objects.create_user(username='user', password='password')
    client.login(username='user', password='password')

    response = client.get(reverse('dfs_subscription_create'))

    assert response.status_code == 403


@pytest.mark.django_db
def test_subscription_create_200_if_authorized(client, django_user_model):
    """Tests 200 response for subscription create with adequate permissions."""
    # Retrieve proper permission, add to user, and login
    content = ContentType.objects.get_for_model(models.SubscriptionPlan)
    permission = Permission.objects.get(
        content_type=content, codename='subscriptions'
    )
    user = django_user_model.objects.create_user(
        username='user', password='password'
    )
    user.user_permissions.add(permission)
    client.login(username='user', password='password')

    response = client.get(reverse('dfs_subscription_create'))

    assert response.status_code == 200


@pytest.mark.django_db
def test_subscription_create_and_success(admin_client, django_user_model):
    """Tests subscription creation and success message works as expected."""
    user_subscription_count = models.UserSubscription.objects.all().count()
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_plan_cost(plan=subscription_plan)
    post_data = {
        'user': user.id,
        'plan_cost': plan_cost.id,
        'subscription_plan': subscription_plan,
    }

    response = admin_client.post(
        reverse('dfs_subscription_create'),
        post_data,
        follow=True,
    )

    messages = list(get_messages(response.wsgi_request))

    assert models.UserSubscription.objects.all().count() == (
        user_subscription_count + 1
    )
    assert messages[0].tags == 'success'
    assert messages[0].message == 'User subscription successfully added'


# SubscriptionUpdateView
# -----------------------------------------------------------------------------
@ pytest.mark.django_db
def test_subscription_update_template(admin_client, django_user_model):
    """Tests for proper subscription_update template."""
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_plan_cost(plan=subscription_plan)
    user_subscription = create_user_subscription(
        user,
        plan_cost,
        subscription_plan
    )

    response = admin_client.get(
        reverse(
            'dfs_subscription_update',
            kwargs={'subscription_id': user_subscription.id}
        )
    )

    assert (
        'subscriptions/subscription_update.html' in [
            t.name for t in response.templates
        ]
    )


@ pytest.mark.django_db
def test_subscription_update_403_if_not_authorized(client, django_user_model):
    """Tests 403 error for subscription update if inadequate permissions."""
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_plan_cost(plan=subscription_plan)
    user_subscription = create_user_subscription(
        user,
        plan_cost,
        subscription_plan
    )

    django_user_model.objects.create_user(username='user', password='password')
    client.login(username='user', password='password')

    response = client.get(
        reverse(
            'dfs_subscription_update',
            kwargs={'subscription_id': user_subscription.id}
        )
    )

    assert response.status_code == 403


@ pytest.mark.django_db
def test_subscription_update_200_if_authorized(client, django_user_model):
    """Tests 200 response for subscription update with adequate permissions."""
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_plan_cost(plan=subscription_plan)
    user_subscription = create_user_subscription(
        user,
        plan_cost,
        subscription_plan
    )

    # Retrieve proper permission, add to user, and login
    content = ContentType.objects.get_for_model(models.SubscriptionPlan)
    permission = Permission.objects.get(
        content_type=content, codename='subscriptions'
    )
    user = django_user_model.objects.create_user(
        username='user', password='password'
    )
    user.user_permissions.add(permission)
    client.login(username='user', password='password')

    response = client.get(
        reverse(
            'dfs_subscription_update',
            kwargs={'subscription_id': user_subscription.id}
        )
    )

    assert response.status_code == 200


@ pytest.mark.django_db
def test_subscription_update_and_success(admin_client, django_user_model):
    """Tests that subscription update and success message works as expected."""
    # Setup initial tag for update

    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_plan_cost(plan=subscription_plan)
    # link = PlanCostLinkFactory(plan=subscription_plan, cost=plan_cost)

    user_subscription = create_user_subscription(
        user,
        plan_cost,
        subscription_plan
    )
    print('User Sub', user_subscription.plan_cost)
    print('Plan cost', plan_cost)
    user_subs_count = models.UserSubscription.objects.all().count()

    post_data = {
        'plan_cost': plan_cost.id,
        'subscription_plan': subscription_plan.id,
        'active': False,
    }
    url = reverse(
        'dfs_subscription_update',
        kwargs={'subscription_id': user_subscription.id}
    )
    response = admin_client.post(
        url,
        post_data,
        follow=True,
    )
    print('Response', response.content.decode())

    messages = list(get_messages(response.wsgi_request))

    assert messages[0].tags == 'success'
    assert messages[0].message == 'User subscription successfully updated'
    # assert models.UserSubscription.objects.all().count() == user_subs_count
    # assert models.UserSubscription.objects.last().active is False


# SubscriptionDeleteView
# -----------------------------------------------------------------------------
@ pytest.mark.django_db
def test_subscription_delete_template(admin_client, django_user_model):
    """Tests for proper subscription_delete template."""
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_plan_cost(plan=subscription_plan)
    user_subscription = create_user_subscription(
        user,
        plan_cost,
        subscription_plan
    )

    response = admin_client.get(
        reverse(
            'dfs_subscription_delete',
            kwargs={'subscription_id': user_subscription.id}
        )
    )

    assert (
        'subscriptions/subscription_delete.html' in [
            t.name for t in response.templates
        ]
    )


@ pytest.mark.django_db
def test_subscription_delete_403_if_not_authorized(client, django_user_model):
    """Tests 403 error for subscription delete if inadequate permissions."""
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_plan_cost(plan=subscription_plan)
    user_subscription = create_user_subscription(
        user,
        plan_cost,
        subscription_plan
    )

    django_user_model.objects.create_user(username='user', password='password')
    client.login(username='user', password='password')

    response = client.get(
        reverse(
            'dfs_subscription_delete',
            kwargs={'subscription_id': user_subscription.id}
        )
    )

    assert response.status_code == 403


@ pytest.mark.django_db
def test_subscription_delete_200_if_authorized(client, django_user_model):
    """Tests 200 response for subscription delete with adequate permissions."""
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_plan_cost(plan=subscription_plan)
    user_subscription = create_user_subscription(
        user,
        plan_cost,
        subscription_plan
    )

    # Retrieve proper permission, add to user, and login
    content = ContentType.objects.get_for_model(models.SubscriptionPlan)
    permission = Permission.objects.get(
        content_type=content, codename='subscriptions'
    )
    user = django_user_model.objects.create_user(
        username='user', password='password'
    )
    user.user_permissions.add(permission)
    client.login(username='user', password='password')

    response = client.get(
        reverse(
            'dfs_subscription_delete',
            kwargs={'subscription_id': user_subscription.id}
        )
    )

    assert response.status_code == 200


@ pytest.mark.django_db
def test_subscription_delete_and_success(admin_client, django_user_model):
    """Tests for success message on successful deletion."""
    user = django_user_model.objects.create_user(username='a', password='b')
    subscription_plan = create_subscription_plan()
    plan_cost = create_plan_cost(plan=subscription_plan)
    user_subscription = create_user_subscription(
        user,
        plan_cost,
        subscription_plan
    )
    subscription_count = models.UserSubscription.objects.all().count()

    response = admin_client.post(
        reverse(
            'dfs_subscription_delete',
            kwargs={'subscription_id': user_subscription.id}
        ),
        follow=True,
    )

    messages = list(get_messages(response.wsgi_request))

    assert models.UserSubscription.objects.all().count() == (
        subscription_count - 1
    )
    assert messages[0].tags == 'success'
    assert messages[0].message == 'User subscription successfully deleted'
