"""Inspect GeoData for already visually approved named photos; no promotion."""
import json,requests
from urllib.parse import unquote,urlsplit
from capture_tku_asset_batch import B,request
def main():
    target=B/'commons_photo_coordinate_candidates.json'
    if target.exists():return
    covered={r['id'] for r in json.loads((B/'campus_location_manifest.json').read_text())}
    photos=[r for r in json.loads((B/'campus_asset_manifest.json').read_text()) if r['id'] not in covered and 'commons.wikimedia.org/wiki/File:' in r['source_url']]
    titles={r['id']:unquote(urlsplit(r['source_url']).path.split('/wiki/',1)[1]).replace('_',' ') for r in photos}
    url=requests.Request('GET','https://commons.wikimedia.org/w/api.php',params=dict(action='query',format='json',titles='|'.join(titles.values()),prop='coordinates',colimit='max')).prepare().url
    source=request(url,'commons');source['institution_file_titles']=titles;target.write_text(json.dumps(source,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(http_status=source.get('http_status'),candidates=[dict(title=p['title'],coordinates=p.get('coordinates',[])) for p in source.get('response',{}).get('query',{}).get('pages',{}).values()]),ensure_ascii=False))
if __name__=='__main__':main()
