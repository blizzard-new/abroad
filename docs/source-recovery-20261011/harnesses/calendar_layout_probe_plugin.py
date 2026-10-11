"""External diagnostic only: evaluate proposed scoped source-banner CSS at frozen SHA."""
def pytest_runtest_call(item):
    if 'test_calendar_appears_first_and_tools_still_work' not in item.name:return
    page=item.funcargs['page']
    page.add_init_script('''document.addEventListener("DOMContentLoaded", () => {
      const style=document.createElement("style");
      style.textContent="body:not(.public-exploration-mode) #catalogue-source-status {display:none}";
      document.head.append(style);
    });''')
