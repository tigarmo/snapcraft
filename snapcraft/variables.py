import hashlib
import re
import subprocess
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional, List

_HOST_VAR_RE = re.compile(r"\$\(HOST(?P<secret>_SECRET)?:(?P<command>.*)\)")


@dataclass
class HostVars:
    mapping: Dict[str, str]
    secrets: List[str]
    is_managed: bool
    env: Dict[str, str]


def apply_host_variables(
    yaml_data: Dict[Any, Any], is_managed: bool, env: Dict[str, str]
) -> HostVars:

    host_vars = HostVars(mapping={}, secrets=[], is_managed=is_managed, env=env)

    parts = yaml_data.get("parts", {})

    _try_handle_container(parts, host_vars)

    return host_vars


def _try_handle_container(data: Any, host_vars: HostVars) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = _handle_string(value, host_vars)
            else:
                _try_handle_container(value, host_vars)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, str):
                data[i] = _handle_string(item, host_vars)
            else:
                _try_handle_container(item, host_vars)
    # Not a dict or list: don't do anything


def _handle_string(value: str, host_vars: HostVars) -> str:
    if match := _HOST_VAR_RE.search(value):
        command = match.group("command")
        if host_vars.is_managed:
            # managed mode: value must exist in 'env'
            var_name = _get_var_name(command)
            new_value = host_vars.env[var_name]
        else:
            # running on the host: run the command
            new_value = _get_host_value(command)

            var_name = _get_var_name(command)
            host_vars.mapping[var_name] = new_value

        if match.group("secret"):
            host_vars.secrets.append(new_value)

        return value.replace(match.group(), new_value)
    return value


def _get_host_value(cmd: str) -> str:
    output = subprocess.check_output(["bash", "-c", cmd])
    return output.decode().rstrip()


def _get_var_name(cmd: str) -> str:
    md5 = hashlib.md5(cmd.encode("utf8"))
    return f"CRAFT_{md5.hexdigest()}"
