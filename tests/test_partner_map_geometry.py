"""Exercise geometry edge cases in the actual ES module, with Node's assertions."""
from pathlib import Path
import subprocess


def test_coordinate_validation_and_dateline():
    path = (Path(__file__).parents[1] / "src/exchange_info/static/partner-map.js").resolve().as_uri()
    program = f"""
import assert from 'node:assert/strict';
import {{hasCoordinates,pointsFor,coordinateBounds}} from {path!r};
const location={{geocode_status:'verified',latitude:0,longitude:0}};
assert.equal(hasCoordinates({{location}}),true);
for(const bad of [null,{{}},{{...location,latitude:null}},{{...location,latitude:NaN}},{{...location,longitude:181}},{{...location,geocode_status:'pending'}}])
  assert.equal(Boolean(hasCoordinates({{location:bad}})),false);
assert.equal(pointsFor([{{school_name:'A',location}},{{school_name:'missing'}}]).features.length,1);
const bounds=coordinateBounds([[179,-20],[-179,-17]]);
assert.equal(bounds[1][0]-bounds[0][0],2);
assert.equal(coordinateBounds([]),null);
"""
    result = subprocess.run(["node", "--input-type=module", "-e", program], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
