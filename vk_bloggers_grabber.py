import vk_api
import random
import time
from utils.providers import login_pass
from utils.vk_bloggers_trello import VkTrelloClient
from utils.timeout import withTimeout
from bloggers_grabber import hashtags, forbidden_words


client = VkTrelloClient()


@withTimeout(160)
def get_followers(userid, vksession):
    user = str(userid)
    # The group id is returned with a minus sign at the beginning
    # Removing the minus sign in front of the id
    if user[0] == '-':
        try:
            groupid = user.replace('-', '')
            followers = vksession.groups.getMembers(group_id=groupid, v=5.131)
            followers_count = followers['count']
            return followers_count
        except:
            print("Followers are hidden")
            followers_count = 0
            return followers_count
    else:
        try:
            user = vksession.users.get(user_ids=user, fields='followers_count', v=5.131)
            '''
            
            Getting:
            {"response": [{"id": ID, "first_name": "NAME", "last_name": "SURNAME", "followers_count": 3940}]}
            Then we turn to the followers_count
             
            '''
            followers_count = user[0]['followers_count']
            return followers_count
        except:
            print("User hide followers")
            followers_count = 0
            return followers_count


@withTimeout(160)
def merge_same_users(posts, all_bloggers):
    users_posts = dict()
    users_ids = dict()
    for post in posts['items']:
        username = str(post['owner_id'])
        if username[0] == '-':
            userid = username.replace('-', '')
            username = (f'https://vk.com/public{userid}')
        else:
            username = (f'https://vk.com/id{username}')
        if username in all_bloggers:
            print(f'username {username} is already on the board. Skipping.')
        else:
            users_posts[username] = post
            users_ids[username] = str(post['owner_id'])
    return users_posts, users_ids


@withTimeout(160)
def get_likes(post):
    likes = post['likes']
    likes_count = likes['count']
    return likes_count


@withTimeout(160)
def get_views(post):
    try:
        views = post['views']
        views_count = views['count']
        return views_count
    except:
        print('Views are unavailable')
        views_count = 0
        return views_count


def main(access_token):
    # Authorization via login and password, not recommended
    # current_vk_account = login_pass(vk_account_card)
    # vk_session = vk_api.VkApi(*current_vk_account)
    # vk_session.auth()
    # vk = vk_session.get_api()

    # Authorization via token
    vk_session = vk_api.VkApi(token=access_token)
    vk = vk_session.get_api()

    for hashtag in hashtags:
        print(f"Getting recent posts with hashtag {hashtag}")
        posts = vk.newsfeed.search(q=f'#{hashtag}', count=200, extended=1, v=5.131)
        users_posts, users_ids = merge_same_users(posts, client.all_trello_card_names)
        print(f'There are {len(users_posts)} users to check if they are appropriate or not')

        for user in users_posts:
            username = user
            post = users_posts[user]
            text = post['text']

            if any((word := bad_word) in text.lower() for bad_word in forbidden_words):
                # Saving a blogger as not appropriate to avoid checking it in future
                print(f'Adding user in not appropriate bloggers list because user media caption text contains {word}')
                client.notAppropriateBloggersList.add_card(f'{username}')
                continue

            userid = users_ids[username]
            followers_count = get_followers(userid, vk)
            media_count = vk.wall.get(owner_id=userid, v=5.131)['count']
            likes_count = get_likes(post)
            views_count = get_views(post)
            print(f'followers_count = {followers_count}\nmedia_count = {media_count}\nlikes_count = {likes_count}\nviews_count = {views_count}\n')

            if followers_count > 500 and media_count > 100 and likes_count > 50 and views_count > 1000:
                print(f'Adding {username} to appropriate bloggers')
                client.leadsList.add_card(f'{username}')

    print(f'end with hashtag {hashtag}')


if __name__ == "__main__":
    while True:
        try:
            random.shuffle(hashtags)
            vk_account_card = random.choice(client.restingAccountsList.list_cards())
            access_token = vk_account_card.description
            print(f"Starting job with account {login_pass(vk_account_card)[0]}")
            main(access_token)
            timeout = random.randrange(2400, 4800)
            print(f"Finished job with account {login_pass(vk_account_card)[0]}. Waiting {timeout} sec.")
            time.sleep(timeout)
        except Exception as e:
            print('Exception occurred: ' + repr(e))
            break

