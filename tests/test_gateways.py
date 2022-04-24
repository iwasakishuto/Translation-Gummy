# coding: utf-8
from typing import Union

from gummy import journals
from gummy.gateways import GummyAbstGateWay
from gummy.journals import whichJournal
from gummy.utils import check_environ, get_driver


def _test_gateways(db, gateway: Union[str, GummyAbstGateWay], journal_type: str = "nature", **gatewaykwargs):
    url: str = db.journals.get(journal_type)[0]

    # Crawler with gateway.
    gateway_crawler: GummyAbstGateWay = journals.get(identifier=journal_type, gateway=gateway)
    is_ok, _ = check_environ(
        required_keynames=gateway_crawler.gateway.get_required_keynames(journal_type=journal_type),
        required_env_varnames=gateway_crawler.gateway.get_required_env_varnames(journal_type=journal_type),
        verbose=1,
        **gatewaykwargs,
    )
    if is_ok:
        with get_driver() as driver:
            gateway_title, gateway_contents = gateway_crawler.get_contents(url=url, driver=driver, **gatewaykwargs)

        # Crawler without gateway.
        useless_crawler = journals.get(identifier=journal_type, gateway="useless")
        with get_driver() as driver:
            useless_title, useless_contents = useless_crawler.get_contents(url=url, driver=driver)

        assert useless_title == gateway_title
        assert len(useless_contents) < len(gateway_contents)


def test_utokyo_gateways(db):
    _test_gateways(db=db, gateway="utokyo")
