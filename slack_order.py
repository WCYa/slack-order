import os
import secrets
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# 訂單資訊
# "ts" : {
#     "order_name": "XXX",
#     "order_creator": "user_id",
#     "order_info": "...",
#     "order_state": ":large_green_circle: 點餐中",
#     "order_img": "https://"
# }
orders = {}
# 訂單詳細資訊
# "ts" : {
#     "item_name" : {
#         "price": "50",
#         "amount": "3",
#         slack_users: {
#             "user1_id": "1",
#             "user2_id": "2"
#         },
#         users: {
#             "user1": "1",
#             "user2": "1"
#         }
#     }
# }
order_details = {}

ORDER_STATE = (
    ":large_green_circle: 點餐中",
    ":red_circle: 已收單"
)

imgs = [
  "https://s3-media2.fl.yelpcdn.com/bphoto/DawwNigKJ2ckPeDeDM7jAg/o.jpg"
]


def isNaturalNumber(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer() and float(n) >= 0


def isPositiveNumber(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer() and float(n) > 0


def getTextFromViewState(view, block_id):
    return view['state']['values'][block_id]['text']['text']


def getValueFromViewState(view, block_id, action_id):
    return view['state']['values'][block_id][action_id]['value']


def getSelectedFromViewState(view, block_id, action_id):
    return view["state"]["values"][block_id][action_id]["selected_option"]["text"]["text"]


def getSelectedUserFromViewState(view, block_id, action_id):
    return view["state"]["values"][block_id][action_id]["selected_user"]


def getSelectedUsersFromViewState(view, block_id, action_id):
    return view["state"]["values"][block_id][action_id]["selected_users"]


def getChannelIdFromViewPrivateMetadata(view):
    '''從 private_metadata 讀取 message 傳來的 channel_id'''
    return view['private_metadata'].split(',')[0]


def getMessageTsFromViewPrivateMetadata(view):
    '''從 private_metadata 讀取 message 傳來的 message_ts'''
    return view['private_metadata'].split(',')[1]


def getTsFromMessageBody(body):
    return body['container']['message_ts']


def getChannelIdFromMessageBody(body):
    return body['container']['channel_id']


def getUserIdFromMessageBody(body):
    return body['user']['id']


def getMetadataEventPayloadFromMessageBody(body):
    return body["message"]["metadata"]["event_payload"]


def getOrderStateFromMessageBody(body):
    return body["message"]["metadata"]["event_payload"]["order_state"]


def getChannelIdFromOpenNewOrderModal(view):
    return view["private_metadata"]


def getOpenNewOrderModal(channel_id):
    '''開啟新訂單的 modal view'''
    return {
        "type": "modal",
        "callback_id": "open_new_order_modal",
        "title": {"type": "plain_text", "text": "開啟一個新訂單 "},
        "submit": {"type": "plain_text", "text": "送出"},
        "private_metadata" : f"{ channel_id }",
        "blocks": [
            {
                "block_id": "order_name",
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "order_name_input"
                },
                "label": {
                    "type": "plain_text",
                    "text": "訂單名稱:"
                }
            },
            {
                "block_id": "order_info",
                "type": "input",
                "label": {"type": "plain_text", "text": "請寫下訂單資訊:"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "order_info_input",
                    "multiline": True
                }
            },
            {
                "block_id": "order_img",
                "type": "input",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "order_img_input"
                },
                "label": {
                    "type": "plain_text",
                    "text": "小圖片連結:"
                },
                "optional": True
            }
        ]
    }


