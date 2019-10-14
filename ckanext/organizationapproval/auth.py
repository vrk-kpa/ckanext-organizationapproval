from ckan.plugins import toolkit
import logging

log = logging.getLogger(__name__)


@toolkit.chained_auth_function
def package_create(next_auth, context, data_dict):
    if data_dict is None:
        return {'success': True}

    owner_org = data_dict.get('owner_org')

    if not owner_org:
        return {'success': True}

    organization = toolkit.get_action('organization_show')(context, {'id': owner_org})
    approved = organization.get('approval_status') == 'approved'
    return {'success': approved}
