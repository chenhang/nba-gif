# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!
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
from PyQt4 import QtCore, QtGui
from PyQt4.QtCore import QAbstractTableModel, Qt, QVariant

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8

    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

VIDEO_QUALITIES = ['416x240_200.mp4', '640x360_600.mp4',
                   '768x432_1500.mp4', '960x540_2500.mp4',
                   '1280x720_3500.mp4']
GAME_CONFIGS = ['PlayByPlayV2']
INDEXES_IN_TABLE = [1, 4, 5, 6, 7, 9, 10, 11, 14, 18, 21, 25, 28, 31]
HEADERS = {
    'User-Agent':
    ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.75 Safari/537.36'
     ),
    'Dnt': ('1'),
    'Host': ('stats.nba.com'),
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
        data = nba_py.Scoreboard(month=month, day=day, year=year).json
        write_json(path, data)
        return data
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
        game_path = 'games'
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


def get_game(game_id='0021700092', game_code='20171030/SASBOS'):
    game_path = 'games'
    if not os.path.exists(game_path):
        os.makedirs(game_path)
    for method in GAME_CONFIGS:
        try:
            file_path = os.path.join(game_path, '-'.join(
                game_code.split('/')) + '.json')
            if os.path.exists(file_path):
                return load_json(file_path)
            print file_path
            data = getattr(game, method)(game_id=game_id).json
            write_json(file_path, data)
            return data
        except Exception as e:
            print e


def get_videos(game_date='20171029', game='SASIND', video_quality=VIDEO_QUALITIES[0], dialog=None):
    year = str(game_date)[0:4]
    data_path = os.path.join(
        'games', '-'.join([game_date, game]) + '.json')
    data = load_json(data_path)
    pbps = data['resultSets'][0]
    headers = data['resultSets'][0]['headers']
    total = len(pbps['rowSet'])
    for current, row in enumerate(pbps['rowSet']):
        event = {}
        for i, value in enumerate(row):
            event[headers[i]] = value
        if event['HOMEDESCRIPTION'] or event['VISITORDESCRIPTION']:
            video_data_url = 'http://stats.nba.com/stats/videoevents'

            res = get(url=video_data_url, timeout=100, headers=HEADERS, params={
                'GameEventID': event['EVENTNUM'], 'GameID': event['GAME_ID']})
            print res, res.url
            video_info = res.json()['resultSets']
            uuid = video_info['Meta']['videoUrls'][0]['uuid']
            name = video_info['playlist'][0]['dsc']
            game_path = os.path.join('downloads',
                                     game_date, '-'.join([game, event['GAME_ID']]))
            gif_path = os.path.join(game_path, 'gif')
            video_path = os.path.join(game_path, 'video')
            if not os.path.exists(game_path):
                os.makedirs(game_path)
            if not os.path.exists(gif_path):
                os.makedirs(gif_path)
            if not os.path.exists(video_path):
                os.makedirs(video_path)

            date_str = '/'.join(video_info['playlist']
                                [0]['gc'].split('/')[0].split('-'))
            video_xml = xmltodict.parse(get(
                url='http://www.nba.com/video/wsc/league/' + uuid + '.xml').content)
            video_url = next(v['#text'] for v in video_xml['video']
                             ['files']['file'] if video_quality in v['#text'])
            clip = VideoFileClip(video_url, audio=False,
                                 resize_algorithm='lanczos').resize(0.7)
            # clip.write_videofile(os.path.join(video_path, '.'.join(
            #     [str(event['EVENTNUM']), name, 'mp4'])))
            clip.write_gif(os.path.join(gif_path, '.'.join(
                [str(event['EVENTNUM']), name, 'gif'])), program='ffmpeg')
            print video_url
            progress = str(current) + '/' + str(total)
            print str(current) + '/' + str(total)
            time.sleep(2)
            if dialog:
                dialog.setText(str(current) + '/' + str(total))
                # dialog.setValue(current)


