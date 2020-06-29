# coding: utf-8
GATEWAY_URL = "https://gateway.itc.u-tokyo.ac.jp/dana-na/auth/url_default/welcome.cgi"

def pass_gate_way(driver, url=GATEWAY_URL, 
                  submit="btnSubmit_6",confirm="btnContinue" **kwargs):
    """
    Pass the gateway server to 
    @params driver  : 
    @params url     : gateway server's url (ex.https://gateway.itc.u-tokyo.ac.jp/dana-na/auth/url_default/welcome.cgi)
    @params kwargs  : the (id,value) pairs which are necessary for Authentication.
        * username=<username>
        * password=<password>
    @params submit  : submit button's id.
    @params confirm : confirm button's id. (if necessary),
    """
    driver.get(url)
    for id, value in kwargs.items():
        driver.find_element_by_id(id).send_keys(value)
    driver.find_element_by_id(submit).click()
    if confirm is not None:
        driver.find_element_by_id(confirm).click()
    return driver