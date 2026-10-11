"""Review-only fault injection: fail the two live CGU Google Sheets reads."""
def pytest_sessionstart(session):
    import requests
    original = requests.get
    def failed_source(url, *args, **kwargs):
        if url.startswith('https://docs.google.com/spreadsheets/d/') and '/gviz/tq' in url:
            raise requests.HTTPError('Review-only controlled CGU source outage')
        return original(url, *args, **kwargs)
    requests.get = failed_source
