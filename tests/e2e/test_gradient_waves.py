"""The decorative ocean animates without taking control of platform navigation."""
import pytest
from playwright.sync_api import expect

from .conftest import enter_public_site, open_navigation


TRACK_WEBGL = """(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    window.__waveContexts = [];
    HTMLCanvasElement.prototype.getContext = function(type, ...args) {
        const gl = original.call(this, type, ...args);
        if (type === 'webgl2' && gl && !window.__waveContexts.includes(gl)) {
            window.__waveContexts.push(gl);
            gl.__frames = 0;
            const draw = gl.drawArrays.bind(gl);
            gl.drawArrays = (...values) => { gl.__frames++; return draw(...values); };
        }
        return gl;
    };
    window.__ocean = () => window.__waveContexts.find(gl =>
        gl.canvas.closest('#platform-background'));
})()"""


@pytest.mark.parametrize("width,height", [(390, 844), (1440, 900)])
def test_ocean_renders_moves_and_keeps_navigation_clickable(page, live_server, width, height):
    page.set_viewport_size({"width": width, "height": height})
    page.emulate_media(reduced_motion="no-preference")
    page.add_init_script(TRACK_WEBGL)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    enter_public_site(page, live_server)
    background = page.locator("#platform-background")
    expect(background).to_have_attribute("aria-hidden", "true")
    expect(background).to_have_css("pointer-events", "none")
    expect(background.locator("canvas")).to_have_count(1)
    assert background.bounding_box() == {"x": 0, "y": 0, "width": width, "height": height}
    frames = page.evaluate("window.__ocean().__frames")
    page.wait_for_function("previous => window.__ocean().__frames > previous + 1", arg=frames)
    page.mouse.move(width * 0.85, height * 0.2)
    page.wait_for_function("""() => {
        const gl = window.__ocean(), program = gl.getParameter(gl.CURRENT_PROGRAM);
        const mouse = gl.getUniform(program, gl.getUniformLocation(program, 'uMouse'));
        return mouse[0] > 0.6 && mouse[1] > 0.6;
    }""")
    page.locator("#guide .guide-action[href='#partners']").click()
    expect(page.locator("#partners")).to_be_visible()
    open_navigation(page)
    page.locator("#theme-toggle").click()
    expect(page.locator("html")).to_have_attribute("data-theme", "dark")
    expect(background.locator("canvas")).to_have_count(1)
    if page.locator("#glass-menu-close").is_visible():
        page.locator("#glass-menu-close").click()
    page.set_viewport_size({"width": width, "height": height - 100})
    page.wait_for_function("height => document.querySelector('#platform-background canvas').height === height",
                           arg=height - 100)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors


def test_reduced_motion_removes_the_canvas_and_remounts_on_preference_change(page, live_server):
    page.emulate_media(reduced_motion="reduce")
    enter_public_site(page, live_server)
    background = page.locator("#platform-background")
    expect(background).to_have_attribute("data-state", "reduced-motion")
    expect(background.locator("canvas")).to_have_count(0)
    page.locator("#guide .guide-action[href='#partners']").click()
    expect(page.locator("#partners")).to_be_visible()
    page.emulate_media(reduced_motion="no-preference")
    expect(background.locator("canvas")).to_have_count(1)
    page.emulate_media(reduced_motion="reduce")
    expect(background.locator("canvas")).to_have_count(0)
    expect(background).to_have_attribute("data-state", "reduced-motion")


def test_unavailable_webgl_does_not_block_the_platform(page, live_server):
    page.emulate_media(reduced_motion="no-preference")
    page.add_init_script("""(() => {
        const original = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {
            return type.startsWith('webgl') ? null : original.call(this, type, ...args);
        };
    })()""")
    enter_public_site(page, live_server)
    expect(page.locator("#platform-background")).to_have_attribute("data-state", "fallback")
    expect(page.locator("#platform-background canvas")).to_have_count(0)
    page.locator("#guide .guide-action[href='#partners']").click()
    expect(page.locator("#partners")).to_be_visible()


def test_lost_context_removes_animation_without_blocking_controls(page, live_server):
    page.emulate_media(reduced_motion="no-preference")
    enter_public_site(page, live_server)
    page.locator("#platform-background canvas").evaluate("canvas => canvas.getContext('webgl2').getExtension('WEBGL_lose_context').loseContext()")
    expect(page.locator("#platform-background")).to_have_attribute("data-state", "fallback")
    expect(page.locator("#platform-background canvas")).to_have_count(0)
    page.locator("#guide .guide-action[href='#partners']").click()
    expect(page.locator("#partners")).to_be_visible()
