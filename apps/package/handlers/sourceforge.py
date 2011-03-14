import re
import xmlrpclib
from urllib import urlopen

try:
    import simplejson as json
except ImportError:
    import json

    
project_name1_RE = re.compile(r'projects/([^/]+)/?$')
project_name2_RE = re.compile(r'^http://([^/]+).sourceforge')

def _sourceforge_name_from_pypi_home_page(home_page):

    name1 = project_name1_RE.search(home_page)
    if name1:
        name1 = name1.group(1)
        
    name2 = project_name2_RE.search(home_page)
    if name2:
        name2 = name2.group(1)
        if name2 == 'www':
            name2 = None
            
    return name1 or name2


def _get_sourceforge_project_data(sourceforge_project_name):
    if sourceforge_project_name == None:
        return None
    
    project_json_path = 'http://sourceforge.net/api/project/name/%s/json/' % sourceforge_project_name
    # open the target and read the content
    response = urlopen(project_json_path)
    response = response.read()
    
    # dejsonify the results
    try:
        project_data = json.loads(response)['Project']
    except KeyError:  # project does not exist
        project_data = None
    except ValueError:  # likely invalid chars in json file
        project_data = None
        
    return project_data


def _get_sourceforge_repo_url(sourceforge_package_data):
    # TODO: add support for hg and git.
    if 'SVNRepository' in sourceforge_package_data:
        return sourceforge_package_data['SVNRepository'].get('location', '')
    elif 'CVSRepository' in sourceforge_package_data:
        return sourceforge_package_data['SVNRepository'].get('anon-root', '')
    else:
        return ''             

    
def _get_sourceforge_participants(sourceforge_package_data):
    maintainers = [maintainer['name'] for maintainer in sourceforge_package_data['maintainers']]
    developers  = [developer['name'] for developer in sourceforge_package_data['developers']]
    participants = maintainers + developers
    return ','.join(participants)


def pull(package):
    sourceforge_project_name = _sourceforge_name_from_pypi_home_page(package.pypi_home_page)
    
    # dejsonify the results
    try:
        sf_package_data = _get_sourceforge_project_data(sourceforge_project_name)
    except json.decoder.JSONDecodeError:
        message = "%s had a JSONDecodeError while loading %s" % (package.title,
                                                                 package_json_path)
        warn(message)
        return package
    
    package.repo_watchers = len(sf_package_data.get('maintainers', [])) + len(sf_package_data.get('developers', [])) 
    package.repo_description = sf_package_data.get('description', '')
    # TODO - remove the line below and use repo_url as your foundation    
    package.repo_url = _get_sourceforge_repo_url(sf_package_data)
    package.repo_forks = None
    package.participants = _get_sourceforge_participants(sf_package_data)
    
    return package
    
