"""
Used to be RAD_ConsciousEmotion_Grab_091216.py
"""

import pandas as pd
import numpy as np
import string
import sys
import os
import re
import datetime
import glob
import shutil
import math


def grabEvents(fileName, eventStart=1, lag=0):
    #open file and collect time stamp, event type and event number from iSPOT generated txt file
    #return dataframe of relevent events
    #eventStart          option to set the event start based off of a specific paradigm number
    #                    For emotional conflict this number should be 12
    #lag                 amount of time in seconds from the end of dummy scans to first event (for emo conflict should be 3.5)

    test = open(fileName, "r")
    test2 = test.readlines()

    dateAndTime  = re.findall('(\d*/\d*/\d* \d*\:\d*\:\d*\.\d*)',  str(test2))
    eventType = np.array(re.findall('\d*/\d*/\d* \d*\:\d*\:\d*\.\d*\\\\t(.*?) : \d*\\\\r\\\\n', str(test2)))
    eventNumber = re.findall('\d*/\d*/\d* \d*\:\d*\:\d*\.\d*\\\\t.*? : (\d*)\\\\r\\\\n', str(test2))

    eventNumberTemp = pd.DataFrame({'num':eventNumber}).astype(int)
    #eventNumberDate = pd.DataFrame({'time':dateAndTime})

    #See PANLab fMRI google doc to see how this was derived; Event 12 is the wait screen for the emo conflict task
    startInd = eventNumberTemp[(eventNumberTemp['num']==eventStart)  & (eventType=='Paradigm Event')].index.tolist()[0]
    #startInd = eventNumberDate[eventNumberDate['time']=='2014/6/6 8:19:35.506'].index.tolist()[0]
    df = pd.DataFrame({'time':dateAndTime[startInd:], 'type':eventType[startInd:], 'num':eventNumber[startInd:]}, )

    #fix column dtypes
    df['num'] = df['num'].astype(int)
    df['time'] = pd.to_datetime(df['time'])

    #Creates onsets relative to the first event with added lag time if needed
    startTime = df['time'] - df['time'][0] + datetime.timedelta(0, lag)
    df['ons'] = startTime.apply(lambda x: x / np.timedelta64(1, 's'))
    return df


def makeOns_Motor(df, outDir):
    Left = df[(df['type']=='Button Press Event') & (df['num']==1)][['num',  'ons']]
    Right = df[(df['type']=='Button Press Event') & (df['num']==6)][['num',  'ons']]

    Left.to_csv('%s/Left.csv' % outDir, index=False)
    Right.to_csv('%s/Right.csv' % outDir, index=False)

    print('saving Left and Right onsets to %s/' %outDir)


def makeOns_Emotions(df, outDir):
    #Creates onset times and durations for Go vs NoGo for Go No Go Task

    Neutral = [17, 49, 121, 137, 153]
    Happy = [9, 65, 81, 161, 217]
    Fear = [25, 97, 113, 169, 185]
    Anger = [1, 33, 73, 193, 209]
    Sad = [89, 129, 177, 201, 225]
    Disgust = [41, 57, 105, 145, 233]


    Neutral_Df  = df[(df['num'].isin(Neutral)) &  (df['type']=='Paradigm Event')]
    Happy_Df = df[(df['num'].isin(Happy)) &  (df['type']=='Paradigm Event')]
    Fear_Df = df[(df['num'].isin(Fear)) &  (df['type']=='Paradigm Event')]
    Anger_Df = df[(df['num'].isin(Anger)) &  (df['type']=='Paradigm Event')]
    Sad_Df = df[(df['num'].isin(Sad)) &  (df['type']=='Paradigm Event')]
    Disgust_Df = df[(df['num'].isin(Disgust)) &  (df['type']=='Paradigm Event')]


    Neutral_Df.to_csv('%s/Neutral_Onsets.csv' % outDir, index=False)
    Happy_Df.to_csv('%s/Happy_Onsets.csv' % outDir, index=False)
    Fear_Df.to_csv('%s/Fear_Onsets.csv' % outDir, index=False)
    Anger_Df.to_csv('%s/Anger_Onsets.csv' % outDir, index=False)
    Sad_Df.to_csv('%s/Sad_Onsets.csv' % outDir, index=False)
    Disgust_Df.to_csv('%s/Disgust_Onsets.csv' % outDir, index=False)


    print('saving Emotion Onsets to %s/' %outDir)

#---------------------flow of control starts here-------------------------------#
if __name__ == "__main__":
    fileName = sys.argv[1]
    outDir = os.path.dirname(fileName)
    df = grabEvents(fileName,  1, 2)
    makeOns_Emotions(df, outDir)
    makeOns_Motor(df, outDir)
