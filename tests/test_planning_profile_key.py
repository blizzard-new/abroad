"""The recommendation plan is keyed on the conditions it was made for, whatever order their fields arrive in."""
import subprocess
from pathlib import Path

APP_JS = Path(__file__).resolve().parents[1] / "src" / "exchange_info" / "static" / "app.js"


def test_planning_profile_key_ignores_field_order_but_not_values() -> None:
    script = r"""
    const assert = require("node:assert/strict"), fs = require("node:fs");
    const source = fs.readFileSync(process.argv[1], "utf8");
    eval(source.match(/^function planningProfileKey\([^]*?^}/m)[0]);
    const activeHomeSchool = () => "長庚大學";
    const state = { account: { id: "student" }, eligibilityProfile: { college: "工學院", degree: "大學部", academicYear: "" } };
    const before = planningProfileKey();
    // The account's saved copy comes back with the same values in another order.
    state.eligibilityProfile = { academicYear: "", college: "工學院", degree: "大學部" };
    assert.equal(planningProfileKey(), before);
    state.eligibilityProfile = { academicYear: "116", college: "工學院", degree: "大學部" };
    assert.notEqual(planningProfileKey(), before);
    state.eligibilityProfile = null;
    assert.equal(planningProfileKey(), JSON.stringify(["student", "長庚大學", null]));
    """
    result = subprocess.run(["node", "-e", script, str(APP_JS)], capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
