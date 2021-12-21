import pandas as pd
import requests
import datetime
import os
from os.path import join, dirname
from dotenv import load_dotenv
from math import floor

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

twitch_client_id=os.environ.get("twitch_client_id")
twitch_client_secret = os.environ.get("twitch_client_secret")

def validate_twitch():

    twitch_token_url = "https://id.twitch.tv/oauth2/token"
    twitch_token_data= {
        "grant_type":"client_credentials",
        "client_id": f"{twitch_client_id}",
        "client_secret":f"{twitch_client_secret}",
        "scope":"analytics:read:games"
        }

    twitch_r = requests.post(twitch_token_url,data=twitch_token_data)
    return twitch_r, twitch_client_id

twitch_validation, twitchid = validate_twitch()

def twitch_access_token(twitch_r):
    ## Twitch Status Code
    twitch_status_code = twitch_r.status_code in range(200,299)

    if twitch_status_code:
        twitch_response_data = twitch_r.json()
        ## How much time before it expires?
        twitch_expires_in = twitch_r.json()["expires_in"]
        twitch_now = datetime.datetime.now()
        twitch_expires = twitch_now + datetime.timedelta(seconds=twitch_expires_in)
        twitch_did_expire = twitch_expires < twitch_now

        ## TWITCH ACCESS TOKEN
        twitch_access_token = twitch_response_data["access_token"]

    return twitch_access_token

twitch_access = twitch_access_token(twitch_r = twitch_validation)

def top_hundred(twitch_access_token=twitch_access):
    base_url = "https://api.twitch.tv/helix/games/top"
    base_params = {"first":"100"}

    headers = {
        "Authorization":f"Bearer {twitch_access_token}",
        "Client-Id":f"{twitch_client_id}"
    }

    twitch_request = requests.get(base_url, params=base_params,headers=headers).json()

    top_games = pd.DataFrame([
    {
      "id":i["id"],
      "name":i["name"],
      "art":i["box_art_url"].replace("{width}","50").replace("{height}","50")
    } for i in twitch_request["data"]])


    return top_games.transpose()

#top_hundred = top_hundred()

def top_streamers(lang,twitch_access_token=twitch_access):
    base_url = "https://api.twitch.tv/helix/streams"
    base_params = {"language":f"{lang}", "first":"100"}

    headers = {
        "Authorization":f"Bearer {twitch_access_token}",
        "Client-Id":f"{twitch_client_id}"
    }

    twitch_request = requests.get(base_url,params=base_params, headers=headers).json()["data"]
    
    vids_data = {
    "total_views":pd.DataFrame(twitch_request)["viewer_count"].sum(),
    "top_category":pd.DataFrame(twitch_request)[["game_name"]].groupby("game_name").size().reset_index().sort_values(by=0, ascending=False).reset_index().iloc[0:1,:].transpose().to_dict()[0],
    "top_game":pd.DataFrame(twitch_request)[["game_name","viewer_count"]].groupby("game_name").sum().sort_values(by="viewer_count", ascending=False).reset_index().head(1).transpose().to_dict()[0],
    "median":floor(pd.DataFrame(twitch_request)["viewer_count"].median())
    }

    top_streamer = pd.DataFrame(twitch_request).sort_values(by="viewer_count", ascending=False).iloc[0:1,:].transpose().to_dict()[0]["user_id"]

    return twitch_request, vids_data, top_streamer

# a = top_streamers(lang="es",twitch_access_token=twitch_access)

def getTwitchUserId(channelURL,twitch_access_token=twitch_access):

    base_url = "https://api.twitch.tv/helix/search/channels"
    base_params = {"query":channelURL}
    headers = {
        "Authorization":f"Bearer {twitch_access_token}",
        "Client-Id":f"{twitch_client_id}"
    }

    twitch_request = requests.get(base_url,params=base_params, headers=headers).json()

    twitchUserId = pd.DataFrame([i for i in twitch_request["data"]])["id"][0]
    return twitchUserId

#userID = getTwitchUserId(channelURL="WilburSoot")

def getallchanneldata(userId, twitch_access_token=twitch_access):
    base_url = "https://api.twitch.tv/helix/users"
    base_params = {"id":userId}
    headers = {
        "Authorization":f"Bearer {twitch_access_token}",
        "Client-Id":f"{twitch_client_id}"
    }

    twitch_request = requests.get(base_url,params=base_params, headers=headers).json()

    # tw2 = pd.DataFrame([i for i in twitch_request["data"]])
    return twitch_request

#channeldata = getallchanneldata(userId =userID)

def user_videos(userId,twitch_access_token=twitch_access):
    base_url = "https://api.twitch.tv/helix/videos"
    base_params = {"user_id":userId, "first":"100"}
    twitch_request_headers = {
        "Authorization":f"Bearer {twitch_access_token}",
        "Client-Id":f"{twitch_client_id}"
    }
 
    twitch_request = requests.get(base_url, params=base_params, headers=twitch_request_headers).json()
    tw3 = pd.DataFrame([i for i in twitch_request["data"]]).sort_values(by="view_count", ascending=False)
    return tw3.transpose().to_dict(), twitch_request

#userVideos = user_videos(userId=userID)

def get_all_user_videos(channelURL):
    twitchUserId = getTwitchUserId(channelURL)
    channelData = getallchanneldata(userId=twitchUserId)
    uv, tw3 = user_videos(userId=twitchUserId)
    
    return uv

#alluservideos = get_all_user_videos(channelURL="WilburSoot")

def top_streams(lang, pagination="", twitch_access_token=twitch_access):
    base_url = "https://api.twitch.tv/helix/streams"
    base_params = {
        "language":lang, 
        "first":"100",
        "after":f"{pagination}"}
    
    twitch_request_headers = {
        "Authorization":f"Bearer {twitch_access_token}",
        "Client-Id":f"{twitch_client_id}"
    }
    
    twitch_request = requests.get(base_url,params=base_params, headers=twitch_request_headers).json()
    print(twitch_request)
    pagination = twitch_request.get("pagination")["cursor"]
    tw = pd.DataFrame([i for i in twitch_request["data"]])
    users_trending = tw["user_id"].tolist()

    return tw, users_trending, pagination


def topStreamsII(loops,language):
    hlist = [""]
    otherlist=[]
    for i in range(loops):
        h,i,j = top_streams(lang=language,pagination=hlist[i])
        otherlist.append(h)
        hlist.append(j)

    topstreams = pd.concat(otherlist).fillna(0).transpose().to_dict()
    return topstreams

#topstramsII = topStreamsII(loops=2,language="en")


if __name__ == "__main__":
    print("OK")
    # print(uv)
#print(user_videos)
