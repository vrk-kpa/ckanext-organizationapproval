from ckan.plugins import toolkit
import itertools


def organization_generator(context, options=None, page_size: int = None) -> list:
    if options is None:
        options = {}
    if page_size is None:
        # Default value for ckan.group_and_organization_list_max is 25
        page_size = toolkit.config.get('ckan.group_and_organization_list_max', 25)

    organization_list = toolkit.get_action('organization_list')

    # Loop through all items. Each page has {page_size} items.
    # Stop iteration when all items have been looped.
    for index in itertools.count(start=0, step=page_size):
        data_dict = options.copy()
        data_dict.update({'limit': page_size, 'offset': index})
        organizations = organization_list(context, data_dict)

        # Empty page, previous must have been the last one
        if not organizations:
            return

        for organization in organizations:
            yield organization

        # Incomplete page, must be the last one
        if len(organizations) < page_size:
            return