def getOrderMessageBlocks(kwargs):
    '''Order Message'''
    global imgs
    order_name = kwargs["order_name"]
    order_creator = kwargs["order_creator"]
    order_info = kwargs["order_info"]
    order_img = kwargs["order_img"] if kwargs["order_img"] else secrets.choice(imgs)
    order_state = kwargs.get("order_state", ORDER_STATE[0])
    order_total_amount = kwargs.get("order_total_amount", "0")
    order_total_price = kwargs.get("order_total_price", "0")

    return [
        {
            "type": "header",
            "block_id": "order_name",
            "text": {
                "type": "plain_text",
                "text": f"{ order_name }"
            }
        },
        {
            "type": "section",
            "block_id": "order_creator",
            "text": {
                "type": "mrkdwn",
                "text": f"訂單建立者: <@{ order_creator }>"
            }
        },
        {
            "type": "section",
            "block_id": "order_info",
            "text": {
                "type": "mrkdwn",
                "text": f"{ order_info }"
            },
            "accessory": {
                "type": "image",
                "image_url": f"{ order_img }",
                "alt_text": "random image"
            }
        },
        {
            "type": "section",
            "block_id": "order_message_modify",
            "text": {
                "type": "plain_text",
                "text": f"{ order_state }"
            },
            "accessory": {
                "type": "overflow",
                "action_id": "order_message_modify",
                "options": [
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "修改訂單資訊"
                        },
                        "value": "modify_order_info"
                    },
                    {
                        "text": {
                            "type": "plain_text",
                            "text": "修改品項金額"
                        },
                        "value": "modify_item_price"
                    }
                ]
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "block_id": "order_total",
            "text": {
                "type": "mrkdwn",
                "text": f"*共 { order_total_amount } 項，訂單金額總計: { order_total_price }*"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "新增品項"
                    },
                    "value": "new_item",
                    "action_id": "new_item"
                },
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "結案"
                    },
                    "action_id": "end_order"
                }
            ]
        }
    ]


def getOrderMessageBlocksWithItems(**kwargs):
    '''返回目前 order_message 和訂單清單'''
    order_details = kwargs.get("order_details", {})

    blocks = getOrderMessageBlocks(kwargs)
    # blocks 插入目前 order_details 資訊
    for item in sorted(order_details.keys()):
        slack_users_detail = '、'.join('<@{}> x{}'.format(*p) for p in order_details[item].get('slack_users', {}).items())
        users_detail = '、'.join('{} x{}'.format(*p) for p in order_details[item].get('users', {}).items())
        if slack_users_detail and users_detail:
            all_users = '、'.join((slack_users_detail, users_detail))
        else:
            all_users = slack_users_detail if slack_users_detail else users_detail

        blocks.insert(5, {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"${ order_details[item]['price'] } { item } x{ order_details[item]['amount'] } ({ all_users }) "
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Choose"
                },
                "value": item,
                "action_id": "add_item_action"
            }
        })
    return blocks


def ifMessageIsNoneReloadMetadata(body):
    '''先確認是否全域變數 orders 為空，是的話將其 Message Metadata 讀進全域變數 orders, order_details'''
    global orders, order_details
    ts = getTsFromMessageBody(body)
    if not orders.get(ts):
        event_payload = getMetadataEventPayloadFromMessageBody(body)
        orders[ts] = {
            "order_name": event_payload["order_name"],
            "order_creator": event_payload["order_creator"],
            "order_info": event_payload["order_info"],
            "order_state": event_payload["order_state"],
            "order_img": event_payload["order_img"]
        }
        order_details[ts] = event_payload["order_details"]


def getAddItemModalBlocks(**kwargs):
    '''品項設定 modal blocks'''
    item_price_mrkdwn = kwargs.get("item_price_mrkdwn", None)
    item_price = kwargs.get("item_price", "")
    item_name = kwargs.get("item_name", "")
    item_amount = kwargs.get("item_amount", "")
    item_slack_users = kwargs.get("item_slack_users", [])
    item_users = kwargs.get("item_users", "")
    current_item_users = kwargs.get("current_item_users", "目前的使用者: None")

    blocks = [
        {
            "type": "input",
            "block_id": "item_name",
            "label": {
                "type": "plain_text",
                "text": "品項 :meat_on_bone: :"
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "item_name_input",
                "initial_value": item_name
            }
        },
        {
            "type": "input",
            "block_id": "item_amount",
            "label": {
                "type": "plain_text",
                "text": "數量 :1234: :"
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "item_amount_input",
                "initial_value": item_amount
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "使用者"
            }
        },
        {
            "type": "input",
            "block_id": "item_slack_users",
            "optional": True,
            "element": {
                "type": "multi_users_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select Users"
                },
                "action_id": "item_slack_users_input",
                "initial_users": item_slack_users
            },
            "label": {
                "type": "plain_text",
                "text": "Slack 使用者:"
            }
        },
        {
            "type": "input",
            "block_id": "item_users",
            "optional": True,
            "element": {
                "type": "plain_text_input",
                "action_id": "item_users_input",
                "initial_value": item_users
            },
            "label": {
                "type": "plain_text",
                "text": "使用者(使用逗號間隔):"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "plain_text",
                "text": current_item_users,
                "emoji": False
            }
        }
    ]

    if not item_price_mrkdwn:
        blocks.insert(0, {
            "type": "input",
            "block_id": "item_price",
            "label": {
                "type": "plain_text",
                "text": "金額 :heavy_dollar_sign: :"
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "item_price_input",
                "initial_value": item_price
            }
        })
    else:
        blocks.insert(0, {
            "block_id": "item_price",
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f" *金額 :heavy_dollar_sign: : { item_price_mrkdwn }*"
            }
        })

    return blocks


