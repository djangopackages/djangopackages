"""
Script found at http://djangosnippets.org/snippets/2905/
"""

import os, re

app_path = os.path.split(os.path.split(__file__)[0])[0]
PROJECT_ROOT = os.path.abspath(app_path)

def update_path(directory):
	"Update {% url to include ''"
	for path, dirs, files in os.walk(directory):
		for fname in files:
			if fname.endswith('.txt') or fname.endswith('.html'):
				fpath = os.path.join(path, fname)
				with open(fpath) as f:
					s = f.read()
				s = re.sub(r'{% url "(\w+)" ', r"{% url '\1' ", s)
				s = re.sub(r'{% url (\w+) ', r"{% url '\1' ", s)
				with open(fpath, "w") as f:
					f.write(s)
		for dir in dirs:
			update_path(dir)
update_path(PROJECT_ROOT)