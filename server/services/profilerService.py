           
def getProfile(df):
    # Print df simpleprofile as json:
    
    desc = df.describe().to_csv()

    print("Simple profile:" + str(desc))
    #report = ProfileReport(df, title="Profiling pyspark DataFrame")
    return desc