"""
Imports
"""
import numpy as np
import pandas as pd

"""
Config
"""
redcap_cols = [
        "ehi_handedness", # hand preference for spoon would be interesting too!
        "demo_education",
        "demo_age",
        "demo_gender", # code this as is_male and is_female
        "lang_nat",
        "weight",
        "height",
        "hamd_total",
        "hama_score",
        "hourssleep", # recode 99 values to be 12
        "feeltoday",
        "demo_edu_years", # this needs to be cleaned
        "whoqol7", # ability to concentrate
        "whoqol1", # satisfied with life
        "whoqol16", # satisfied with sleep
        "phq_score", # would like to see how it compares with hamd hama
        "masq_score2",
        "masq_score3",
        "rrq_12",
]
wn_cols = [
        "emzcompk", "emzoverk", "g2fnk", # Act correlations
        "getcpA", "tdomnk", # RS correlations
        "ecoackII", # PPI
        "esoadur2", # biotypes
]

def setup_wn():
    dfs = list()
    for redcap_path, fmri_path, renaming in [
            (hc_redcap_path, hc_fmri_path, rename_hc),
            (des_redcap_path, des_fmri_path, rename_des)
        ]:
        redcap = pd.read_csv(redcap_path, low_memory=False)
        redcap["participant_id"] = redcap["participant_id"].map(renaming)
        redcap = redcap[["participant_id", "webneuroc_id"]].dropna()
    #     redcap = redcap[redcap["participant_id"].notnull()]
        redcap.rename(columns={"participant_id": "subNum", "webneuroc_id": "wn"}, inplace=True)
        fmri = pd.read_csv(fmri_path)
        fmri = pd.merge(fmri, redcap, on="subNum", how="inner")
        dfs.append(fmri)
    fmri = pd.concat(dfs)

def main(hc_redcap_path, des_redcap_path, wn_path):
    wn = pd.read_excel(wn_path).replace(".", np.nan)
    wn.rename(columns={"login": "wn"}, inplace=True)
    df = pd.merge(fmri, wn, on="wn", how="inner")
    df = pd.merge(wn, redcap, on="subject", how="inner")
    df.to_csv(dst, index=False)

if __name__ == "__main__":
    hc_redcap_path  = "/Users/pbezuhov/Desktop/PHI/redcap/connhc.csv"
    des_redcap_path = "/Users/pbezuhov/Desktop/PHI/redcap/conndes.csv"
    wn_path         = "/Users/pbezuhov/Desktop/PHI/cognition/conn/DISC100313_WebNeuro_Data_2020-05-12_08-34-00.xls"
    main(hc_redcap_path, des_redcap_path, wn_path)