def getMessageMetadataPayload(kwargs):
    '''orders 和 order_details 組成 Message metadata'''
    payload = {}
    payload["order_name"] = kwargs["order_name"]
    payload["order_info"] = kwargs["order_info"]
    payload["order_state"] = kwargs.get("order_state", ORDER_STATE[0])
    payload["order_creator"] = kwargs["order_creator"]
    payload["order_img"] = kwargs["order_img"]
    payload["order_details"] = kwargs.get("order_details", {})
    return payload


def getMessageMetadata(**kwargs):
    payload = getMessageMetadataPayload(kwargs)
    metadata = {
        "event_type": "general_event",
        "event_payload": payload
    }
    return metadata


def checkPermission(channel_id, ts, body, client):
    global orders
    if orders[ts]["order_state"] == ORDER_STATE[1] and body['user']['id'] != orders[ts]['order_creator']:
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=ts,
            text=f"已收單，<@{ body['user']['id'] }>請聯繫訂單建立者(<@{ orders[ts]['order_creator'] }>)"
        )
        return False
    return True


def isOrderCreator(channel_id, ts, body, client):
    global orders
    if body['user']['id'] != orders[ts]["order_creator"]:
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=ts,
            text=f"<@{ body['user']['id'] }> 只有訂單建立者(<@{ orders[ts]['order_creator'] }>)能修改資訊及結案"
        )
        return False
    return True


def getPrivateMetadataFormatString(body):
    return f"{ getChannelIdFromMessageBody(body) },{ getTsFromMessageBody(body) }"


def getOrderTotalPrice(ts):
    global order_details
    total = 0
    for item in order_details.get(ts, {}):
        total += (int(order_details[ts][item]["amount"]) * int(order_details[ts][item]["price"]))
    return str(total)


def getOrderTotalAmount(ts):
    global order_details
    amount = 0
    for item in order_details.get(ts, {}):
        amount += int(order_details[ts][item]["amount"])
    return str(amount)


# Initializes your app with your bot token and socket mode handler
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))


@app.command("/order")
def open_modal(ack, body, client):
    '''指令 /order 開啟新訂單的 modal'''
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view=getOpenNewOrderModal(channel_id=body["channel_id"])
    )


@app.view("open_new_order_modal")
def handle_submission(ack, say, client, view, body):
    '''Handle OpenNewOrderModal submission'''
    global orders, order_details, imgs
    ack()
    order_name = getValueFromViewState(view=view, block_id="order_name", action_id="order_name_input")
    order_info = getValueFromViewState(view=view, block_id="order_info", action_id="order_info_input")
    order_img = getValueFromViewState(view=view, block_id="order_img", action_id="order_img_input")
    order_img = order_img if order_img else secrets.choice(imgs)
    order_creator = getUserIdFromMessageBody(body=body)

    # 將資訊存到 Message metadata > event_payload
    metadata = getMessageMetadata(
        order_name=order_name,
        order_info=order_info,
        order_state=ORDER_STATE[0],
        order_creator=order_creator,
        order_img=order_img,
        order_details={}
    )

    message = say(
        text="order",
        channel=getChannelIdFromOpenNewOrderModal(view=view),
        blocks=getOrderMessageBlocksWithItems(
            order_name=order_name,
            order_creator=order_creator,
            order_info=order_info,
            order_img=order_img,
            order_state=ORDER_STATE[0]
        ),
        metadata=metadata,
        # 不要自動展開連結
        unfurl_links=False
    )

    # 釘選訂單 message
    client.pins_add(channel=message["channel"], timestamp=message["ts"])
    # 新增/更新 訂單資訊到全域變數
    orders[message["ts"]] = {
        "order_name": order_name,
        "order_creator": order_creator,
        "order_info": order_info,
        "order_img": order_img,
        "order_state": ORDER_STATE[0]
    }
    order_details[message["ts"]] = {}


