from collections.abc import Generator
from ckan.plugins import toolkit
from ckan.types import Context, DataDict
import itertools
from typing import Optional


def organization_generator(context: Context,
                           options: Optional[DataDict] = None,
                           page_size: Optional[int] = None) -> Generator[dict]:
    if options is None:
        options = {}

    if page_size is None:
        # Default value for ckan.group_and_organization_list_all_fields_max is 25
        # Default value for ckan.group_and_organization_list_max is 1000
        if options.get('all_fields', False):
            page_size = toolkit.config.get('ckan.group_and_organization_list_all_fields_max', 25)
        else:
            page_size = toolkit.config.get('ckan.group_and_organization_list_max', 1000)

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

        yield from organizations

        # Incomplete page, must be the last one
        if len(organizations) < page_size:
            return
