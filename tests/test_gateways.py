# coding: utf-8
from gummy import journals
from gummy.utils import get_driver
from gummy.journals import whichJournal

def _test_gateways(gateway, url="https://doi.org/10.1038/171737a0", **kwargs):
    journal_type = whichJournal(url)
    
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

def test_utokyo_gateways():
    _test_gateways(gateway="utokyo")