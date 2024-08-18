import requests
from shared.model import CharacterClass

base_url = 'http://dnd5e.wikidot.com'
def get_spell_html(href):
    '''
    makes a synchronous request to get a spell's html body
    it would be much faster to wrap this in an async block, but seeing as how this is intended to be used for scraping, we don't want to frustrate the server
    '''
    return make_get_request(base_url + href)

def get_class_html(charClass: CharacterClass):
    '''
    makes a synchronous request to get a class's html body
    it would be much faster to wrap this in an async block, but seeing as how this is intended to be used for scraping, we don't want to frustrate the server
    '''
    print(charClass.lower().replace(' ', '-'))
    return make_get_request(base_url + '/' + charClass.lower().replace(' ', '-'))

def make_get_request(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        print('error in response')
        print(r)
        return None
    return r.text