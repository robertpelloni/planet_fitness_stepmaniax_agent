import pytest
import os
from lupa import LuaRuntime

@pytest.fixture(scope="module")
def lua_fitness():
    lua = LuaRuntime(unpack_returned_tuples=True)

    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Scripts', 'FitnessDifficulties.lua')

    with open(script_path, 'r') as f:
        lua_code = f.read()

    lua_module = lua.execute(lua_code)
    return lua_module

def test_get_intensity_from_nps(lua_fitness):
    # Base cases
    assert lua_fitness.GetIntensityFromNPS(0) == 1.0
    assert lua_fitness.GetIntensityFromNPS(-5) == 1.0

    # Normal usage
    assert lua_fitness.GetIntensityFromNPS(6.0) == 5.0

    # Max bound
    assert lua_fitness.GetIntensityFromNPS(12.0) == 10.0
    assert lua_fitness.GetIntensityFromNPS(20.0) == 10.0

def test_get_category_from_nps(lua_fitness):
    assert lua_fitness.GetCategoryFromNPS(6.0) == 5
    assert lua_fitness.GetCategoryFromNPS(12.0) == 10

def test_estimate_met(lua_fitness):
    # Base cases
    assert lua_fitness.EstimateMET(0) == 1.0

    # Normal usage
    # 6.0 nps -> 5.0 intensity -> 3.0 + (5.0 - 1.0) * (9.0 / 9.0) = 7.0
    assert lua_fitness.EstimateMET(6.0) == 7.0

    # Max bound
    # 12.0 nps -> 10.0 intensity -> 3.0 + (10.0 - 1.0) * (9.0 / 9.0) = 12.0
    assert lua_fitness.EstimateMET(12.0) == 12.0
