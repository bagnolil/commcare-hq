from __future__ import absolute_import
from django.core.management.base import BaseCommand

from corehq.apps.accounting.models import Currency
from corehq.apps.sms.models import INCOMING, OUTGOING
from corehq.apps.smsbillables.models import SmsGatewayFee, SmsGatewayFeeCriteria
from corehq.apps.smsbillables.utils import log_smsbillables_info
from corehq.messaging.smsbackends.unicel.models import SQLUnicelBackend


def bootstrap_unicel_gateway(apps):
    currency = (apps.get_model('accounting.Currency') if apps else Currency).objects.get(code="INR")
    sms_gateway_fee_class = apps.get_model('smsbillables.SmsGatewayFee') if apps else SmsGatewayFee
    sms_gateway_fee_criteria_class = apps.get_model('smsbillables.SmsGatewayFeeCriteria') if apps else SmsGatewayFeeCriteria

    SmsGatewayFee.create_new(SQLUnicelBackend.get_api_id(), INCOMING, 0.50,
                             currency=currency,
                             fee_class=sms_gateway_fee_class,
                             criteria_class=sms_gateway_fee_criteria_class)
    SmsGatewayFee.create_new(SQLUnicelBackend.get_api_id(), OUTGOING, 0.50,
                             currency=currency,
                             fee_class=sms_gateway_fee_class,
                             criteria_class=sms_gateway_fee_criteria_class)
    log_smsbillables_info("Updated Unicel gateway fees.")


class Command(BaseCommand):
    help = "bootstrap Unicel gateway fees"

    def handle(self, *args, **options):
        bootstrap_unicel_gateway(None)
