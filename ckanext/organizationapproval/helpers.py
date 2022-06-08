from ckan.lib import helpers


def make_pager_url(q=None, page=None):
    url = helpers.url_for("organizationapproval.manage_organizations")
    return url + '?page=' + str(page)