@app.view("add_item")
def handle_submission(ack, view):
    '''監聽訂單新增按鈕開起的 modal view 送出'''
    global orders, order_details
    channel_id = getChannelIdFromViewPrivateMetadata(view)
    message_ts = getMessageTsFromViewPrivateMetadata(view)
    errors = {}
    item = getValueFromViewState(view=view, block_id="item_name", action_id="item_name_input")
    price = getValueFromViewState(view=view, block_id="item_price", action_id="item_price_input") if view['state']['values'].get("item_price", {}) else view["private_metadata"].split(',')[2]
    amount = getValueFromViewState(view=view, block_id="item_amount", action_id="item_amount_input")
    slack_users = getSelectedUsersFromViewState(view=view, block_id="item_slack_users", action_id="item_slack_users_input")
    users = getValueFromViewState(view=view, block_id="item_users", action_id="item_users_input")

    if not isPositiveNumber(price):
        errors["item_price"] = "金額必須是的數字, 且大於0"
    if not isNaturalNumber(amount):
        errors["item_amount"] = "數量必須是數字, 且大於等於0"

    if not slack_users and not users:
        errors["item_slack_users"] = "必須有一個使用者"
        errors["item_users"] = "必須有一個使用者"

    if len(errors) > 0:
        ack(response_action="errors", errors=errors)
        return

    ack()

    # 目前這個品項的使用者
    current_item_slack_users = {}
    current_item_users = {}

    # get current order_detail if exist
    if order_details.get(message_ts, {}).get(item, {}).get("slack_users"):
        current_item_slack_users = order_details[message_ts][item]["slack_users"]
    if order_details.get(message_ts, {}).get(item, {}).get("users"):
        current_item_users = order_details[message_ts][item]["users"]

    for slack_user in slack_users:
        if int(amount) == 0:
            current_item_slack_users.pop(slack_user, None)
        else:
            current_item_slack_users[slack_user] = amount

    if users:
        users = users.split(',')
        for user in users:
            if int(amount) == 0:
                current_item_users.pop(user, None)
            else:
                current_item_users[user] = amount

    # 計算總數
    current_amount = 0
    for value in list(current_item_slack_users.values()):
        current_amount += int(value)
    for value in list(current_item_users.values()):
        current_amount += int(value)
    if current_amount == 0:
        order_details.setdefault(message_ts, {}).pop(item, {})
    else:
        order_details.setdefault(message_ts, {})[item] = {
            "price": price,
            "amount": current_amount,
            "slack_users": current_item_slack_users,
            "users": current_item_users
        }

    blocks = getOrderMessageBlocksWithItems(
        order_name=orders[message_ts]["order_name"],
        order_creator=orders[message_ts]["order_creator"],
        order_info=orders[message_ts]["order_info"],
        order_img=orders[message_ts]["order_img"],
        order_state=orders[message_ts]["order_state"],
        order_total_price=getOrderTotalPrice(message_ts),
        order_total_amount=getOrderTotalAmount(message_ts),
        order_details=order_details[message_ts]
    )

    metadata = getMessageMetadata(
        order_name=orders[message_ts]["order_name"],
        order_creator=orders[message_ts]["order_creator"],
        order_info=orders[message_ts]["order_info"],
        order_img=orders[message_ts]["order_img"],
        order_state=orders[message_ts]["order_state"],
        order_details=order_details[message_ts]
    )

    app.client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text="updated",
        metadata=metadata,
        blocks=blocks
    )


