import shlex
from textwrap import dedent
from typing import Set, Dict, List, cast, Optional, Tuple

from craft_parts.plugins import Plugin
from craft_parts.plugins.python_plugin import PythonPluginProperties


class PythonPlugin(Plugin):
    """A modified version of craft_parts' PythonPlugin"""

    properties_class = PythonPluginProperties

    def get_build_snaps(self) -> Set[str]:
        """Return a set of required snaps to install in the build environment."""
        return set()

    def get_build_packages(self) -> Set[str]:
        """Return a set of required packages to install in the build environment."""
        return {"findutils", "python3-dev", "python3-venv"}

    def get_build_environment(self) -> Dict[str, str]:
        """Return a dictionary with the environment to use in the build step."""
        return {
            # Add PATH to the python interpreter we always intend to use with
            # this plugin. It can be user overridden, but that is an explicit
            # choice made by a user.
            "PATH": f"{self._part_info.part_install_dir}/bin:${{PATH}}",
            "PARTS_PYTHON_INTERPRETER": "python3",
            "PARTS_PYTHON_VENV_ARGS": "",
        }

    # pylint: disable=line-too-long

    def get_build_commands(self) -> List[str]:
        """Return a list of commands to run during the build step."""
        build_commands = [
            f'"${{PARTS_PYTHON_INTERPRETER}}" -m venv ${{PARTS_PYTHON_VENV_ARGS}} "{self._part_info.part_install_dir}"',
            f'PARTS_PYTHON_VENV_INTERP_PATH="{self._part_info.part_install_dir}/bin/${{PARTS_PYTHON_INTERPRETER}}"',
        ]

        options = cast(PythonPluginProperties, self._options)

        pip = f"{self._part_info.part_install_dir}/bin/pip"

        if options.python_constraints:
            constraints = " ".join(f"-c {c!r}" for c in options.python_constraints)
        else:
            constraints = ""

        if options.python_packages:
            python_packages = " ".join(
                [shlex.quote(pkg) for pkg in options.python_packages]
            )
            python_packages_cmd = f"{pip} install {constraints} -U {python_packages}"
            build_commands.append(python_packages_cmd)

        if options.python_requirements:
            requirements = " ".join(f"-r {r!r}" for r in options.python_requirements)
            requirements_cmd = f"{pip} install {constraints} -U {requirements}"
            build_commands.append(requirements_cmd)

        build_commands.append(f"[ -f setup.py ] && {pip} install {constraints} -U .")

        # Now fix shebangs.
        shebang_target = self.get_shebang_target()
        build_commands.append(
            dedent(
                f"""\
            find "{self._part_info.part_install_dir}" -type f -executable -print0 | xargs -0 \
                sed -i "1 s|^#\\!${{PARTS_PYTHON_VENV_INTERP_PATH}}.*$|{shebang_target}|"
            """
            )
        )

        if self.should_remove_symlinks():
            build_commands.append(
                dedent(
                    f"""
                    echo Removing python symlinks in {self._part_info.part_install_dir}/bin
                    rm {self._part_info.part_install_dir}/bin/python*
                    """
                )
            )
            return build_commands

        candidate_base_python, reason = self.get_base_python()
        base_python_path = candidate_base_python or ""
        # Lastly, fix the symlink to the "real" python3 interpreter.
        build_commands.append(
            dedent(
                f"""\
            determine_link_target() {{
                opts_state="$(set +o +x | grep xtrace)"
                interp_dir="$(dirname "${{PARTS_PYTHON_VENV_INTERP_PATH}}")"
                payload_python=$(find  "{self._part_info.part_install_dir}/usr/bin" "{self._part_info.stage_dir}/usr/bin" -iname "python3.10"  2> /dev/null | head -1)
                if [ -n "$payload_python" ]; then
                    python_path="../usr/bin/python3.10"
                else
                    python_path=""
                fi
                
                echo "${{python_path}}"
                eval "${{opts_state}}"
            }}

            payload_python="$(determine_link_target)"
            base_python_path="{base_python_path}"
            if [ -n "$payload_python" ]; then
                echo "Found payload python at $payload_python"
                python_path=${{payload_python}}
            else
                echo "{reason}"
                if [ -n "$base_python_path" ]; then
                    python_path=${{base_python_path}}
                else
                    exit 1
                fi
            fi            
            echo "Using python: ${{python_path}}"
            ln -sf "${{python_path}}" "${{PARTS_PYTHON_VENV_INTERP_PATH}}"
            """
            )
        )

        return build_commands

    def get_base_python(self) -> Tuple[Optional[str], str]:
        return '"$(which "${{PARTS_PYTHON_INTERPRETER}}")"', ""

    def get_shebang_target(self) -> str:
        return "#\!/usr/bin/env ${PARTS_PYTHON_INTERPRETER}"

    def should_remove_symlinks(self) -> bool:
        return False
