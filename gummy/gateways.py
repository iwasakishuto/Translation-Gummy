# coding: utf-8
import os
import json
from collections import OrderedDict
from abc import ABCMeta, abstractmethod
from kerasy.utils import toBLUE, toGREEN, toACCENT

from .utils import GummyImprementationWarning
from .utils import (try_find_element_click, try_find_element_send_keys, 
                    pass_forms, click)
from .utils import TRANSLATION_GUMMY_ENVNAME_PREFIX, DOTENV_PATH, load_environ
from .utils import mk_class_get

class GummyAbstGateWay(metaclass=ABCMeta):
    """
    It is not possible to define all the patterns as the usage of gateway differs for each service and each journal. 
    Therefore, if you don't use `UTokyoGateWay`, define a new gateway class (please inherit this class with `passthrough` method).
    I would also appreciate if you could pull request about your own class.

    ```python
    # How to inherit `GummyAbstGateWay` class
    from gummy.gateways import GummyAbstGateWay
    class myGateWay(GummyAbstGateWay):
        def __init__(self, url, ...)
            super().__init__(url)
            :
    ```
    """
    def __init__(self, url=None, verbose=1, env_varnames=[], dotenv_path=DOTENV_PATH):
        if not hasattr(self, "passthrough"):
            attribute_error_msg = f"module {toGREEN(self.__class__.__name__)} has no attribute {toBLUE('passthrough')}"
            raise AttributeError(attribute_error_msg + GummyAbstGateWay.__doc__)
        self.url = url
        self.verbose = verbose
        self.env_varnames = [f"{TRANSLATION_GUMMY_ENVNAME_PREFIX}_{self.__class__.__name__.replace('GateWay', '').upper()}_GATEWAY_{v.upper()}" for v in env_varnames]
        load_environ(dotenv_path=dotenv_path, env_varnames=self.env_varnames)

    @abstractmethod
    def passthrough(self, driver, **kwargs):
        return driver

    def pass2journal(self, driver, journal, **kwargs):
        driver = {
            "" : self.passthrough
        }.get(journal, self.passthrough)(driver, **kwargs)
        return driver

class UTokyoGateWay(GummyAbstGateWay):
    def __init__(self, verbose=1, username=None, password=None):
        super().__init__(
            url="https://gateway.itc.u-tokyo.ac.jp/dana-na/auth/url_default/welcome.cgi", 
            verbose=verbose,
            env_varnames=["username", "password"]
        )

    def passthrough(self, driver, username=None, password=None, **gatewaykwargs):
        """
        ```html
        <input id="username"    type="text"     name="username">
        <input id="password"    type="password" name="password">
        <input id="btnSubmit_6" type="submit"   name="btnSubmit">
        ~~~ next page ~~~
        <input id="btnContinue" type="submit"   name="btnContinue">
        ```
        """
        kwargs = OrderedDict(**{
            "username"    : username or os.getenv("TRANSLATION_GUMMY_UTOKYO_GATEWAY_USERNAME"),
            "password"    : password or os.getenv("TRANSLATION_GUMMY_UTOKYO_GATEWAY_PASSWORD"),
            "btnSubmit_6" : click,
            "btnContinue" : click,
        })
        kwargs.update(gatewaykwargs)
        driver.get(url=self.url)
        driver = pass_forms(driver, **kwargs)
        return driver

all = TranslationGummyGateWays = {
    "utokyo" : UTokyoGateWay,
}

get = mk_class_get(
    all_classes=TranslationGummyGateWays,
    gummy_abst_class=[GummyAbstGateWay],
    genre="gateways"
)