@app.view("modify_order_message_modal")
def handle_submission(ack, view, client):
    global orders, order_details, imgs
    channel_id = getChannelIdFromViewPrivateMetadata(view)
    ts = getMessageTsFromViewPrivateMetadata(view)
    new_order_creator = getSelectedUserFromViewState(view=view, block_id="order_creator", action_id="order_creator_select")

    if orders[ts]["order_creator"] != new_order_creator:
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=ts,
            text=f"訂單建立者<@{ orders[ts]['order_creator'] }>，已將權限轉給<@{ new_order_creator }>"
        )

    orders[ts]["order_creator"] = new_order_creator
    orders[ts]["order_name"] = getValueFromViewState(view=view, block_id="order_name", action_id="order_name_input")
    orders[ts]["order_info"] = getValueFromViewState(view=view, block_id="order_info", action_id="order_info_input")
    orders[ts]["order_img"] = getValueFromViewState(view=view, block_id="order_img", action_id="order_img_input")
    orders[ts]["order_img"] = orders[ts]["order_img"] if orders[ts]["order_img"] else secrets.choice(imgs)
    orders[ts]["order_state"] = getSelectedFromViewState(view=view, block_id="order_state", action_id="order_state_selected")

    blocks = getOrderMessageBlocksWithItems(
        order_name=orders[ts]["order_name"],
        order_creator=orders[ts]["order_creator"],
        order_info=orders[ts]["order_info"],
        order_state=orders[ts]["order_state"],
        order_img=orders[ts]["order_img"],
        order_total_price=getOrderTotalPrice(ts),
        order_total_amount=getOrderTotalAmount(ts),
        order_details=order_details.get(ts, {})
    )

    metadata = getMessageMetadata(
        order_name=orders[ts]["order_name"],
        order_creator=orders[ts]["order_creator"],
        order_info=orders[ts]["order_info"],
        order_state=orders[ts]["order_state"],
        order_img=orders[ts]["order_img"],
        order_details=order_details.get(ts, {})
    )

    client.chat_update(
        channel=channel_id,
        ts=ts,
        text="updated",
        metadata=metadata,
        blocks=blocks
    )
    ack()


@app.view("modify_item_price_modal")
def handle_submission(ack, view, client):
    global orders, order_details
    errors = {}
    channel_id = getChannelIdFromViewPrivateMetadata(view)
    ts = getMessageTsFromViewPrivateMetadata(view)
    item = getSelectedFromViewState(view=view, block_id="modify_item_name", action_id="modify_item_name_select")
    price = getValueFromViewState(view=view, block_id="modify_item_price", action_id="modify_item_price_input")

    if not isPositiveNumber(price):
        errors["modify_item_price"] = "金額必須是的數字, 且大於0"

    if len(errors) > 0:
        ack(response_action="errors", errors=errors)
        return

    order_details[ts][item]["price"] = price

    blocks = getOrderMessageBlocksWithItems(
        order_name=orders[ts]["order_name"],
        order_creator=orders[ts]["order_creator"],
        order_info=orders[ts]["order_info"],
        order_state=orders[ts]["order_state"],
        order_total_price=getOrderTotalPrice(ts),
        order_total_amount=getOrderTotalAmount(ts),
        order_img=orders[ts]["order_img"],
        order_details=order_details[ts]
    )

    metadata = getMessageMetadata(
        order_name=orders[ts]["order_name"],
        order_creator=orders[ts]["order_creator"],
        order_info=orders[ts]["order_info"],
        order_state=orders[ts]["order_state"],
        order_img=orders[ts]["order_img"],
        order_details=order_details[ts]
    )

    client.chat_update(
        channel=channel_id,
        ts=ts,
        text="updated",
        metadata=metadata,
        blocks=blocks
    )
    ack()


# 新增 按鈕
@app.action("new_item")
def new_item_clicked(ack, body, client):
    ack()
    global orders
    ifMessageIsNoneReloadMetadata(body=body)
    ts = getTsFromMessageBody(body)
    channel_id = getChannelIdFromMessageBody(body)

    # 確認是否點餐中，或是否為訂單建立者
    if not checkPermission(channel_id=channel_id, ts=ts, body=body, client=client):
        return

    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "add_item",
            "title": {"type": "plain_text", "text": "新增品項"},
            "submit": {"type": "plain_text", "text": "送出"},
            "private_metadata": getPrivateMetadataFormatString(body=body),
            "blocks": getAddItemModalBlocks(
                item_slack_users=[f"{ body['user']['id'] }"],
                item_amount="1"
                )
        }
    )


