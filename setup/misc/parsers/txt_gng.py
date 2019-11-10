"""
Used to be RAD_GoNoGo_Grab_091216.py
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
    startInd = eventNumberTemp[(eventNumberTemp['num']==eventStart) &  (eventType=='Paradigm Event')].index.tolist()[0]
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


def makeOns_GovsNoGo(df, outDir):
    #Creates onset times and durations for Go vs NoGo for Go No Go Task

    NoGoEvents = [15, 16, 21, 22, 27, 28, 39, 40, 43, 44, 51, 52, 63, 64, 77, 78, 83, 84, 87, 88, 103, 104, 109, 110, 117, 118, 127, 128, 137, 138, 145, 146, 149, 150, 159, 160, 167, 168, 173, 174, 179, 180, 191, 192, 195, 196, 207, 208, 211, 212, 217, 218, 225, 226, 231, 232, 243, 244, 247, 248]
    GoEvents = [9, 10, 11, 12, 13, 14, 17, 18, 19, 20, 23, 24, 25, 26, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 41, 42, 45, 46, 47, 48, 49, 50, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 79, 80, 81, 82, 85, 86, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 105, 106, 107, 108, 111, 112, 113, 114, 115, 116, 119, 120, 121, 122, 123, 124, 125, 126, 129, 130, 131, 132, 133, 134, 135, 136, 139, 140, 141, 142, 143, 144, 147, 148, 151, 152, 153, 154, 155, 156, 157, 158, 161, 162, 163, 164, 165, 166, 169, 170, 171, 172, 175, 176, 177, 178, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 193, 194, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 209, 210, 213, 214, 215, 216, 219, 220, 221, 222, 223, 224, 227, 228, 229, 230, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 245, 246]

    NoGoEvents_Df  = df[(df['num'].isin(NoGoEvents)) &  (df['type']=='Paradigm Event')]
    GoEvents_Df = df[(df['num'].isin(GoEvents)) &  (df['type']=='Paradigm Event')]


    NoGoEvents_Df.to_csv('%s/NoGo_Onsets.csv' % outDir, index=False)
    GoEvents_Df.to_csv('%s/Go_Onsets.csv' % outDir, index=False)

    print('saving Go and NoGo onsets to %s/' %outDir)

#---------------------flow of control starts here-------------------------------#
if __name__ == "__main__":
    fileName = sys.argv[1]
    outDir = os.path.dirname(fileName)
    df = grabEvents(fileName,  9, 1.5)
    makeOns_GovsNoGo(df, outDir)
    makeOns_Motor(df, outDir)
