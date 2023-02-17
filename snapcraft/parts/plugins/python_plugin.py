# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2020-2021 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""The python plugin."""

import shlex
from textwrap import dedent
from typing import Any, Dict, List, Set, cast, Optional, Tuple

from overrides import override

from ._parts_python_plugin import PythonPlugin as PartsPythonPlugin


CONFIG_TO_PYTHON = {
    ("core22", "strict"): "/usr/bin/python3.10",
    ("core22", "classic"): "/snap/core22/current/usr/bin/python3.10",
}

SHEBANG = r"""#\!/bin/sh\n''':'\nexec \$SNAP/bin/python3 -tt "\$0" "\$@"\n'''"""
"""
#!/bin/bash
''':'
exec $SNAP/bin/python3 -tt "$0" "$@"
'''
"""


class SnapcraftPythonPlugin(PartsPythonPlugin):
    @override
    def get_base_python(self) -> Tuple[Optional[str], str]:
        info = self._part_info
        base = info.base
        confinement = info.confinement
        base_confinement = (base, confinement)

        found = CONFIG_TO_PYTHON.get(base_confinement)
        if found:
            reason = f'Using python interpreter "{found}" because of base "{base}" and confinement "{confinement}"'
        else:
            reason = f'Don\'t know which python interpreter to use for base "{base}" and confinement "{confinement}"'

        return found, reason

    @override
    def get_shebang_target(self) -> str:
        return SHEBANG