@app.action("order_message_modify")
def handle_some_action(ack, client, body, action):
    '''修改訂單資訊按鈕'''
    ack()
    global orders, order_details, imgs
    ifMessageIsNoneReloadMetadata(body)
    channel_id = getChannelIdFromMessageBody(body)
    ts = getTsFromMessageBody(body)
    order_img = orders[ts]["order_img"] if orders[ts]["order_img"] else secrets.choice(imgs)
    order_state = getOrderStateFromMessageBody(body)

    if action["selected_option"]["value"] == "modify_order_info":
        # 判斷是否是訂單建立者
        if not isOrderCreator(channel_id=channel_id, ts=ts, body=body, client=client):
            return

        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "modify_order_message_modal",
                "title": {"type": "plain_text", "text": "修改訂單資訊"},
                "submit": {"type": "plain_text", "text": "修改"},
                "private_metadata": getPrivateMetadataFormatString(body=body),
                "blocks": [
                    {
                        "block_id": "order_creator",
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "訂單建立者:"
                        },
                        "accessory": {
                            "type": "users_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "Select a user"
                            },
                            "action_id": "order_creator_select",
                            "initial_user": orders[ts]["order_creator"]
                        }
                    },
                    {
                        "block_id": "order_name",
                        "type": "input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "order_name_input",
                            "initial_value": orders[ts]["order_name"]
                        },
                        "label": {"type": "plain_text", "text": "訂單名稱:"}
                    },
                    {
                        "block_id": "order_info",
                        "type": "input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "order_info_input",
                            "multiline": True,
                            "initial_value": orders[ts]["order_info"]
                        },
                        "label": {"type": "plain_text", "text": "請寫下訂單資訊:"},
                    },
                    {
                        "block_id": "order_state",
                        "label": {"type": "plain_text", "text": "訂單狀態:"},
                        "type": "input",
                        "element": {
                            "type": "static_select",
                            "action_id": "order_state_selected",
                            "initial_option": {
                                "value": str(ORDER_STATE.index(order_state)),
                                "text": {
                                    "type": "plain_text",
                                    "text": order_state
                                }
                            },
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": ORDER_STATE[0]
                                    },
                                    "value": "0"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": ORDER_STATE[1]
                                    },
                                    "value": "1"
                                }
                            ]
                        }
                    },
                    {
                        "block_id": "order_img",
                        "type": "input",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "order_img_input",
                            "initial_value": order_img
                        },
                        "label": {"type": "plain_text", "text": "小圖片連結:"},
                        "optional": True
                    },
                ]
            }
        )
    elif action["selected_option"]["value"] == "modify_item_price":
        options = []
        # 確認是否點餐中，或是否為訂單建立者
        if not checkPermission(channel_id=channel_id, ts=ts, body=body, client=client):
            return
        # 確認是否有存在品項資料
        if not order_details.get(ts):
            return
        # 產生所有品項的 dictionaries
        for item in order_details[ts]:
            options.append({
                "value": item,
                "text": {
                    "type": "plain_text",
                    "text": item
                }
            })
        options.sort(key=lambda item: item['value'], reverse=True)
        client.views_open(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "modify_item_price_modal",
                "title": {"type": "plain_text", "text": "修改品項金額"},
                "submit": {"type": "plain_text", "text": "修改"},
                "private_metadata": getPrivateMetadataFormatString(body=body),
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "modify_item_name",
                        "element": {
                            "type": "static_select",
                            "placeholder": {
                                "type": "plain_text",
                                "text": "品項"
                            },
                            "options": options,
                            "action_id": "modify_item_name_select",
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "請選擇一個品項:"
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "modify_item_price",
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "modify_item_price_input"
                        },
                        "label": {
                            "type": "plain_text",
                            "text": "品項金額:"
                        }
                    }
                ]
            }
        )


