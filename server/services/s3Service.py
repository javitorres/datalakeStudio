import boto3
import json
import time

index = None
indexBuildingTime = 0
previousBucket = None

def buildIndex(bucket_name):
    print ("Building index...")
    global index
    s3 = boto3.client("s3")
    indice = []

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        #print("Page: " + str(page))
        for obj in page.get("Contents", []):
            fileName = "s3://" + bucket_name + "/" + obj["Key"]
            indice.append(fileName)
            #print("Added file: " + fileName)
    print("S3 Index built")
    return indice

############################################################################################################

def s3Search(bucket, fileName):
    global index
    global indexBuildingTime
    global previousBucket

    if (bucket!=previousBucket):
        index = None
        previousBucket = bucket
    
    if (index == None) or time.time() - indexBuildingTime > 600:
        index = buildIndex(bucket)
        indexBuildingTime = time.time()

    results = []

    for file in index:
        if fileName in file:
            results.append(file)

    return results

############################################################################################################
def getContent(bucket, path):
    s3 = boto3.client("s3")
    content = []

    
    respuesta = s3.list_objects_v2(Bucket=bucket, Prefix=path, Delimiter='/')

    # Get metadata.json  from bucket and path
    try:
        response = s3.get_object(Bucket=bucket, Key=path + "metadata.json")
        metadata = json.loads(response['Body'].read())
        
    except Exception as e:
        metadata = None


    for objeto in respuesta.get('Contents', []):
        print("Obj:" + objeto['Key'])
        content.append(objeto['Key'])

    for prefijo in respuesta.get('CommonPrefixes', []):
        print("Pref:" + prefijo['Prefix'])
        content.append(prefijo['Prefix'])

    return {"content": content, "metadata": metadata}

############################################################################################################
def getFilePreview(bucket, path):
    s3 = boto3.client("s3")
    results = []
    byte_range = 'bytes=0-1000'
    response = s3.get_object(Bucket=bucket, Key=path)
    response = s3.get_object(Bucket=bucket, Key=path, Range=byte_range)

    results.append(response['Body'].read())

    return results

############################################################################################################
def updateMetadata(metadata):
    # Create JSON file in bucket metadata.bucket and key metadata.path  with name metadata.json. The content of the file is metadata itself in JSON format
    s3 = boto3.client("s3")

    # Create file in bucket
    try:
        s3.put_object(Bucket=metadata.bucket, Key=metadata.path + "metadata.json", Body=json.dumps(metadata.dict()))
        print("Metadata updated in bucket: " + json.dumps(metadata.dict()))
        return True
    except Exception as e:
        print("Error creating file in bucket: " + str(e))
        return False









