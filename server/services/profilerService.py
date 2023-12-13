#import numpy as np
#import pandas as pd
#from ydata_profiling import ProfileReport

#from pyspark.sql import SparkSession
#from ydata_profiling import ProfileReport

'''
def getProfile_ydata(df):
    try:
        profile = ProfileReport(df, title="Profiling Report")
        report = profile.to_notebook_iframe()
        return report
    except Exception as e:
        print("Error in generating profile report:" + str(e))
        return None
'''
            
def getProfile(df):
    # Print df simpleprofile as json:
    
    desc = df.describe().to_csv()

    print("Simple profile:" + str(desc))
    #report = ProfileReport(df, title="Profiling pyspark DataFrame")
    return desc