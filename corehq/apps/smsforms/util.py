from __future__ import absolute_import
from corehq.apps.receiverwrapper.util import submit_form_locally
from dimagi.utils.couch import CriticalSection


def form_requires_input(form):
    """
    Returns True if the form has at least one question that requires input
    """
    for question in form.get_questions([]):
        if question["tag"] not in ("trigger", "label", "hidden"):
            return True

    return False


def process_sms_form_complete(session, form, completed=True):
    result = submit_form_locally(form, session.domain,
        app_id=session.app_id, partial_submission=not completed)
    session.end(completed=completed)
    session.submission_id = result.xform.form_id
    session.save()


def critical_section_for_smsforms_sessions(contact_id):
    return CriticalSection(['smsforms-sessions-lock-for-contact-%s' % contact_id], timeout=5 * 60)
