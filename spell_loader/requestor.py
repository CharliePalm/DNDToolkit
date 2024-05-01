import requests

base_url = 'http://dnd5e.wikidot.com'
def get_spell_html(href):
    '''
    makes a synchronous request to get a spell's html body
    it would be much faster to wrap this in an async block, but seeing as how this is intended to be used for scraping, we don't want to frustrate the server
    '''
    r = requests.get(base_url + href)
    if r.status_code != 200:
        print('error in response')
        print(r)
        exit(0)
    return r.text