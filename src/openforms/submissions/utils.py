import logging
from typing import Any

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.mail import send_mail

from openforms.appointments.models import AppointmentInfo
from openforms.appointments.utils import get_client

from .constants import SUBMISSIONS_SESSION_KEY, UPLOADS_SESSION_KEY
from .models import Submission, TemporaryFileUpload

logger = logging.getLogger(__name__)


def append_to_session_list(session: SessionBase, session_key: str, value: Any) -> None:
    # note: possible race condition with concurrent requests
    active = session.get(session_key, [])
    if value not in active:
        active.append(value)
        session[session_key] = active


def remove_from_session_list(
    session: SessionBase, session_key: str, value: Any
) -> None:
    # note: possible race condition with concurrent requests
    active = session.get(session_key, [])
    if value in active:
        active.remove(value)
        session[session_key] = active


def add_submmission_to_session(submission: Submission, session: SessionBase) -> None:
    """
    Store the submission UUID in the request session for authorization checks.
    """
    append_to_session_list(session, SUBMISSIONS_SESSION_KEY, str(submission.uuid))


def remove_submission_from_session(
    submission: Submission, session: SessionBase
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    remove_from_session_list(session, SUBMISSIONS_SESSION_KEY, str(submission.uuid))


def add_upload_to_session(upload: TemporaryFileUpload, session: SessionBase) -> None:
    """
    Store the upload UUID in the request session for authorization checks.
    """
    append_to_session_list(session, UPLOADS_SESSION_KEY, str(upload.uuid))


def remove_upload_from_session(
    upload: TemporaryFileUpload, session: SessionBase
) -> None:
    """
    Remove the submission UUID from the session if it's present.
    """
    remove_from_session_list(session, UPLOADS_SESSION_KEY, str(upload.uuid))


def remove_submission_uploads_from_session(
    submission: Submission, session: SessionBase
) -> None:
    for attachment in submission.get_attachments().filter(temporary_file__isnull=False):
        remove_upload_from_session(attachment.temporary_file, session)


def send_confirmation_email(submission: Submission):
    email_template = submission.form.confirmation_email_template

    to_emails = submission.get_email_confirmation_recipients(submission.data)
    if not to_emails:
        logger.warning(
            "Could not determine the recipient e-mail address for submission %d, "
            "skipping the confirmation e-mail.",
            submission.id,
        )
        return

    content = email_template.render(submission)

    if hasattr(submission, "appointment_info"):
        client = get_client()
        content += client.get_appointment_details_html(
            submission.appointment_info.appointment_id
        )
        content += client.get_appointment_links_html(submission)

    send_mail(
        email_template.subject,
        content,
        settings.DEFAULT_FROM_EMAIL,  # TODO: add config option to specify sender e-mail
        to_emails,
        fail_silently=False,
        html_message=content,
    )
