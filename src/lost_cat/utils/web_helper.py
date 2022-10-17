import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def parse_aans(text: str) -> dict:
    """ Reads the aans glossary and returns the terms found"""
    _soup = BeautifulSoup(text, 'html.parser')
    _content = _soup.find_all(id='page-content')

    for _con_blk in _content:
        _def_blk = _con_blk.find_all('p')
        for _p_blk in _def_blk:
            #print(_p_blk)

            _term_blk = _p_blk.find("strong")
            _term = _term_blk.get_text()
            _term = ' '.join(_term.split())

            _defn = _p_blk.get_text()
            _defn = ' '.join(_defn.split())
            _defn = _defn.replace(_term, "").replace("-","")

            yield (_term.lower(), _defn)

def parse_mayfield(text: str) -> dict:
    """ Will process the response from the Mayfeild site"""
    _soup = BeautifulSoup(text, 'html.parser')
    _content = _soup.find_all('p')

    for _con_blk in _content:
        try:
            _term_blk = _con_blk.find('b')
            if not _term_blk:
                continue
            _term = _term_blk.get_text().replace(":","")
            _term = ' '.join(_term.split())

            _defn = _con_blk.get_text().strip()
            _defn = ' '.join(_defn.split())
            _defn = _defn.replace(":","").replace(_term, "").strip()

            yield (_term.lower(), _defn)

        except Exception as ex:
            print(ex)

def parse_nursecepts(text: str) -> dict:
    """ Will process the bursecepts site"""
    soup = BeautifulSoup(text, 'html.parser')
    _table = soup.find(id='tablepress-55')
    _defns = {}
    _term = None
    for _row in _table.find_all('tr'):
        try:

            _r_term = _row.find_all('td', {'class':'column-1'})
            _r_defn = _row.find_all('td', {'class':'column-2'})

            if not _r_term or not _r_defn:
                continue

            _c_term = _r_term[0].get_text()
            _c_defn = _r_defn[0].get_text()
            _c_defn = ' '.join(_c_defn.split())

            if _c_term:
                _c_term = ' '.join(_c_term.split())
                _defns[_c_term.lower()] = []
                _term = _c_term

            if _c_defn:
                yield (_term.lower(), _c_defn)

        except Exception as ex:
            print(ex)

def parse_harvard(text: str) -> dict:
    """Will process the Harvard site"""
    _soup = BeautifulSoup(text, 'html.parser')
    _content = _soup.find_all('p')

    for _con_blk in _content:
        try:
            _term_blk = _con_blk.find('strong')
            if not _term_blk:
                continue
            _term = _term_blk.get_text().replace(":","")
            _term = ' '.join(_term.split())

            _defn = _con_blk.get_text().strip()
            _defn = ' '.join(_defn.split())
            _defn = _defn.replace(":","").replace(_term, "").strip()

            yield (_term.lower(), _defn)
        except Exception as ex:
            print(ex)

def parse_schlich(text: str) -> dict:
    """Will process the Harvard site"""
    _soup = BeautifulSoup(text, 'html.parser')
    _content = _soup.find_all('li')

    for _con_blk in _content:
        try:
            _term_blk = _con_blk.find('strong')
            if not _term_blk:
                continue
            _term = _term_blk.get_text().replace(":","")
            _term = ' '.join(_term.split())

            _defn = _con_blk.get_text().strip()
            _defn = ' '.join(_defn.split())
            _defn = _defn.replace(":","").replace(_term, "").strip()

            yield (_term.lower(), _defn)
        except Exception as ex:
            print(ex)

def parse_kinston(text: str) -> dict:
    """Will process the Harvard site"""
    _soup = BeautifulSoup(text, 'html.parser')

    _content = _soup.find_all('div', {"class": "views-row"})

    for _con_blk in _content:
        try:
            _field_item = _con_blk.find_all("div", {"class": "field-item"})
            _field_body = _con_blk.find_all("div", {"class": "field-name-body"})

            if not _field_item:
                continue

            _term = _field_item[0].get_text().replace(":","")
            _term = ' '.join(_term.split())

            _defn = _field_body[0].find("p").get_text().strip()
            _defn = ' '.join(_defn.split())
            _defn = _defn.replace(":","").replace(_term, "").strip()

            yield (_term.lower(), _defn)

        except Exception as ex:
            print(ex)

def parse_wikiabbrvs(text: str) -> dict:
    """Will process the Wiki Abbrvs and pivot the terms"""
    _soup = BeautifulSoup(text, 'html.parser')
    _table = _soup.find("table", {"class": "wikitable"})
    _defns = {}
    _term = None
    for _row in _table.find_all('tr'):
        try:
            _cols = _row.find_all("td")
            print(_cols)

            if len(_cols) >= 2:
                _r_abbrv = _cols[0].get_text()
                _r_terms = _cols[1].get_text()

                if not _r_terms or not _r_abbrv:
                    continue

                yield (_r_abbrv.lower(), _r_terms)

        except Exception as ex:
            print(ex)