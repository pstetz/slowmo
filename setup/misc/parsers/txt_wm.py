"""
Used to be RAD_WorkingMemory_Grab_091216.py
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


def makeOns_WorkingMemory(df, outDir):
    #Creates onset times and durations for Go vs NoGo for Go No Go Task

    Baseline = [18, 31, 33, 35, 37, 40, 42, 47, 52, 55, 57, 58, 60, 65, 67, 68, 69, 71, 77, 78, 80, 82, 84, 87, 88, 89, 90, 94, 95, 97, 99, 102, 111, 112, 114, 118, 122, 125, 128, 129]
    NonTarget = [13, 14, 16, 17, 19, 20, 21, 23, 25, 26, 27, 28, 29, 32, 34, 38, 39, 45, 48, 50, 53, 54, 56, 59, 62, 63, 66, 70, 72, 74, 76, 79, 81, 83, 91, 92, 96, 98, 100, 101, 105, 107, 108, 109, 113, 116, 117, 121, 126, 132]
    Target = [15, 22, 24, 30, 36, 41, 43, 44, 46, 49, 51, 61, 64, 73, 75, 85, 86, 93, 103, 104, 106, 110, 115, 119, 120, 123, 124, 127, 130, 131]


    Baseline_Df  = df[(df['num'].isin(Baseline)) &  (df['type']=='Paradigm Event')]
    NonTarget_Df = df[(df['num'].isin(NonTarget)) &  (df['type']=='Paradigm Event')]
    Target_Df = df[(df['num'].isin(Target)) &  (df['type']=='Paradigm Event')]


    Baseline_Df.to_csv('%s/Baseline_Onsets.csv' % outDir, index=False)
    NonTarget_Df.to_csv('%s/NonTarget_Onsets.csv' % outDir, index=False)
    Target_Df.to_csv('%s/Target_Onsets.csv' % outDir, index=False)


    print('saving Working Memory Onsets to %s/' %outDir)

#---------------------flow of control starts here-------------------------------#
if __name__ == "__main__":
    fileName = sys.argv[1]
    outDir = os.path.dirname(fileName)
    df = grabEvents(fileName,  13, 2.75)
    makeOns_WorkingMemory(df, outDir)
    makeOns_Motor(df, outDir)
