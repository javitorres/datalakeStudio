from dataprofiler import Data, Profiler

def getProfile(df):
    try:
        profile = Profiler(df)
        readable_report = profile.report(report_options={"output_format": "compact"})
        return readable_report
    except:
        return None