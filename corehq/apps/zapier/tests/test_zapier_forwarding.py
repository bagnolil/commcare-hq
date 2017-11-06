from __future__ import absolute_import
import uuid
from django.test import TestCase
from casexml.apps.case.mock import CaseBlock
from casexml.apps.case.util import post_case_blocks
from corehq.apps.zapier.consts import EventTypes
from corehq.apps.zapier.models import ZapierSubscription
from corehq.apps.zapier.tests.test_utils import bootrap_domain_for_zapier, cleanup_repeaters_for_domain, \
    cleanup_repeat_records_for_domain
from corehq.form_processor.tests.utils import run_with_all_backends
from corehq.motech.repeaters.models import RepeatRecord


DOMAIN = 'zapier-case-forwarding-tests'
ZAPIER_CASE_TYPE = 'animal'


class TestZapierCaseForwarding(TestCase):

    @classmethod
    def setUpClass(cls):
        super(TestZapierCaseForwarding, cls).setUpClass()
        cls.domain = DOMAIN
        cls.domain_object, cls.web_user, cls.api_key = bootrap_domain_for_zapier(cls.domain)

    @classmethod
    def tearDownClass(cls):
        cls.web_user.delete()
        cls.domain_object.delete()
        cleanup_repeaters_for_domain(cls.domain)
        super(TestZapierCaseForwarding, cls).tearDownClass()

    def tearDown(self):
        cleanup_repeat_records_for_domain(self.domain)
        ZapierSubscription.objects.all().delete()

    @run_with_all_backends
    def test_create_case_forwarding(self):
        self._run_test(EventTypes.NEW_CASE, 1, 1)

    @run_with_all_backends
    def test_update_case_forwarding(self):
        self._run_test(EventTypes.UPDATE_CASE, 0, 1)

    @run_with_all_backends
    def test_change_case_forwarding(self):
        self._run_test(EventTypes.CHANGED_CASE, 1, 2)

    @run_with_all_backends
    def test_case_forwarding_wrong_type(self):
        self._run_test(EventTypes.NEW_CASE, 0, 0, 'plant')

    @run_with_all_backends
    def test_update_case_forwarding_wrong_type(self):
        self._run_test(EventTypes.UPDATE_CASE, 0, 0, 'plant')

    @run_with_all_backends
    def test_change_case_forwarding_wrong_type(self):
        self._run_test(EventTypes.CHANGED_CASE, 0, 0, 'plant')

    def _run_test(self, event_type, expected_records_after_create, expected_records_after_update,
                  case_type=ZAPIER_CASE_TYPE):
        ZapierSubscription.objects.create(
            domain=self.domain,
            user_id=str(self.web_user._id),
            event_name=event_type,
            url='http://example.com/lets-make-some-cases/',
            case_type=ZAPIER_CASE_TYPE,
        )

        # create case and run checks
        case_id = uuid.uuid4().hex
        post_case_blocks(
            [
                CaseBlock(
                    create=True,
                    case_id=case_id,
                    case_type=case_type,
                ).as_xml()
            ], domain=self.domain
        )
        repeat_records = list(RepeatRecord.all(domain=self.domain))
        self.assertEqual(expected_records_after_create, len(repeat_records))
        for record in repeat_records:
            self.assertEqual(case_id, record.payload_id)

        # update case and run checks
        post_case_blocks(
            [
                CaseBlock(
                    create=False,
                    case_id=case_id,
                ).as_xml()
            ], domain=self.domain
        )
        repeat_records = list(RepeatRecord.all(domain=self.domain))
        self.assertEqual(expected_records_after_update, len(repeat_records))
        for record in repeat_records:
            self.assertEqual(case_id, record.payload_id)
