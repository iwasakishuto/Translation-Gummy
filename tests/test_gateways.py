# coding: utf-8
from gummy import journals
from gummy.utils import get_driver
from gummy.journals import whichJournal


def _test_gateways(db, gateway, journal_type="nature", **kwargs):
    url = db.journals.get(journal_type)
    pre_journal_type = whichJournal(url)

    assert journal_type == pre_journal_type
    
    # Crawler without gateway.
    useless_crawler = journals.get(identifier=journal_type, gateway="useless")
    with get_driver() as driver:
        useless_title, useless_contents = useless_crawler.get_contents(url=url, driver=driver)

    # Crawler with gateway.
    gateway_crawler = journals.get(identifier=journal_type, gateway=gateway)
    with get_driver() as driver:
        gateway_title, gateway_contents = gateway_crawler.get_contents(url=url, driver=driver)
        
    assert useless_title == gateway_title
    assert len(useless_contents) < len(gateway_contents)

def test_utokyo_gateways(db):
    _test_gateways(db=db, gateway="utokyo")