@app.action("add_item_action")
def choose_bt_clicked(ack, client, body, action):
    '''品項 Choose 按鈕 action'''
    ack()
    ifMessageIsNoneReloadMetadata(body)
    global orders, order_details
    item = action['value']
    ts = getTsFromMessageBody(body)
    channel_id = getChannelIdFromMessageBody(body)

    # 確認是否點餐中，或是否為訂單建立者
    if not checkPermission(channel_id=channel_id, ts=ts, body=body, client=client):
        return

    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "add_item",
            "title": {"type": "plain_text", "text": "新增品項"},
            "submit": {"type": "plain_text", "text": "送出"},
            "private_metadata": getPrivateMetadataFormatString(body=body) + f",{ order_details[ts][item]['price'] }",
            "blocks": getAddItemModalBlocks(
                item_price_mrkdwn=order_details[ts][item]["price"],
                item_name=item,
                item_amount="1",
                item_slack_users=[body["user"]["id"]],
                current_item_users=f"目前的使用者: { ','.join(order_details[ts][item]['users']) }"
                )
        }
    )


@app.action("end_order")
def end(ack, body, client):
    ack()
    global orders, order_details
    ifMessageIsNoneReloadMetadata(body)
    channel = getChannelIdFromMessageBody(body)
    ts = getTsFromMessageBody(body)

    if not isOrderCreator(channel_id=channel, ts=ts, body=body, client=client):
        return
    # 沒有品項
    if not order_details[ts]:
        return

    users_total_aggegations = ""  # 統計個人應付金額及所有品項資訊
    users_total_amount = {}  # 計算個人應付金額
    users_total_items = {}  # 個人所點的所有品項
    for item in order_details[ts]:

        item_price = order_details[ts][item].get("price", 0)

        for id in order_details[ts][item].get('slack_users', {}):
            user_item_amount = int(order_details[ts][item]["slack_users"][id])
            user = f"<@{ id }>"
            users_total_amount.setdefault(user, 0)
            users_total_items.setdefault(user, "")
            users_total_amount[user] += (int(item_price) * user_item_amount)
            if users_total_items[user]:
                users_total_items[user] += f"、{ item }(${ item_price })*{ user_item_amount }"
            else:
                users_total_items[user] += f"{ item }(${ item_price })*{ user_item_amount }"

        for user in order_details[ts][item].get('users', {}):
            user_item_amount = int(order_details[ts][item]["users"][user])
            users_total_amount.setdefault(user, 0)
            users_total_items.setdefault(user, "")
            users_total_amount[user] += (int(item_price) * int(user_item_amount))
            if users_total_items[user]:
                users_total_items[user] += f"、{ item }(${ item_price })*{ user_item_amount }"
            else:
                users_total_items[user] += f"{ item }(${ item_price })*{ user_item_amount }"

    for user in users_total_items:
        users_total_aggegations += f"${ users_total_amount[user] } { user } ({ users_total_items[user] })\n"

    client.chat_postMessage(
        channel=channel,
        thread_ts=ts,
        text=f"統計:\n{ users_total_aggegations }"
    )

    # 修改 Message 狀態
    blocks = getOrderMessageBlocksWithItems(
        order_name=orders[ts]["order_name"],
        order_creator=orders[ts]["order_creator"],
        order_info=orders[ts]["order_info"],
        order_img=orders[ts]["order_img"],
        order_total_price=getOrderTotalPrice(ts),
        order_total_amount=getOrderTotalAmount(ts),
        order_state=ORDER_STATE[1],
        order_details=order_details[ts]
    )

    metadata = getMessageMetadata(
        order_name=orders[ts]["order_name"],
        order_creator=orders[ts]["order_creator"],
        order_info=orders[ts]["order_info"],
        order_img=orders[ts]["order_img"],
        order_state=ORDER_STATE[1],
        order_details=order_details[ts]
    )

    client.chat_update(
        channel=channel,
        ts=ts,
        text="ended",
        metadata=metadata,
        blocks=blocks
    )

    # 移除全域變數
    orders.pop(ts, {})
    order_details.pop(ts, {})
    try:
        client.pins_remove(channel=channel, timestamp=ts)
    except Exception:
        pass


# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
