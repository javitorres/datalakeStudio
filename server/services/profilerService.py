import numpy as np
import pandas as pd
from ydata_profiling import ProfileReport

def getProfile(df):
    try:
        profile = ProfileReport(df, title="Profiling Report")
        report = profile.to_notebook_iframe()
        return report
    except Exception as e:
        print("Error in generating profile report:" + str(e))
        return None