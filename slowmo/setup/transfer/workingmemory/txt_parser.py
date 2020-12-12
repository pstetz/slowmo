import os
import re
import datetime
import numpy as np
import pandas as pd
from os.path import dirname, isdir, join

def grabEvents(filepath, eventStart=1, lag=0):
    file_handle = open(filepath, "r")
    lines = file_handle.readlines()

    dateAndTime  = re.findall('(\d*/\d*/\d* \d*\:\d*\:\d*\.\d*)',  str(lines))
    eventType = np.array(re.findall('\d*/\d*/\d* \d*\:\d*\:\d*\.\d*\\\\t(.*?) : \d*\\\\r\\\\n', str(lines)))
    eventNumber = re.findall('\d*/\d*/\d* \d*\:\d*\:\d*\.\d*\\\\t.*? : (\d*)\\\\r\\\\n', str(lines))

    eventNumberTemp = pd.DataFrame({'num':eventNumber}).astype(int)

    startInd = eventNumberTemp[(eventNumberTemp['num']==eventStart)  & (eventType=='Paradigm Event')].index.tolist()[0]
    df = pd.DataFrame({'time':dateAndTime[startInd:], 'type':eventType[startInd:], 'num':eventNumber[startInd:]}, )

    #fix column dtypes
    df['num'] = df['num'].astype(int)
    df['time'] = pd.to_datetime(df['time'])

    #Creates onsets relative to the first event with added lag time if needed
    startTime = df['time'] - df['time'][0] + datetime.timedelta(0, lag)
    df['ons'] = startTime.apply(lambda x: x / np.timedelta64(1, 's'))
    return df


def make_ons_motor(df):
    dfs = list()
    for cat, num in [("left", 1), ("right", 6)]:
        tmp_df = df[(df['type']=='Button Press Event') & (df['num']==num)][['num',  'ons']]
        if len(tmp_df) == 0: continue
        tmp_df["category"] = cat
        tmp_df["stimulus"] = "keypress"
        dfs.append(tmp_df)
    return dfs


def make_ons(df, cat_index):
    dfs = make_ons_motor(df)
    for cat, index in cat_index:
        tmp_df = df.copy()[(df['num'].isin(index)) &  (df['type']=='Paradigm Event')]
        tmp_df["category"] = cat
        dfs.append( tmp_df )
    return pd.concat(dfs, sort=False)


def make_ons_faces(df):
    neutral = [17, 49, 121, 137, 153]
    happy   = [9, 65, 81, 161, 217]
    fear    = [25, 97, 113, 169, 185]
    anger   = [1, 33, 73, 193, 209]
    sad     = [89, 129, 177, 201, 225]
    disgust = [41, 57, 105, 145, 233]

    cat_index = [
            ("Neutral", neutral),
            ("Happy", happy),
            ("Fear", fear),
            ("Anger", anger),
            ("Sad", sad),
            ("Disgust", disgust),
    ]
    return make_ons(df, cat_index)


def make_ons_wm(df):
    baseline = [18, 31, 33, 35, 37, 40, 42, 47, 52, 55, 57, 58, 60, 65, 67, 68, 69, 71, 77, 78, 80, 82, 84, 87, 88, 89, 90, 94, 95, 97, 99, 102, 111, 112, 114, 118, 122, 125, 128, 129]
    nontarget = [13, 14, 16, 17, 19, 20, 21, 23, 25, 26, 27, 28, 29, 32, 34, 38, 39, 45, 48, 50, 53, 54, 56, 59, 62, 63, 66, 70, 72, 74, 76, 79, 81, 83, 91, 92, 96, 98, 100, 101, 105, 107, 108, 109, 113, 116, 117, 121, 126, 132]
    target = [15, 22, 24, 30, 36, 41, 43, 44, 46, 49, 51, 61, 64, 73, 75, 85, 86, 93, 103, 104, 106, 110, 115, 119, 120, 123, 124, 127, 130, 131]

    cat_index = [
            ("Baseline", baseline),
            ("NonTarget", nontarget),
            ("Target", target)
    ]
    return make_ons(df, cat_index)


def make_ons_gonogo(df):
    nogo = [15, 16, 21, 22, 27, 28, 39, 40, 43, 44, 51, 52, 63, 64, 77, 78, 83, 84, 87, 88, 103, 104, 109, 110, 117, 118, 127, 128, 137, 138, 145, 146, 149, 150, 159, 160, 167, 168, 173, 174, 179, 180, 191, 192, 195, 196, 207, 208, 211, 212, 217, 218, 225, 226, 231, 232, 243, 244, 247, 248]
    go = [9, 10, 11, 12, 13, 14, 17, 18, 19, 20, 23, 24, 25, 26, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 41, 42, 45, 46, 47, 48, 49, 50, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 79, 80, 81, 82, 85, 86, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 105, 106, 107, 108, 111, 112, 113, 114, 115, 116, 119, 120, 121, 122, 123, 124, 125, 126, 129, 130, 131, 132, 133, 134, 135, 136, 139, 140, 141, 142, 143, 144, 147, 148, 151, 152, 153, 154, 155, 156, 157, 158, 161, 162, 163, 164, 165, 166, 169, 170, 171, 172, 175, 176, 177, 178, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 193, 194, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 209, 210, 213, 214, 215, 216, 219, 220, 221, 222, 223, 224, 227, 228, 229, 230, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 245, 246]

    cat_index = [
            ("Go", go),
            ("NoGo", nogo),
    ]
    return make_ons(df, cat_index)


def txt_parser(logpath, task, dst):
    if task == "workingmemSB":
        df = grabEvents(logpath,  13, 2.75)
        df = make_ons_wm(df)
    elif task in ["conscious", "nonconscious"]:
        df = grabEvents(logpath,  1, 2)
        df = make_ons_faces(df)
    elif task == "gonogo":
        df = grabEvents(logpath,  9, 1.5)
        df = make_ons_gonogo(df)
    else:
        raise Exception("Task %s not known for txt parser" % task)

    if not isdir(dirname(dst)):
        os.makedirs(dirname(dst))
    df.sort_values("ons", inplace=True)
    df.to_csv(dst, index=False)


if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    logpath = args[0]
    task    = args[1]
    dst = args[2]
    txt_parser(logpath, task, dst)

