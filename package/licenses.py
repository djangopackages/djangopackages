"""Turn the many ways a license gets written down into one SPDX id.

Licenses reach us three ways: a PEP 639 `license_expression`, a trove
classifier, and the legacy free text `license` field, which holds
anything from "MIT" to the full license body to "LICENSE.txt". GitHub
also detects a license from the repository. This module makes them
agree, so MIT is "MIT" whichever way it arrived and the license filter
has one bucket per license rather than five.
"""

from __future__ import annotations

import re

UNKNOWN = "UNKNOWN"

# Trove classifier -> SPDX id. Classifiers that name a family rather
# than a license ("OSI Approved", "BSD License") keep a short family
# label, since guessing the clause count would be making data up.
CLASSIFIERS = {
    "Academic Free License (AFL)": "AFL-3.0",
    "Apache Software License": "Apache-2.0",
    "Apple Public Source License": "APSL-2.0",
    "Artistic License": "Artistic-2.0",
    "Attribution Assurance License": "AAL",
    "BSD License": "BSD",
    "Blue Oak Model License (BlueOak-1.0.0)": "BlueOak-1.0.0",
    "Boost Software License 1.0 (BSL-1.0)": "BSL-1.0",
    "CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)": "CECILL-2.1",
    "CMU License (MIT-CMU)": "MIT-CMU",
    "Common Development and Distribution License 1.0 (CDDL-1.0)": "CDDL-1.0",
    "Common Public License": "CPL-1.0",
    "Eclipse Public License 1.0 (EPL-1.0)": "EPL-1.0",
    "Eclipse Public License 2.0 (EPL-2.0)": "EPL-2.0",
    "Educational Community License, Version 2.0 (ECL-2.0)": "ECL-2.0",
    "Eiffel Forum License": "EFL-2.0",
    "European Union Public Licence 1.0 (EUPL 1.0)": "EUPL-1.0",
    "European Union Public Licence 1.1 (EUPL 1.1)": "EUPL-1.1",
    "European Union Public Licence 1.2 (EUPL 1.2)": "EUPL-1.2",
    "GNU Affero General Public License v3": "AGPL-3.0-only",
    "GNU Affero General Public License v3 or later (AGPLv3+)": "AGPL-3.0-or-later",
    "GNU Free Documentation License (FDL)": "GFDL-1.3-only",
    "GNU General Public License (GPL)": "GPL",
    "GNU General Public License v2 (GPLv2)": "GPL-2.0-only",
    "GNU General Public License v2 or later (GPLv2+)": "GPL-2.0-or-later",
    "GNU General Public License v3 (GPLv3)": "GPL-3.0-only",
    "GNU General Public License v3 or later (GPLv3+)": "GPL-3.0-or-later",
    "GNU Lesser General Public License v2 (LGPLv2)": "LGPL-2.0-only",
    "GNU Lesser General Public License v2 or later (LGPLv2+)": "LGPL-2.0-or-later",
    "GNU Lesser General Public License v3 (LGPLv3)": "LGPL-3.0-only",
    "GNU Lesser General Public License v3 or later (LGPLv3+)": "LGPL-3.0-or-later",
    "GNU Library or Lesser General Public License (LGPL)": "LGPL",
    "Historical Permission Notice and Disclaimer (HPND)": "HPND",
    "IBM Public License": "IPL-1.0",
    "ISC License (ISCL)": "ISC",
    "MIT License": "MIT",
    "MIT No Attribution License (MIT-0)": "MIT-0",
    "MirOS License (MirOS)": "MirOS",
    "Mozilla Public License 1.0 (MPL)": "MPL-1.0",
    "Mozilla Public License 1.1 (MPL 1.1)": "MPL-1.1",
    "Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
    "Mulan Permissive Software License v2 (MulanPSL-2.0)": "MulanPSL-2.0",
    "NASA Open Source Agreement v1.3 (NASA-1.3)": "NASA-1.3",
    "Nethack General Public License": "NGPL",
    "Open Software License 3.0 (OSL-3.0)": "OSL-3.0",
    "PostgreSQL License": "PostgreSQL",
    "Python License (CNRI Python License)": "CNRI-Python",
    "Python Software Foundation License": "PSF-2.0",
    "Qt Public License (QPL)": "QPL-1.0",
    "SIL Open Font License 1.1 (OFL-1.1)": "OFL-1.1",
    "Sleepycat License": "Sleepycat",
    "Sun Public License": "SPL-1.0",
    "The Unlicense (Unlicense)": "Unlicense",
    "Universal Permissive License (UPL)": "UPL-1.0",
    "University of Illinois/NCSA Open Source License": "NCSA",
    "Vovida Software License 1.0": "VSL-1.0",
    "W3C License": "W3C",
    "Zero-Clause BSD (0BSD)": "0BSD",
    "Zope Public License": "ZPL-2.1",
    "zlib/libpng License": "Zlib",
    "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication": "CC0-1.0",
    "CeCILL-B Free Software License Agreement (CECILL-B)": "CECILL-B",
    "CeCILL-C Free Software License Agreement (CECILL-C)": "CECILL-C",
    "Public Domain": "Public Domain",
    "Other/Proprietary License": "Proprietary",
}

