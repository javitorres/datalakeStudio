import boto3
import json
import time

index = None
indexBuildingTime = 0

def buildIndex(bucket_name):
    print ("Building index...")
    global index
    s3 = boto3.client("s3")
    indice = []

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            indice.append("s3://" + bucket_name + "/" + obj["Key"])

    return indice

def s3Search(bucket, fileName):
    global index
    global indexBuildingTime
    if (index == None) or time.time() - indexBuildingTime > 300:
        index = buildIndex(bucket)
        indexBuildingTime = time.time()

    results = []

    for file in index:
        if fileName in file:
            results.append(file)

    return results

# Example:
#bucket = "madiva-datalake"
#fileName = "cargadores"
#results = s3Search(bucket, fileName)
#print("Results:", results)
