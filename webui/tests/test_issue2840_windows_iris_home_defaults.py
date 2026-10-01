from pathlib import Path

import api.config as config
import api.profiles as profiles


def test_profiles_unwrap_profile_home_to_base():
    base = Path('/tmp/iris-base')
    profile_home = base / 'profiles' / 'webui'
    assert profiles._unwrap_profile_home_to_base(profile_home) == base


def test_default_iris_home_returns_path_object():
    home = config._platform_default_iris_home()
    assert isinstance(home, Path)
