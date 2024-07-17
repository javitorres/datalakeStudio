import requests
import urllib.parse
import os
import re
import mimetypes


def downloadFile(url, destination_dir):
    urllib.parse.unquote(url)

    r = requests.get(url, allow_redirects=True)
    fileName = None
    if r.status_code == 200:
        # let's try to guess the file format
        # when coming as an attachment, the filename is in the Content-Disposition header.

        if 'Content-Disposition' in r.headers:
            if (d := r.headers['Content-Disposition']) != 'inline':
                names = re.findall("filename=(.+)", d)
                if len(names) == 1:
                    fileName = names[0]
                else:
                    fileName = 'download'
        if not fileName and 'Content-Type' in r.headers:
            extension = mimetypes.guess_extension(r.headers['Content-Type'].split(';')[0])
            fileName = 'download' + extension
            # detect geojson format in a json file
            if extension == '.json' and "FeatureCollection" in str(r.content[:27]):
                fileName = 'download.geojson'
        if fileName:
            fileName = os.path.join(destination_dir, fileName)
            open(fileName, 'wb').write(r.content)
        print("Downloaded file: " + str(fileName))
        return fileName
    else:
        print("Error downloading file: " + str(r.status_code))
        return None