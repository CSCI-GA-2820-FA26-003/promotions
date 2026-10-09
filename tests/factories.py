"""
Test Factory to make fake objects for testing
"""

import random
from datetime import date, datetime, time, timedelta, timezone

import factory
from service.models import Promotions

PROMOTION_TYPES = [
    "discount",
    "2x1",
    "cross-selling",
    "free shipping",
    "free installment",
    "bundle deal",
    "cashback",
    "free gift",
    "loyalty points",
]

# campaign -> ((month, day) when it usually starts, typical length in days)
# None means the campaign can happen any time of year
CAMPAIGN_DATES = {
    "black friday":    ((11, 24), 4),
    "cyber monday":    ((11, 27), 2),
    "halloween":       ((10, 25), 7),
    "christmas":       ((12, 15), 10),
    "new year":        ((12, 28), 5),
    "valentine's day": ((2, 7), 8),
    "mother's day":    ((5, 1), 10),
    "back to school":  ((8, 15), 20),
    "spring sale":     ((3, 20), 30),
    "summer sale":     ((6, 21), 30),
    "flash sale":      None,
}

# List of campaigns
CAMPAIGNS = list(CAMPAIGN_DATES.keys())


def _start_for(campaign):
    """Return a start date near the campaign's season, in a recent or upcoming year.

    Seasonal campaigns start within 14 days of their usual date, in the
    previous, current, or next year. Campaigns with no fixed season (None)
    start anywhere from 120 days ago to 60 days from now.

    Args:
        campaign (str): A key from CAMPAIGN_DATES.

    Returns:
        datetime.date: The promotion's start date.
    """
    window = CAMPAIGN_DATES[campaign]
    if window is None:
        return date.today() + timedelta(days=random.randint(-120, 60))
    (month, day), _ = window
    year = date.today().year + random.choice([-1, 0, 0, 1])
    return date(year, month, day) + timedelta(days=random.randint(-14, 14))


def _length_for(campaign):
    """Return a campaign length in days, with wide variation.

    Seasonal campaigns vary by roughly +/-50% around their usual length
    (never below 1 day). Campaigns with no fixed season last 1 to 7 days.

    Args:
        campaign (str): A key from CAMPAIGN_DATES.

    Returns:
        int: The campaign length in days.
    """
    window = CAMPAIGN_DATES[campaign]
    if window is None:
        return random.randint(1, 7)
    usual = window[1]
    spread = max(1, usual // 2)
    return max(1, usual + random.randint(-spread, spread))


class PromotionsFactory(factory.Factory):
    """Creates fake promotions"""

    class Meta:  # pylint: disable=too-few-public-methods
        """Maps factory to data model"""

        model = Promotions

    product_id = factory.Sequence(lambda n: n + 1)
    promotion_id = factory.Sequence(lambda n: n + 1)
    promotion_description = factory.Faker("random_element", elements=PROMOTION_TYPES)
    campaign = factory.Faker("random_element", elements=CAMPAIGNS)

    # Dates are derived from the campaign so they make sense for its season
    start_date = factory.LazyAttribute(lambda o: _start_for(o.campaign))
    end_date = factory.LazyAttribute(
        lambda o: o.start_date + timedelta(days=_length_for(o.campaign))
    )

    # Status depends on the dates; running promotions may be switched off
    status = factory.LazyAttribute(
        lambda o: "scheduled"
        if o.start_date > date.today()
        else "expired"
        if o.end_date < date.today()
        else random.choices(["active", "inactive"], weights=[80, 20])[0]
    )

    final_price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)

    # Always created 1 to 30 days before the start date, at a random time of day
    created_at = factory.LazyAttribute(
        lambda o: datetime.combine(o.start_date, time(), tzinfo=timezone.utc)
        - timedelta(
            days=random.randint(1, 30),
            seconds=random.randint(0, 86399),
        )
    )