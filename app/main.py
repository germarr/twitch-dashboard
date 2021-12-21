from typing import Optional
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from twitch import top_streamers, getallchanneldata
from fastapi.middleware.cors import CORSMiddleware

description = """
The purpose of this app is to plot the performance of different Twitch Channels.
"""

app = FastAPI(
    title="GMARR Twitch webapp 👾",
    description=description,
    version="0.0.1"
)

origins=['*']

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.get("/")
def topTwitchStreamers(request:Request):
    """
    List of all the top Streamers on Twitch right now.
    """

    return templates.TemplateResponse("index.html",{
        "request":request,
    })

@app.get("/streamers/{language}")
def topTwitchStreamers(request:Request,language:str="es"):
    """
    List of all the top Streamers onn Twitch right now.
    """
    twitch_request, vids_data, top_streamer = top_streamers(lang=language)
    topstreamer = getallchanneldata(userId = top_streamer)
    
    print(topstreamer["data"][0])
    
    return templates.TemplateResponse("streamer.html",{
        "request":request,
        "twitch_videos":twitch_request,
        "vids":vids_data,
        "topStreamer":topstreamer["data"][0]
    })


