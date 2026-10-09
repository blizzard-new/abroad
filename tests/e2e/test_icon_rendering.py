"""Background icon rendering must preserve an in-flight pointer target."""
from playwright.sync_api import expect

from .conftest import enter_public_site


def test_background_icon_render_does_not_discard_mobile_menu_click(page, live_server):
    page.set_viewport_size({"width": 390, "height": 956})
    page.emulate_media(reduced_motion="reduce")
    enter_public_site(page, live_server, "partners")
    toggle = page.locator("#glass-menu-toggle")
    box = toggle.bounding_box()
    page.evaluate('window.originalMenuIcon = document.querySelector("#glass-menu-toggle svg")')
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.evaluate("initIcons()")
    page.mouse.up()
    expect(toggle).to_have_attribute("aria-expanded", "true")
    expect(page.locator("#glass-navigation")).to_be_visible()
    assert page.evaluate("window.originalMenuIcon.isConnected")


def test_icon_render_preserves_existing_nodes_and_renders_new_or_changed_icons(page, live_server):
    enter_public_site(page, live_server, "partners")
    result = page.evaluate('''() => {
        const existing = document.querySelector('#glass-menu-toggle svg');
        const fixture = document.createElement('div');
        fixture.innerHTML = '<i data-lucide="heart" aria-label="New icon"></i>';
        document.body.append(fixture);
        initIcons();
        const first = fixture.querySelector('svg');
        const initial = Boolean(first?.classList.contains('lucide-heart'));
        first.setAttribute('data-lucide', 'star');
        initIcons();
        const second = fixture.querySelector('svg');
        const result = {initial, changed: second?.classList.contains('lucide-star'),
            accessible: second?.getAttribute('aria-label') === 'New icon',
            existingPreserved: existing.isConnected,
            pending: document.querySelectorAll('[data-lucide-pending]').length};
        fixture.remove();
        return result;
    }''')
    assert result == {"initial": True, "changed": True, "accessible": True,
                      "existingPreserved": True, "pending": 0}
