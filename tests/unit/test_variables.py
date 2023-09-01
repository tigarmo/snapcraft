import copy

from snapcraft import variables

YAML = {
    "parts": {
        "mypart": {
            "source": "https://github.com/$(HOST_SECRET:echo $MY_SECRET_VAR).git",
            "build-environment": [
                {"PART_ENVVAR1": "$(HOST:echo $MY_VAR)"},
                {"PART_ENVVAR2": "on"},
            ],
        }
    }
}


def test_variables_1(monkeypatch):
    monkeypatch.setenv("MY_SECRET_VAR", "my_secret_var_value")
    monkeypatch.setenv("MY_VAR", "my_var_value")

    test_yaml = copy.deepcopy(YAML)
    host_vars = variables.apply_host_variables(test_yaml, is_managed=False, env={})

    part = test_yaml["parts"]["mypart"]
    assert part["source"] == "https://github.com/my_secret_var_value.git"

    assert part["build-environment"] == [
        {"PART_ENVVAR1": "my_var_value"},
        {"PART_ENVVAR2": "on"},
    ]

    assert host_vars.mapping == {
        "CRAFT_94d30d76b97e6646d294adec8196bdf7": "my_secret_var_value",
        "CRAFT_35406838c6f56676de97758243093aea": "my_var_value",
    }
    assert host_vars.secrets == ["my_secret_var_value"]
