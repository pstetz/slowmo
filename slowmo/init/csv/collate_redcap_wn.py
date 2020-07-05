"""
Imports
"""
import numpy as np
import pandas as pd

redcap_cols = {
        "ehi_handedness": "handedness", # hand preference for spoon would be interesting too!
        "demo_education": "education",
        "demo_age": "age",
        "lang_nat": "native_language",
        "weight": "weight",
        "height": "height",
        "hamd_total": "hamd_total",
        "hama_score": "hama_score",
        "hourssleep": "hourssleep",
        "feeltoday": "feeltoday",
        "whoqol7": "whoqol7", # ability to concentrate
        "whoqol1": "whoqol1", # satisfied with life
        "whoqol16": "whoqol16", # satisfied with sleep
        "phq_score": "phq_score", # would like to see how it compares with hamd hama
        "masq_score2": "masq_score2",
        "masq_score3": "masq_score3",
        "participant_id": "subject",
        "webneuroc_id": "login",
        #"demo_edu_years", # this needs to be cleaned # I don't want to do that
#        "rrq_12", # not in HCP-DES
}
wn_cols = [
        "emzcompk", "emzoverk", "g2fnk", # Act correlations
        "getcpA", "tdomnk", # RS correlations
        "ecoackII", # PPI
        "esoadur2", # biotypes
]

def ohe(df, variables):
    for var in variables:
        values = df[var].unique()
        for val in values:
            if np.isnan(val): continue
            df["%s_%s" % (var, str(val).replace(".", "_"))] = (df[var] == val).astype(int)
        df.drop(var, axis=1, inplace=True)

def combine_redcap(hc, des):
    hc = hc[hc["webneuroc_id"].notnull()]
    des = des[des["webneuroc_id"].notnull()]
    hc["participant_id"] = hc["participant_id"].map(lambda x: "CONN%03d" % int(x))
    des["participant_id"] = des["participant_id"].map(lambda x: "CONN%s" % x[:3])
    des["is_des"] = 1
    des["is_des"] = 0
    redcap = pd.concat([hc, des]).reset_index(drop=True)
    return redcap

def setup_redcap(hc, des):
    redcap = combine_redcap(hc, des)
    redcap["is_female"] = (redcap["demo_gender"] == 1).astype(int)
    redcap["is_male"]   = (redcap["demo_gender"] == 2).astype(int)
    redcap.drop("demo_gender", axis=1, inplace=True)
    redcap["hourssleep"] = redcap["hourssleep"].map(lambda x: x if x != 99 else 12)
    redcap.rename(columns=redcap_cols, inplace=True)
    redcap = redcap[list(redcap_cols.values()) + ["is_female", "is_male", "is_des"]]
    ohe(redcap, ["native_language"])
    return redcap

def main(wn, hc, des, dst):
    redcap = setup_redcap(hc, des)
    wn = wn[wn_cols + ["login"]]
    df = pd.merge(wn, redcap, on="login", how="inner")
    df.drop(["subject", "login"], axis=1, inplace=True)
    df.to_csv(dst, index=False)

if __name__ == "__main__":
    wn_path = "/Volumes/hd_4tb/slowmo/data/PHI/cognition/DISC100313_WebNeuro_Data_2020-05-12_08-34-00.xls"
    hc_redcap_path  = "/Volumes/hd_4tb/slowmo/data/PHI/redcap/ConnectomeProjectHea_DATA_2020-06-12_1336.csv"
    des_redcap_path = "/Volumes/hd_4tb/slowmo/data/PHI/redcap/ConnectomeProject_DATA_2020-06-12_1336.csv"
    dst = "/Users/pstetz/Desktop/subjects.csv"

    wn = pd.read_excel(wn_path).replace(".", np.nan)
    hc  = pd.read_csv(hc_redcap_path, low_memory=False)
    des = pd.read_csv(des_redcap_path, low_memory=False)

    main(wn, hc, des, dst)

