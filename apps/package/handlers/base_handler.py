"""
github = package.handlers.Gibhut()
github.repo_url

package = github.pull()

"""
from package.models import Package

class BaseHandler(object):

    @property
    def title(self):
        """ title for display in drop downs:

                return: string
                example: 'Github'
        """
        raise NotImplemented()
    
    @property
    def url(self):
        """ base value for url API interation:

                return: URL string        
                example: 'https://github.com'
        """
        raise NotImplemented()
            
    def pull(self, package):
        """ Accepts a package.models.Package instance:
            
                return: package.models.Package instance
                
            Must set the following fields:

                package.repo_watchers (int)
                package.repo_forks (int)
                package.repo_description (text )
                package.participants = (comma-seperated value)

        """
        raise NotImplemented()

    @property
    def is_other(self):
        """ DON'T CHANGE THIS PROPERTY!

                return: False
        """
        if self.title == 'Other':
            return True
        return False
        
    @property
    def user_url(self):
        """ identifies the user URL:
        
                example: 
        """
        raise NotImplemented()
        
    @property
    def user_regex(self):
        """ Used by the JavaScript forms """
        raise NotImplemented()

    @property
    def repo_regex(self):
        """ Used by the JavaScript forms """        
        raise NotImplemented()

    @property
    def slug_regex(self):
        """ Used by the JavaScript forms """        
        raise NotImplemented()
        
    @property
    def package_updater(self):
        """ Used by the JavaScript forms """        
        raise NotImplemented()
        
        
    def packages_for_profile(self, profile):
        """ Return a list of all packages contributed to by a profile. """
        repo_url = profile.url_for_repo(self)
        if repo_url:
            regex = r'^{0},|,{0},|{0}$'.format(repo_url)
            query = Q(participants__regex=regex) & Q(repo=self)
            return list(Package.objects.filter(query))
        else:
            return []