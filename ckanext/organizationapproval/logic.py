import logging
from pylons import config
from ckan.common import _
import ckan.lib.helpers as h
from ckan.lib.mailer import mail_recipient, MailerException
from ckan.logic import get_action
from ckan.lib.base import render_jinja2

log = logging.getLogger(__name__)


def get_user_from_organization(organization):
    from ckan import model
    context = {'model': model, 'ignore_auth': True, 'session': model.Session}

    user_id = organization['users'][0]['id']
    return get_action('user_show')(context, data_dict={"id": user_id})


def send_organization_approved(organization):
    user_details = get_user_from_organization(organization)
    site_addr = config['ckan.site_url']
    email = make_email_template('organization_approved', {
      "url_guide": site_addr + '/opas/avoimen-datan-opas',
      "url_user_guide": site_addr + '/opas/johdanto'
    })

    send_email(
        user_details['name'],
        user_details['email'],
        email['subject'],
        email['message'])


def send_organization_denied(organization, reason):
    user_details = get_user_from_organization(organization)
    site_addr = config['ckan.site_url']
    email = make_email_template('organization_denied', {
      "reason": reason,
      "url_guide": site_addr + '/opas/avoimen-datan-opas',
      "url_user_guide": site_addr + '/opas/johdanto'
    })

    send_email(
        user_details['name'],
        user_details['email'],
        email['subject'],
        email['message'])


def send_new_organization_email_to_admin():
    site_addr = config['ckan.site_url']

    email = make_email_template('admin_new_organization', {
      "ckan_admin_url": site_addr + '/data/ckan-admin/organization_management',
    })

    send_email(
        'admin',
        config['ckanext.organizationapproval.admin_email'],
        email['subject'],
        email['message']
    )


def make_email_template(template, extra_vars):
    message = render_jinja2('emails/message/{0}.html'.format(template), extra_vars)
    subject = render_jinja2('emails/subject/{0}.txt'.format(template), extra_vars)
    return {'message': message, 'subject': subject}


def send_email(name, email, subject, message):
    try:
        mail_recipient(
            name,
            email,
            subject,
            message,
            {'Content-Type': 'text/html; charset=UTF-8'}
        )
        h.flash_success(_("Succesfully sent email notification"))
    except MailerException as e:
        # NOTE: MailerException happens in cypress.
        h.flash_error(_("Failed to send email notification"))
        log.error('Error sending email: %s', e)
