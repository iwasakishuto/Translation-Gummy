#coding: utf-8
""" Use an external module.
$ pip install requests PyMySQL -t ./src
$ rm src/*dist-info
$ rm src/bin
$ cd src && zip -r ../gummy.zip . && cd ../
"""
import re
import os
import json
import logging
import urllib
import boto3
import requests
import pymysql

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def getSlackBotUserAccessToken(team_id):
    try:
        conn = pymysql.connect(
            host   = os.environ["AWS_RDS_HOST_NAME"], # os.environ["AWS_RDS_PROXY_NAME"],
            port   = int(os.environ["AWS_RDS_PORT_NUM"]),
            user   = os.environ["AWS_RDS_USER_NAME"],
            db     = os.environ["AWS_RDS_DATABASE_NAME"],
            passwd = os.environ["AWS_RDS_PASSWORD"],
            connect_timeout=5,
            ssl={"fake_flag_to_enable_tls":True},
        )
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(f'SELECT team_id, access_token FROM {os.environ["AWS_RDS_TABLE_NAME"]} WHERE team_id="{team_id}"')
            result = cursor.fetchall()
            # Get the latest Access Token.
            slack_access_token = result[-1].get("access_token")
    except:
        slack_access_token = None
    return slack_access_token

def is_invalid_event(slack_event):
    event = slack_event.get("event")
    return is_bot(event) or (not is_app_mention(event)) or (slack_event.get("token")!=os.environ["SLACK_BOT_VERIFY_TOKEN"])

def is_bot(event):
    # return slack_event.get("event").get("subtype") == "bot_message"
    return event.get("bot_id") is not None

def is_app_mention(event):
    return event.get("type", "") == "app_mention"
    
def lambda_handler(slack_event, context):
    logging.info(json.dumps(slack_event))

    # Event API authentication (Required to be considered End Point)
    if "challenge" in slack_event: 
        return slack_event.get("challenge")
    # Filter the slack event.
    if is_invalid_event(slack_event):
        return "invalid"

    slack_access_token = getSlackBotUserAccessToken(team_id=slack_event["team_id"])
    channel = slack_event["event"]["channel"]
    ts      = slack_event["event"]["ts"]
    text    = slack_event["event"]["text"]
    if slack_access_token is None:
        return "Couldn't get the slack token."
    # # TODE: Only react to @gummy -> Use 'app_mention' Event Subscriptions to solve it.
    # if re.match(pattern=r"^<(@U.*?)>", string=text):
    match = re.search(pattern=r"(?:-T|--translate)\s(.*)", string=text)
    translator = match.group(1) if match else "deepl"        
    urls = re.findall(pattern=r"<(https?://.+?)>", string=text)
    if len(urls)>0:
        postMsg2slackCh(message="translating...", channel=channel, ts=ts, slack_access_token=slack_access_token)
    for url in urls:
        msg = journal2url(journal_url=url, translator=translator)
        postMsg2slackCh(message=msg, channel=channel, ts=ts, slack_access_token=slack_access_token)
    return "OK"

def journal2url(journal_url, translator="deepl"):
    """ Post requests to Translation-Gummy Website to get s3url."""
    ret = requests.post(
        url=os.environ["TRANSLATION_GUMMY_WEBURL"],
        data=json.dumps({
            "url": journal_url, 
            "translator": translator,
        }), 
        headers={"content-type": "application/json"},
    )
    if ret.ok:
        s3url = ret.json().get("s3url")
        add_info = ret.json().get("add_info")
        if add_info=="success":
            msg = s3url
        else:
            msg = s3url + "\n" + add_info
    else:
        contact_info = "Please install <https://github.com/iwasakishuto/Translation-Gummy/|Translation-Gummy> to try by yourself, or report this error to <https://twitter.com/cabernet_rock/|the developer>."
        msg  = f"[{ret.status_code}] {ret.reason}" + "\n" + contact_info
    return msg

def postMsg2slackCh(message, channel, ts, slack_access_token):
    req = urllib.request.Request(
        url="https://slack.com/api/chat.postMessage",
        data=json.dumps({
            "token"     : os.environ["SLACK_BOT_VERIFY_TOKEN"],
            "channel"   : channel,
            "text"      : message,
            "thread_ts" : ts,
        }).encode("utf-8"),
        method="POST", 
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {slack_access_token}"
        },
    )
    ret = urllib.request.urlopen(req)
    logging.info(ret.read().decode("utf-8"))
