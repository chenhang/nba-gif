import nba_py
from nba_py import team, game, constants, player
import json
import os
from requests import get
from datetime import date, timedelta
from moviepy.editor import *
import xmltodict
import time
import sys
from xml.etree import ElementTree
VIDEO_QUALITIES = ['416x240_200.mp4', '640x360_600.mp4',
                   '768x432_1500.mp4', '960x540_2500.mp4',
                   '1280x720_3500.mp4']
GAME_CONFIGS = ['PlayByPlayV2']
HEADERS = {
    'user-agent':
    ('Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'
     ),
    'Dnt': ('1'),
    'Accept-Encoding': ('gzip, deflate, sdch'),
    'Accept-Language': ('en'),
    'origin': ('http://stats.nba.com')
}


def load_json(file_name):
    with open(file_name) as json_data:
        d = json.load(json_data)
        return d


def write_json(file_name, json_data):
    print 'writting:' + file_name
    with open(file_name, 'w') as outfile:
        json.dump(json_data, outfile)
        return json_data
    print 'writting done:' + file_name


def get_scoreboard(year=2017, month=10, day=29):
    single_date = date(year, month, day)
    day, month, year = (single_date.timetuple().tm_mday,
                        single_date.timetuple().tm_mon,
                        single_date.timetuple().tm_year)
    key = '-'.join([str(year), str(month), str(day)])
    if not os.path.exists('scoreboards'):
        os.makedirs('scoreboards')
    path = 'scoreboards/' + key + '.json'
    try:
        print((day, month, year))
        write_json(path,
                   nba_py.Scoreboard(month=month, day=day, year=year).json)
    except Exception as e:
        print e


def get_games(year=2017, month=10, day=29):
    single_date = date(year, month, day)
    day, month, year = (single_date.timetuple().tm_mday,
                        single_date.timetuple().tm_mon,
                        single_date.timetuple().tm_year)
    key = '-'.join([str(year), str(month), str(day)])
    scoreboard_path = 'scoreboards/' + key + '.json'
    scoreboard = load_json(scoreboard_path)
    headers = scoreboard['resultSets'][0]['headers']
    for row in scoreboard['resultSets'][0]['rowSet']:
        game_id, season, home, away, vs = row[2], row[8], row[6], row[7], row[5]
        game_path = os.path.join('games', str(season))
        if not os.path.exists(game_path):
            os.makedirs(game_path)
        for method in GAME_CONFIGS:
            try:
                file_path = os.path.join(game_path, '-'.join(
                    vs.split('/')) + '.json')
                if os.path.exists(file_path):
                    continue
                print file_path
                write_json(
                    file_path, getattr(game, method)(game_id=game_id).json)
                time.sleep(2)
            except Exception as e:
                print e


def get_videos(game_date='20171029', game='SASIND'):
    year = str(game_date)[0:4]
    data_path = os.path.join(
        'games', year, '-'.join([game_date, game]) + '.json')
    data = load_json(data_path)
    pbps = data['resultSets'][0]
    headers = data['resultSets'][0]['headers']
    for row in pbps['rowSet']:
        event = {}
        for i, value in enumerate(row):
            event[headers[i]] = value
        if event['HOMEDESCRIPTION'] or event['VISITORDESCRIPTION']:
            video_data_url = 'http://stats.nba.com/stats/videoevents'
            video_info = get(url=video_data_url, headers=HEADERS, params={
                             'GameEventID': event['EVENTNUM'], 'GameID': event['GAME_ID']}).json()['resultSets']
            uuid = video_info['Meta']['videoUrls'][0]['uuid']
            date_str = '/'.join(video_info['playlist']
                                [0]['gc'].split('/')[0].split('-'))
            video_xml = xmltodict.parse(get(
                url='http://www.nba.com/video/wsc/league/' + uuid + '.xml').content)
            video_url = next(v['#text'] for v in video_xml['video']
                             ['files']['file'] if VIDEO_QUALITIES[2] in v['#text'])
            clip = (VideoFileClip(video_url)
                    .resize(0.5))
            clip.write_gif("test.gif")
            print video_url
            break
            time.sleep(2)


# get_scoreboard()
# get_games()
get_videos()