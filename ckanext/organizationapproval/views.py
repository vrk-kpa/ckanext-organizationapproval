from flask import Blueprint, request
from ckan.plugins import toolkit
from ckan import model
from math import ceil
import logging
from .logic import send_organization_approved, send_organization_denied
from .utils import organization_generator

log = logging.getLogger(__name__)
_ = toolkit._


organizationapproval = Blueprint('organizationapproval', __name__)


def get_blueprint():
    return [organizationapproval]


@organizationapproval.route('/ckan-admin/organization_management', methods=['GET', 'POST'])
def manage_organizations():
    '''
    A ckan-admin page to list and add showcase admin users.
    '''
    context = {'model': model, 'session': model.Session,
               'user': toolkit.c.user or toolkit.c.author}

    try:
        toolkit.check_access('sysadmin', context, {})
    except toolkit.NotAuthorized:
        toolkit.abort(401, _('User not authorized to view page'))

    # Approving, deleting or denying organizations.
    if request.method == 'POST':
        org_id = request.form['org_id']
        approval_status = request.form['approval_status']
        # NOTE: should the possible statuses come from somewhere else?
        possible_statuses = ['approved', 'pending', 'denied']
        if approval_status in possible_statuses:
            log.debug('Valid approval status')
            data_dict = {'id': org_id,
                         'include_users': False,
                         'include_dataset_count': False,
                         'include_groups': False,
                         'include_tags': False,
                         'include_followers': False}
            organization = toolkit.get_action('organization_show')(context, data_dict)
            if organization['approval_status'] != approval_status:
                organization['approval_status'] = approval_status
                toolkit.get_action('organization_patch')(context, organization)
                if approval_status == 'approved':
                    send_organization_approved(organization)
                elif approval_status == 'denied':
                    reason = request.form['deny-reason']
                    send_organization_denied(organization, reason)
                toolkit.h.flash_success(_("Organization was successfully updated"))
            else:
                toolkit.h.flash_error(_("Status is already set to '%s'") % approval_status)
        else:
            toolkit.h.flash_error(_("Status not allowed"))

    # NOTE: This might cause slowness, get's all organizations and they are filtered later.
    # Organization list action doesn't support sorting by any field.
    # Maybe would be better to build a custom action for this case.
    organization_list = list(organization_generator(context, {"all_fields": True}))

    page_num = 1
    per_page = 50.0

    # Total number of pages of organizations
    total_pages = int(ceil(len(organization_list) / per_page))

    if 'page' in request.args:
        page_num = int(request.args['page'])

    # Return 20 most recently added organizations
    organization_data = sorted(organization_list, key=lambda x: (x['approval_status'], x['created']), reverse=True)[
        (int(per_page) * (page_num - 1)):(int(per_page) * page_num)
    ]

    return toolkit.render('admin/manage_organizations.html', extra_vars={
        'current_page': page_num,
        'total_pages': total_pages,
        'organization_data': organization_data
    })


# FIXME: Disabled, pending AV-1548
# @organizationapproval.route('/organization/edit/{id}', methods=['GET', 'POST'])
def ask_reapproval(id, data=None, errors=None, error_summary=None):
    context = {'model': model, 'session': model.Session, 'user': toolkit.c.user or toolkit.c.author}
    if (
        request.method == 'POST' and request.form['save'] == 'approve' and
        toolkit.check_access('organization_update', context, {'id': id})
    ):
        # update approval status to pending for organization
        toolkit.get_action('organization_patch')(data_dict={'id': id, 'approval_status': 'pending'})
        # NOTE: maybe send message to admin about reapproval?

    # FIXME: Original implementation called "original" edit route. This is not practical in Flask.
    # return self.edit(id, data, errors, error_summary)
