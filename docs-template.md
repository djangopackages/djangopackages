[[[cog
import cog
from pathlib import Path
import inspect
import importlib.util

import django
django.setup()

def load_module_from_file(file_path):
    spec = importlib.util.spec_from_file_location("module.name", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def extract_docstrings(file_path, class_name=None):
    module = load_module_from_file(file_path)
    class_docstring = None
    method_docstring = None

    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and (class_name is None or name == class_name):
            class_docstring = inspect.getdoc(obj)
            # Now check for the 'check' method
            if hasattr(obj, 'check'):
                method_docstring = inspect.getdoc(getattr(obj, 'check'))
                method_docstring = method_docstring.replace('\n', ' ')
            break

    return class_docstring, method_docstring

file_path = Path('searchv2/rules.py')

class_docstring, method_docstring = extract_docstrings(file_path, class_name)

cog.out(f"# {class_name}\n\n")
cog.out(f"{class_docstring}\n\n")
cog.out(f"{method_docstring}")

]]]
# DeprecatedRule

A specific rule that checks if the package is deprecated.

Check if the package is deprecated.Returns a full score and a success message if the package is not deprecated,or a zero score and an error message otherwise.
[[[end]]]
