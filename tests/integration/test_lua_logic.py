import pytest
import os
from lupa import LuaRuntime

@pytest.fixture(scope="module")
def lua_fitness():
    """Initializes the Lua runtime and loads the FitnessDifficulties module."""
    lua = LuaRuntime(unpack_returned_tuples=True)

    # Read the Lua file
    script_path = os.path.join(os.path.dirname(__file__), '../../Scripts/FitnessDifficulties.lua')
    with open(script_path, 'r') as f:
        lua_code = f.read()

    # Execute the module code and get the returned table
    fitness_module = lua.execute(lua_code)
    return fitness_module

def test_intensity_scaling(lua_fitness):
    """Test that Notes Per Second (NPS) correctly maps to a 1-10 intensity scale."""
    # Base cases
    assert lua_fitness.GetIntensityFromNPS(0) == 1.0
    assert lua_fitness.GetIntensityFromNPS(-5) == 1.0

    # Mid-range (e.g., 6.0 NPS should be 50% of MAX_CARDIO_NPS (12.0) = 5.0 intensity)
    assert lua_fitness.GetIntensityFromNPS(6.0) == 5.0

    # Max range cap
    assert lua_fitness.GetIntensityFromNPS(12.0) == 10.0
    assert lua_fitness.GetIntensityFromNPS(20.0) == 10.0 # Should not exceed 10.0

def test_met_estimation(lua_fitness):
    """Test that Metabolic Equivalent of Task (MET) scales appropriately with intensity."""
    # Base case (Resting)
    assert lua_fitness.EstimateMET(0) == 1.0

    # Low intensity (Intensity 1.0 -> 3.0 MET)
    # GetIntensityFromNPS(1.2) = 1.0
    assert lua_fitness.EstimateMET(1.2) == 3.0

    # Max intensity (Intensity 10.0 -> 12.0 MET)
    assert lua_fitness.EstimateMET(12.0) == 12.0

def test_category_floor(lua_fitness):
    """Test that broad categorization correctly floors the intensity."""
    # 6.6 NPS -> 5.5 Intensity -> Category 5
    assert lua_fitness.GetCategoryFromNPS(6.6) == 5

    # 11.9 NPS -> 9.9 Intensity -> Category 9
    assert lua_fitness.GetCategoryFromNPS(11.9) == 9
