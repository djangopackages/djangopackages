"""RestConsumer: Generic REST API consumer. 
-----------------------------------------------------------------------

RestConsumer is a generic python wrapper for consuming JSON REST APIs. It is built with python-requests, some magic and good intentions. This is the first alpha release; pull requests are welcome.

Rationale:

    All modern REST API services already have an hierarchical meaningful url structure and return the response content in JSON format. Custom API wrappers for each service would necessitate the developer consuming the API, to refer to the documentation of the wrapper as well as the service itself. (Do I call the twitter.public_timeline() or twitter.get_public_timeline() of this particular library; what about it's pagination option?)

    This package is an attempt to exploit the meaningful url structure and use some python magic to make it developer friendly to create a thin wrapper, on using which the developer would be enabled to consume REST API by looking at the service documentation alone. 

    Examples below highlight it's purpose and use.

For Github API v3:  From the documentation, `/users/:user/repos/` returns all the user's repos.

::

	# Instantiate the consumer with the api end point
	>>> github = RestConsumer(base_url='https://api.github.com/')

	# use the consumer to query for the repos.
	>>> github.users.kennethreitz.repos() -- Returns all the repos of the user kennethreitz.

	Internally, requests.get(url='https://api.github.com/users/kennethreitz/repos') is called and the content is returned in a python dict.

For Stackoverflow: http://api.stackoverflow.com/1.1/users/55562/questions/unanswered returns unanswered questions for user with id 55562

::

	>>> stack = RestConsumer(base_url='http://api.stackoverflow.com/1.1')

	# When there are special characters, that can't be used as python methods, You can access it's item, like a dict.
	>>> s.users['55562'].questions.unanswered()

	# All the top answerers of the tag python can be obtained from: http://api.stackoverflow.com/1.1/tags/python/top-answerers/all-time
	s.tags.python['top-answerers']['all-time']()

For Twitter:

::

	# Initialize twitter from it's end point. All twitter api calls need '.json' appended.
	t = RestConsumer(base_url='http://api.twitter.com/1',append_json=True)

	# From the twitter documentation, /statuses/public_timeline provides all public timeline data
	t.statuses.public_timeline()

	# Similarly, /user_timeline?screen_name=becomingGuru provides the timeline of the given user
	t.statuses.user_timeline.get(screen_name='becomingGuru')

	# Since get is the default, you can skip that and just do:
	t.statuses.user_timeline(screen_name='becomingGuru')

	# Since twitter also allows (undocumented) /user_timeline/becomingGuru, you can do:
	t.statuses.user_timeline.becomingGuru() -- Which is equivallent to t.statuses.user_timeline.becomingGuru.get()

This is all you need to know about this package. That's the whole point.
Spend your time reading through the documentation of the REST API that you are trying to consume rather than another class wrapper built around it.
You get a dictionary of the received JSON. Wrapping those in classes is hardly pythonic or transparent, nor does it allow you to store it in a database without enough changes. Might as well deal with the received data directly.

Credits: API has been inspired by http://mike.verdone.ca/twitter/, about 2 years ago: http://weblog.becomingguru.com/2009/05/awesome-python-twitter-library-see.html
While that one is twitter only, this is intended as a generic wrapper. With requests in the scene doing all the hard work, this should be simpler.


TODO:

* Returning mutated self is not a good idea. Return new objects.    - Done.
* Enable oAuth
* Enable all parameters taken by requests. Lazy content fetch, with header only, ...
* Provide services.py, that provides various classes, that document end points of various services, so developer can import bing and get going.
* Enable bash auto completion of different services by including various uri's
* Include headers etc as params in the response given.
* Explore wrapping response into ServiceClasses that behave like dict, list and other
* Add more services, freebase, wikipedia"""

import requests, json

def append_to_url(base_url,param):
    return "%s%s/" % (base_url,param)


class RestConsumer(object):

    def __init__(self,base_url,append_json=False,append_slash=False):
        self.base_url = base_url if base_url[-1] == '/' else "%s%s" % (base_url,"/")
        self.append_json = append_json
        self.append_slash = append_slash

    def __getattr__(self,key):
        new_base = append_to_url(self.base_url,key)
        return self.__class__(base_url=new_base,
                              append_json=self.append_json,
                              append_slash=self.append_slash)
    
    def __getitem__(self,key):
        return self.__getattr__(key)

    def __call__(self, **kwargs):
        if not self.append_slash:
            self.base_url = self.base_url[:-1]
        if self.append_json:
            self.base_url = "%s%s" % (self.base_url,'.json')
        print "Calling %s" % self.base_url
        return self.get(self.base_url,**kwargs)

    def get(self,url,**kwargs):
        r = requests.get(url,**kwargs)
        return json.loads(r.content)

    def post(self,**kwargs):
        r = requests.post(**kwargs)
        return json.loads(r.content)


Twitter = RestConsumer(base_url='https://api.twitter.com/1',append_json=True)
Github = RestConsumer(base_url='https://api.github.com')
Stackoverflow = RestConsumer(base_url='http://api.stackoverflow.com/1.1')

if __name__=='__main__':
    from pprint import pprint
    t = RestConsumer(base_url='https://api.twitter.com/1',append_json=True)
    public_timeline = t.statuses.public_timeline()
    pprint(public_timeline)

    g = RestConsumer(base_url='https://api.github.com')
    repos = g.users.kennethreitz.repos()
    pprint(repos)

    s = RestConsumer(base_url='http://api.stackoverflow.com/1.1')
    sr = s.users['55562'].questions.unanswered()
    pprint(sr)

    sr2 = s.tags.python['top-answerers']['all-time']
    pprint(sr2())