# The spellings people actually put in the legacy field, lower cased
# with punctuation squeezed, -> SPDX id. Built from what is in our
# database today; extend it when a new spelling shows up in numbers.
SPELLINGS = {
    # MIT
    "mit": "MIT",
    "mit license": "MIT",
    "the mit license": "MIT",
    "the mit license (mit)": "MIT",
    "mit license (mit)": "MIT",
    "expat": "MIT",
    # BSD
    "bsd": "BSD",
    "bsd license": "BSD",
    "freebsd": "BSD-2-Clause",
    "simplified bsd": "BSD-2-Clause",
    "bsd 2-clause": "BSD-2-Clause",
    "bsd-2-clause": "BSD-2-Clause",
    "bsd 2-clause license": "BSD-2-Clause",
    "2-clause bsd": "BSD-2-Clause",
    "new bsd": "BSD-3-Clause",
    "new bsd license": "BSD-3-Clause",
    "modified bsd": "BSD-3-Clause",
    "revised bsd": "BSD-3-Clause",
    "bsd 3-clause": "BSD-3-Clause",
    "bsd-3-clause": "BSD-3-Clause",
    "bsd 3-clause license": "BSD-3-Clause",
    "bsd-3": "BSD-3-Clause",
    "bsd3": "BSD-3-Clause",
    "3-clause bsd": "BSD-3-Clause",
    "3-clause bsd license": "BSD-3-Clause",
    "0bsd": "0BSD",
    # Apache
    "apache": "Apache-2.0",
    "apache 2": "Apache-2.0",
    "apache 2.0": "Apache-2.0",
    "apache-2.0": "Apache-2.0",
    "apache2": "Apache-2.0",
    "apache 2.0 license": "Apache-2.0",
    "apache license": "Apache-2.0",
    "apache license 2.0": "Apache-2.0",
    "apache license, version 2.0": "Apache-2.0",
    "apache license version 2.0": "Apache-2.0",
    "apache software license": "Apache-2.0",
    "apache software license 2.0": "Apache-2.0",
    "asl 2": "Apache-2.0",
    # GPL family
    "gpl": "GPL",
    "gnu gpl": "GPL",
    "gnu general public license": "GPL",
    "gplv2": "GPL-2.0-only",
    "gpl v2": "GPL-2.0-only",
    "gpl2": "GPL-2.0-only",
    "gpl-2.0": "GPL-2.0-only",
    "gpl-2.0-only": "GPL-2.0-only",
    "gplv2+": "GPL-2.0-or-later",
    "gpl-2.0-or-later": "GPL-2.0-or-later",
    "gplv3": "GPL-3.0-only",
    "gpl v3": "GPL-3.0-only",
    "gpl3": "GPL-3.0-only",
    "gpl-3.0": "GPL-3.0-only",
    "gpl-3": "GPL-3.0-only",
    "gpl-3.0-only": "GPL-3.0-only",
    "gnu gplv3": "GPL-3.0-only",
    "gnu gplv3 license": "GPL-3.0-only",
    "gnu gpl v3": "GPL-3.0-only",
    "gnu general public license v3": "GPL-3.0-only",
    "gnu general public license v3 (gplv3)": "GPL-3.0-only",
    "gplv3+": "GPL-3.0-or-later",
    "gpl-3.0+": "GPL-3.0-or-later",
    "gpl-3.0-or-later": "GPL-3.0-or-later",
    "gnu gplv3+": "GPL-3.0-or-later",
    # LGPL
    "lgpl": "LGPL",
    "gnu lgpl": "LGPL",
    "lgpl 3": "LGPL-3.0-only",
    "lgpl3": "LGPL-3.0-only",
    "lgplv3": "LGPL-3.0-only",
    "lgpl-3.0": "LGPL-3.0-only",
    "lgpl-3.0-only": "LGPL-3.0-only",
    "lgpl3+": "LGPL-3.0-or-later",
    "lgplv3+": "LGPL-3.0-or-later",
    "lgpl-3.0-or-later": "LGPL-3.0-or-later",
    "lgpl 2.1": "LGPL-2.1-only",
    "lgplv2.1": "LGPL-2.1-only",
    "lgpl-2.1": "LGPL-2.1-only",
    "lgplv2": "LGPL-2.0-only",
    # AGPL
    "agpl": "AGPL-3.0-only",
    "agplv3": "AGPL-3.0-only",
    "agpl-3.0": "AGPL-3.0-only",
    "agpl-3.0-only": "AGPL-3.0-only",
    "agpl v3": "AGPL-3.0-only",
    "agplv3+": "AGPL-3.0-or-later",
    "agpl-3.0-or-later": "AGPL-3.0-or-later",
    # Others
    "isc": "ISC",
    "isc license": "ISC",
    "mpl": "MPL-2.0",
    "mpl 2.0": "MPL-2.0",
    "mpl-2.0": "MPL-2.0",
    "mpl2": "MPL-2.0",
    "mozilla public license 2.0": "MPL-2.0",
    "unlicense": "Unlicense",
    "the unlicense": "Unlicense",
    "public domain": "Public Domain",
    "cc0": "CC0-1.0",
    "cc0-1.0": "CC0-1.0",
    "wtfpl": "WTFPL",
    "zlib": "Zlib",
    "psf": "PSF-2.0",
    "python software foundation license": "PSF-2.0",
    "proprietary": "Proprietary",
    "beer-ware": "Beerware",
    "beerware": "Beerware",
    "cecill-b": "CECILL-B",
    "eupl-1.2": "EUPL-1.2",
    "eupl 1.2": "EUPL-1.2",
}

