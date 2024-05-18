import io
import base64
import mimetypes
import requests
import av
from urllib.parse import urlparse
from PIL import Image

def GuessMediaType(pathOrUrl: str) -> str:
    mimetype, _ = mimetypes.guess_type(pathOrUrl)
    if None != mimetype:
        return mimetype
    r=requests.head(pathOrUrl)
    return r.headers.get("content-type")

def ConvertVideoFormat(bytesSrc, format):
    videoSrc = av.open(io.BytesIO(bytesSrc))
    if format == videoSrc.format:
        return bytesSrc.getvalue()
    
    bytesDst = io.BytesIO()
    videoDst = av.open(bytesDst, mode='w', format=format)
    
    streamSrc = videoSrc.streams.video[0]
    streamDst = videoDst.add_stream('libx264', rate=streamSrc.average_rate)
    streamDst.width = streamSrc.width
    streamDst.height = streamSrc.height
    streamDst.pix_fmt = 'yuv420p'

    for frame in videoSrc.decode(video=0):
        for packet in streamDst.encode(frame):
            videoDst.mux(packet)

    for packet in streamDst.encode():
        videoDst.mux(packet)

    videoSrc.close()
    videoDst.close()
    bytesDst.seek(0)
    return bytesDst.getvalue()

class AImage():
    def __init__(self, format: str, data: bytes):
        self.format = format
        self.data = data
        return
    
    def __str__(self) -> str:
        return f"< AImage object in {self.format} format. >"
    
    def ToJson(self):
        return {'format': self.format, 'data': base64.b64encode(self.data).decode('utf-8')}
    
    def Convert(self, format: str):
        if format == self.format:
            return self
        imageBytes = io.BytesIO()
        image = Image.open(io.BytesIO(self.data))
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(imageBytes, format=format)
        return AImage(format=format, data=imageBytes.getvalue())
    
    def Standardize(self):
        return self.Convert(format="JPEG")

class AImageLocation():
    def __init__(self, urlOrPath: str):
        self.urlOrPath = urlOrPath
        return
    
    def IsURL(self, ident: str) -> bool:
        return urlparse(ident).scheme != ''
    
    def GetImage(self, ident: str) -> Image:
        if self.IsURL(ident):
            response = requests.get(ident)
            imageBytes = io.BytesIO(response.content)
            return Image.open(imageBytes)
        else:
            return Image.open(ident)

    def Standardize(self):
        image = self.GetImage(self.urlOrPath)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        imageByte = io.BytesIO()
        image.save(imageByte, format='JPEG')
        return AImage(format="JPEG", data=imageByte.getvalue())

class AVideo():
    def __init__(self, format: str, data: bytes):
        self.format = format
        self.data = data
        return
    
    def __str__(self) -> str:
        return f"< AVideo object in {self.format} format. >"
    
    def ToJson(self):
        return {'format': self.format, 'data': base64.b64encode(self.data).decode('utf-8')}
    
    def Standardize(self):
        return AVideo(format="mp4", data=ConvertVideoFormat(self.data, 'mp4'))

class AVideoLocation():
    def __init__(self, urlOrPath: str):
        self.urlOrPath = urlOrPath
        return
    
    def IsURL(self, ident: str) -> bool:
        return urlparse(ident).scheme != ''
    
    def GetVideo(self, ident: str):
        if self.IsURL(ident):
            response = requests.get(ident)
            videoBytes = io.BytesIO(response.content)
            return videoBytes.getvalue()
        else:
            with open(ident, "rb") as f:
                videoBytes = io.BytesIO(f.read())
                return videoBytes.getvalue()

    def Standardize(self):
        return AImage(format="mp4", data=ConvertVideoFormat(self.GetVideo(self.urlOrPath), "mp4"))
    
typeInfo = {AImage: {"modal": "image", "tag": False},
            AImageLocation: {"modal": "image", "tag": True},
            AVideo: {"modal": "video", "tag": False},
            AVideoLocation: {"modal": "video", "tag": True}}