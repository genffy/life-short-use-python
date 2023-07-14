import json
import gpxpy
import gpxpy.gpx

gpx = gpxpy.gpx.GPX()

# Create first track in our GPX:
gpx_track = gpxpy.gpx.GPXTrack()
gpx.tracks.append(gpx_track)

# Create first segment in our GPX track:
gpx_segment = gpxpy.gpx.GPXTrackSegment()
gpx_track.segments.append(gpx_segment)

# Create points:
# read from json file
# {
#     "code": 0,
#     "message": "",
#     "data": {
#         "createTime": "2023/07/14",
#         "distance": 177.95,
#         "region": "上海市",
#         "totalAscent": 0,
#         "totalDecline": 0,
#         "wgs84trackJsonPath": "",
#         "tracks": [
#             {
#                 "alt": 0.0,
#                 "latitude": 31.30137183876083,
#                 "longitute": 121.39867816570057
#             }
#         ]
#     }
# }
with open("./data/DetailsRoutesWeb.json", "r") as f:
    data = json.load(f)["data"]
    tracks = data["tracks"]
    altList = data["altList"]
    for track in tracks:
        # get alt by index
        # "alt": 0.0,
        # "latitude": 31.30137183876083,
        # "longitute": 121.39867816570057
        gpx_segment.points.append(
            gpxpy.gpx.GPXTrackPoint(track["latitude"], track["longitute"])
        )
# You can add routes and waypoints, too...
with open("./data/routes.gpx", "w") as f:
    f.write(gpx.to_xml())