class Ui_NbaGifMainWindow(object):
    def setupUi(self, NbaGifMainWindow):
        NbaGifMainWindow.setObjectName(_fromUtf8("NbaGifMainWindow"))
        screen = QtGui.QDesktopWidget().screenGeometry()
        NbaGifMainWindow.resize(screen.width(), screen.height())
        NbaGifMainWindow.showMaximized()
        self.window = NbaGifMainWindow
        self.centralwidget = QtGui.QWidget(NbaGifMainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(
            QtCore.QRect(0, 60, screen.width(), screen.height() - 60))
        self.horizontalLayoutWidget.setObjectName(
            _fromUtf8("horizontalLayoutWidget"))
        self.pbpHorizontalLayout = QtGui.QHBoxLayout(
            self.horizontalLayoutWidget)
        self.pbpHorizontalLayout.setObjectName(
            _fromUtf8("pbpHorizontalLayout"))
        self.PbpTableView = QtGui.QTableView(self.horizontalLayoutWidget)
        self.PbpTableView.setObjectName(_fromUtf8("PbpTableView"))
        self.pbpHorizontalLayout.addWidget(self.PbpTableView)
        self.horizontalLayoutWidget_2 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_2.setGeometry(
            QtCore.QRect(0, 0, screen.width(), 61))
        self.horizontalLayoutWidget_2.setObjectName(
            _fromUtf8("horizontalLayoutWidget_2"))
        self.optionLayout = QtGui.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.optionLayout.setObjectName(_fromUtf8("optionLayout"))
        self.dateEdit = QtGui.QDateEdit(self.horizontalLayoutWidget_2)
        sizePolicy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.dateEdit.sizePolicy().hasHeightForWidth())
        self.dateEdit.setSizePolicy(sizePolicy)
        self.dateEdit.setObjectName(_fromUtf8("dateEdit"))
        self.optionLayout.addWidget(self.dateEdit)
        self.gameBox = QtGui.QComboBox(self.horizontalLayoutWidget_2)
        sizePolicy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.gameBox.sizePolicy().hasHeightForWidth())
        self.gameBox.setSizePolicy(sizePolicy)
        self.gameBox.setObjectName(_fromUtf8("gameBox"))
        self.optionLayout.addWidget(self.gameBox)
        self.qualityBox = QtGui.QComboBox(self.horizontalLayoutWidget_2)
        sizePolicy = QtGui.QSizePolicy(
            QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.qualityBox.sizePolicy().hasHeightForWidth())
        self.qualityBox.setSizePolicy(sizePolicy)
        self.qualityBox.setObjectName(_fromUtf8("qualityBox"))
        self.optionLayout.addWidget(self.qualityBox)
        self.downloadButton = QtGui.QPushButton(self.horizontalLayoutWidget_2)
        self.downloadButton.setObjectName(_fromUtf8("downloadButton"))
        self.optionLayout.addWidget(self.downloadButton)
        NbaGifMainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtGui.QStatusBar(NbaGifMainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        NbaGifMainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(NbaGifMainWindow)
        self.initContent()
        QtCore.QMetaObject.connectSlotsByName(NbaGifMainWindow)

    def retranslateUi(self, NbaGifMainWindow):
        NbaGifMainWindow.setWindowTitle(_translate(
            "NbaGifMainWindow", "MainWindow", None))
        self.downloadButton.setText(_translate(
            "NbaGifMainWindow", "Download", None))

    def initContent(self):
        self.dateEdit.dateChanged.connect(self.onDateChanged)
        self.dateEdit.setDate(QtCore.QDate(2017, 10, 29))
        self.dateEdit.setCalendarPopup(True)
        self.qualityBox.clear()
        self.qualityBox.addItems(VIDEO_QUALITIES)
        self.qualityBox.currentIndexChanged.connect(self.onQualityChanged)
        self.quality = VIDEO_QUALITIES[0]
        self.gameBox.currentIndexChanged.connect(self.onGameChanged)
        self.downloadButton.clicked.connect(self.download)

    def onQualityChanged(self, index):
        self.quality = VIDEO_QUALITIES[index]

    def onGameChanged(self, index):
        self.drawGame(self.games[index])

    def onDateChanged(self, new_date):
        year, month, day = new_date.getDate()
        self.drawScoreboard(year=year, month=month, day=day)

    def drawScoreboard(self, year=2017, month=10, day=29):
        self.scoreboard = {d[5]: d[2] for d in get_scoreboard(
            year=year, month=month, day=day)['resultSets'][0]['rowSet']}
        self.games = self.scoreboard.keys()
        self.gameBox.clear()
        self.gameBox.addItems(self.games)
        if len(self.games):
            self.drawGame(self.games[0])

    def drawGame(self, game_code):
        game_date, game_name = game_code.split('/')
        self.game = get_game(game_code=game_code,
                             game_id=self.scoreboard[game_code])['resultSets'][0]

        self.PbpTableView.clearSpans()
        self.PbpTableView.setModel(PbpTableModel(self.game))

        self.PbpTableView.resizeColumnsToContents()
        self.PbpTableView.resizeRowsToContents()

    def download(self, page):
        dialog = QtGui.QMessageBox()
        # dialog = QtGui.QProgressDialog()
        # dialog.setMaximum(len(self.game['rowSet']))
        dialog.show()
        self.game['rowSet']
        get_videos(game_date='20171029', game='SASIND',
                   video_quality=self.quality, dialog=dialog)
        #    video_quality=self.quality, dialog=None)


class PbpTableModel(QAbstractTableModel):
    def __init__(self, game, parent=None):
        QAbstractTableModel.__init__(self, parent)

        game['rowSet'] = [[d[i] for i in INDEXES_IN_TABLE]
                          for d in game['rowSet']]
        game['headers'] = [game['headers'][i] for i in INDEXES_IN_TABLE]
        self.game = game

    def rowCount(self, parent):
        return len(self.game['rowSet'])

    def columnCount(self, parent):
        return len(self.game['headers'])

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role != Qt.DisplayRole:
            return QVariant()
        return QVariant(self.game['rowSet'][index.row()][index.column()])

    def setData(self, index, value, role):
        pass

    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.game['headers'][col])
        return QVariant()

    def sort(self, Ncol, order):
        """
        Sort table by given column number.
        """
        pass
