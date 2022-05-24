import vk_api
import random
import time
from utils.vk_bloggers_trello import VkTrelloClient
from utils.providers import login_pass
from utils.timeout import withTimeout
from utils.talker import VkTalker

client = VkTrelloClient()


@withTimeout(150)
def get_direct_threads(count, vk):
    threads = vk.messages.getConversations(count=count, extended=1, v=5.131)
    ids = []
    users = threads['profiles']
    groups = threads['groups']
    for item in users:
        ids.append('https://vk.com/id' + str(item['id']))
    for item in groups:
        ids.append('https://vk.com/public' + str(item['id']))
    return ids


@withTimeout(150)
def get_user_info(card, vk):
    user_id = card.name
    user_info = {}
    if 'https://vk.com/public' in user_id:
        user_id = user_id.replace('https://vk.com/public', '')
        info = vk.groups.getById(group_ids=user_id, fields='members_count', v=5.131)
        # user_info[str(info[0]['name'])] = info[0]['members_count']
        # user_info['name'] = str(info[0]['name'])
        user_info['name'] = 'Public'
        user_info['followers_count'] = str(info[0]['members_count'])
    else:
        user_id = user_id.replace('https://vk.com/id', '')
        info = vk.users.get(user_ids=user_id, fields='followers_count', v=5.131)
        # user_info[str(info[0]['first_name'] + ' ' + info[0]['last_name'])] = info[0]['followers_count']
        user_info['name'] = str(info[0]['first_name'] + ' ' + info[0]['last_name'])
        user_info['followers_count'] = info[0]['followers_count']
    return user_info


@withTimeout(150)
def user_id_from_username(card_name):
    name = card_name
    if 'https://vk.com/public' in card_name:
        user_id = name.replace('https://vk.com/public', '-')
    else:
        user_id = name.replace('https://vk.com/id', '')
    return user_id


def main(token):
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()

    while True:
        try:
            print(f"Starting job with account {login_pass(vk_account_card)[0]}")
            bloggers_to_write_cards = client.leadsList.list_cards()
            random.shuffle(bloggers_to_write_cards)
            direct_threads = get_direct_threads(200, vk)
            print(f"received {len(direct_threads)} threads")
            for card in bloggers_to_write_cards[0:random.randint(1, 20)]:
                if card.name in direct_threads:
                    print(f"thread with {card.name} already exists. Moving to contacted list")
                    card.change_list(client.contacted_list_id)
                    break
                else:
                    try:
                        user_info = get_user_info(card, vk)
                        messenger = VkTalker(user_info)
                        message = messenger.next_message()
                        print(f'sending to {card.name}\n{message}')
                        user_id = user_id_from_username(card.name)
                        vk.messages.send(peer_id=user_id, message=message, random_id=0, v=5.131)
                        card.change_list(client.contacted_list_id)
                    except Exception as exp:
                        print('Exception occurred: ' + repr(exp))
                        continue
        finally:
            timeout = random.randrange(4200, 9400)
            print(f'Job for {login_pass(vk_account_card)[0]} finished. Waiting {timeout} sec before starting a new job')
            time.sleep(timeout)


if __name__ == "__main__":
    vk_account_card = random.choice(client.restingAccountsList.list.cards())
    access_token = vk_account_card.description
    main(access_token)
