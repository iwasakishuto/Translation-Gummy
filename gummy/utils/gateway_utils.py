# coding: utf-8
import json
from kerasy.utils import toBLUE, toGREEN, toACCENT
from selenium.common.exceptions import NoSuchElementException

def pass_gate_way(driver, url, submit_id, confirm_id=None, **kwargs):
    """
    Pass the gate way server.
    @params driver  : web driver.
    @params url     : gateway server's url (ex. "https://gateway.itc.u-tokyo.ac.jp/dana-na/auth/url_default/welcome.cgi")
    @params kwargs  : the (id,value) pairs which are necessary for Authentication.
        * username=<username>
        * password=<password>
    @params submit  : submit button's id.
    @params confirm : confirm button's id. (if necessary),
   
    example.)
    =========================================================
    ```html
    <input id="username"    type="text"     name="username">
    <input id="password"    type="password" name="password">
    <input id="btnSubmit_6" type="submit"   name="btnSubmit">
    ~~~ next page ~~~
    <input id="btnContinue" type="submit"   name="btnContinue">
    ```
    
    ```python    
    from gummy.utils import get_driver
    from gummy.journal import pass_gate_way
    
    with get_driver() as driver:
        drver = pass_gate_way(
            drive = driver
            url = GATEWAY_URL,
            submit = "btnSubmit_6",
            confirm = "btnContinue",
            username = USERNAME,
            password = PASSWORD,            
        )
        :
        
    """
    print(f"""{toACCENT('GateWay Information:')}
    * gateway url : {toBLUE(url)}
    * You will send""" + "".join(f"""
        - {toGREEN(val)} in the form with id='{toBLUE(id)}'""" for id,val in kwargs.items()) + f"""
    * click id='{toGREEN(submit_id)}' button to submit.
    * click id='{toGREEN(confirm_id)}' button to confirm.
    """)
    driver.get(url)
    # Fill in all form fields.
    for id, value in kwargs.items():
        try:
            driver.find_element_by_id(id).send_keys(value)
        except NoSuchElementException:
            print(f"Unable to locate element with id='{id}'")
    driver.find_element_by_id(submit_id).click()
    if confirm_id is not None:
        try:
            driver.find_element_by_id(confirm_id).click()
        except NoSuchElementException:
            print(f"Unable to locate element with id='{confirm_id}'.")
    return driver