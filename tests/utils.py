from subscriptions import models


def create_cost(plan=None, period=1, unit=models.MONTH, cost='1.00'):
    """Creates and returns PlanCost instance."""
    pc = models.PlanCost.objects.create(
        recurrence_period=period, recurrence_unit=unit, cost=cost
    )
    if plan:
        pc.plans.add(plan)
    return pc
