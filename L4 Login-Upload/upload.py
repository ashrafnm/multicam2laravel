import requests

url = 'http://150.7.136.76:80/api/upload-python'

file_paths = {
    'camera1': 'recording_202310031459/output_video_0.mp4',
    'camera2': 'recording_202310031459/output_video_1.mp4'
}

files = {}

try:
    for key, path in file_paths.items():
        files[key] = open(path, 'rb')

    response = requests.post(url, files=files)

    if response.status_code == 200:
        print('File uploaded successfully')
    else:
        print('File upload failed')

    print('HTTP Status Code:', response.status_code)
    print('HTTP Reason Phrase:', response.reason)
    print('Response Text:', response.text)
except requests.RequestException as e:
    print('Network error:', e)
except FileNotFoundError as e:
    print('File not found error:', e)
finally:
    # Ensure to close the files
    for file in files.values():
        file.close()
