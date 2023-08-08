import logging
from ckan.common import _
import ckan.lib.helpers as h
from ckan.lib.mailer import mail_recipient, MailerException
from ckan.logic import get_action
from ckan.authz import is_sysadmin
import ckan.plugins.toolkit as toolkit

log = logging.getLogger(__name__)


def get_user_from_organization(organization):
    from ckan import model
    context = {'model': model, 'ignore_auth': True, 'session': model.Session}

    admin_list = get_action('member_list')(context, {'id': organization['id'], 'object_type': 'user', 'capacity': 'admin'})
    user_id = admin_list[0][0]
    return get_action('user_show')(context, data_dict={"id": user_id})


def send_organization_approved(organization):
    user_details = get_user_from_organization(organization)
    site_addr = toolkit.config['ckan.site_url']
    email = make_email_template('organization_approved', {
      "url_guide": site_addr + '/opas/avoimen-datan-opas',
      "url_user_guide": site_addr + '/opas/johdanto'
    })

    send_email_with_admin_copy(
        user_details['name'],
        user_details['email'],
        email['subject'],
        email['message'])


def send_organization_denied(organization, reason):
    user_details = get_user_from_organization(organization)
    site_addr = toolkit.config['ckan.site_url']
    email = make_email_template('organization_denied', {
      "reason": reason,
      "url_guide": site_addr + '/opas/avoimen-datan-opas',
      "url_user_guide": site_addr + '/opas/johdanto'
    })

    send_email_with_admin_copy(
        user_details['name'],
        user_details['email'],
        email['subject'],
        email['message'])


def send_new_organization_email_to_admin():
    site_addr = toolkit.config['ckan.site_url']

    email = make_email_template('admin_new_organization', {
      "ckan_admin_url": site_addr + '/data/ckan-admin/organization_management',
    })

    send_email(
        'admin',
        toolkit.config['ckanext.organizationapproval.admin_email'],
        email['subject'],
        email['message']
    )


def make_email_template(template, extra_vars):
    message = toolkit.render('emails/message/{0}.html'.format(template), extra_vars)
    subject = toolkit.render('emails/subject/{0}.txt'.format(template), extra_vars)
    return {'message': message, 'subject': subject}


def send_email(name, email, subject, message):
    log.debug('send_email(%s, %s, %s, %s)', name, email, subject, message)
    try:
        mail_recipient(
            name,
            email,
            subject,
            message,
            headers={'Content-Type': 'text/html; charset=UTF-8'}
        )
        h.flash_success(_("Successfully sent email notification"))
    except MailerException as e:
        # NOTE: MailerException happens in cypress.
        h.flash_error(_("Failed to send email notification"))
        log.error('Error sending email: %s', e)


def send_email_with_admin_copy(user_name, user_email, subject, message):
    send_email(user_name, user_email, subject, message)

    admin_email = toolkit.config.get('ckanext.organizationapproval.admin_email')
    if admin_email:
        send_email('Admin notifications', admin_email,
                   f'(sent to {user_name}) {subject}', message)


# May cause issues for unpatched CKANs, see https://github.com/ckan/ckan/issues/4597
@toolkit.chained_action
@toolkit.side_effect_free
def organization_list(original_action, context, data_dict):
    org_list = original_action(context, data_dict)

    model = context['model']
    user = context.get('user')

    # Early return for trivial cases and sysadmins
    if len(org_list) == 0 or (user and is_sysadmin(user)):
        return org_list

    # Find names of all non-approved organizations
    query = (model.Session.query(model.Group.name)
             .filter(model.Group.state == 'active')
             .filter(model.Group.approval_status != 'approved'))

    non_approved = set(result[0] for result in query.all())

    # If user is logged in, retain only names of organizations the user is not a member of
    if user:
        query = (model.Session.query(model.Group.name)
                 .join(model.Member, model.Member.group_id == model.Group.id)
                 .join(model.User, model.User.id == model.Member.table_id)
                 .filter(model.Member.state == 'active')
                 .filter(model.Member.table_name == 'user')
                 .filter(model.User.name == user)
                 .filter(model.Group.state == 'active')
                 .filter(model.Group.approval_status != 'approved'))
        memberships = set(result[0] for result in query.all())
        non_approved -= memberships

    # Filter the result list to exclude non-approved organizations the user is not a member of
    if isinstance(org_list[0], dict):
        return [o for o in org_list if o.get('name') not in non_approved]
    else:
        return [o for o in org_list if o not in non_approved]