# A bare SPDX expression: ids joined with AND / OR / WITH, maybe in
# parentheses. "MIT OR Apache-2.0" is kept as written.
_EXPRESSION = re.compile(r"^[A-Za-z0-9.+\-]+(\s+(AND|OR|WITH)\s+[A-Za-z0-9.+\-]+)*$")
_SPDX_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+\-]*$")

# Things that end up in the legacy field and are not a license.
_NOT_A_LICENSE = {
    "",
    "unknown",
    "none",
    "license",
    "licence",
    "license.txt",
    "license.md",
    "licence.txt",
    "see license",
    "see license file",
    "see license.txt",
    "tbd",
    "todo",
    "n/a",
    "gnu",
    "custom",
    "other",
}


def _squeeze(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .,;:'\"")


def from_classifier(classifier: str) -> str | None:
    """The SPDX id a `License ::` trove classifier stands for."""
    if not classifier.startswith("License ::"):
        return None
    name = classifier.split("::")[-1].strip()
    return CLASSIFIERS.get(name)


def normalize(text: str | None) -> str | None:
    """One spelling for a license, or None when the text is not one.

    Short text is matched against the spellings table, then accepted as
    an SPDX id or expression if it is shaped like one. Anything long or
    multi-line is a license body that someone pasted into a name field,
    and the classifiers are the place to find out what it is.
    """
    if not text:
        return None
    text = str(text)
    if "\n" in text.strip() or len(text) > 60:
        return None

    squeezed = _squeeze(text)
    if squeezed in _NOT_A_LICENSE:
        return None
    if squeezed in SPELLINGS:
        return SPELLINGS[squeezed]

    stripped = text.strip()
    if _EXPRESSION.match(stripped):
        # "MIT" and friends resolved above; this keeps "MIT OR Apache-2.0"
        # and ids we have no spelling for, like "CeCILL-2.1". A lone word
        # of letters is not evidence of anything, so an id has to carry a
        # version or an operator to count here.
        parts = re.split(r"\s+(?:AND|OR|WITH)\s+", stripped)
        looks_like_ids = all(_SPDX_ID.match(part) for part in parts)
        has_shape = len(parts) > 1 or any(ch.isdigit() or ch == "-" for ch in stripped)
        if looks_like_ids and has_shape:
            return stripped

    # Short free text that names a license we have no mapping for:
    # keep it, since "Repoze Public License" beats UNKNOWN.
    if len(stripped) <= 40 and any(ch.isalpha() for ch in stripped):
        return stripped
    return None


def from_pypi(
    *,
    license_expression: str | None,
    classifiers: list[str],
    legacy: str | None,
) -> list[str]:
    """Every license PyPI tells us about, best evidence first.

    A PEP 639 expression is the author stating it outright. A classifier
    is a choice from a fixed list. The legacy field is free text and
    only counts when it is short enough to be a name rather than the
    license itself.
    """
    found: list[str] = []

    def add(value: str | None) -> None:
        if value and value not in found:
            found.append(value)

    add(normalize(license_expression))
    for classifier in classifiers:
        add(from_classifier(classifier))
    if not found:
        add(normalize(legacy))
    return found
