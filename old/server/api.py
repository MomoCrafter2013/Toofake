import json
import uuid
import requests
import os
import io
from flask import Flask, request
import models.instant
from parse import Parse
from urllib.parse import quote_plus
import pendulum
from PIL import Image

app = Flask(__name__)

api_url="https://mobile.bereal.com/api"
google_api_key="AIzaSyDwjfEeparokD7sXPVQli9NsTuhT6fJ6iA"

head = {
    "x-firebase-client": "apple-platform/ios apple-sdk/19F64 appstore/true deploy/cocoapods device/iPhone9,1 fire-abt/8.15.0 fire-analytics/8.15.0 fire-auth/8.15.0 fire-db/8.15.0 fire-dl/8.15.0 fire-fcm/8.15.0 fire-fiam/8.15.0 fire-fst/8.15.0 fire-fun/8.15.0 fire-install/8.15.0 fire-ios/8.15.0 fire-perf/8.15.0 fire-rc/8.15.0 fire-str/8.15.0 firebase-crashlytics/8.15.0 os-version/14.7.1 xcode/13F100",
    "user-agent":"FirebaseAuth.iOS/8.15.0 AlexisBarreyat.BeReal/0.22.4 iPhone/14.7.1 hw/iPhone9_1",
    "x-ios-bundle-identifier": "AlexisBarreyat.BeReal",
    "x-firebase-client-log-type": "0",
    "x-client-version": "iOS/FirebaseSDK/8.15.0/FirebaseCore-iOS",
}

@app.route("/")
def slash():
    return "<p>-</p>"

@app.route("/sendotp/<phone>")
def send_otp(phone: str):
    print("=========================================")
    print(phone)
    print(type(phone))
    res = requests.post(
        #url="https://www.googleapis.com/identitytoolkit/v3/relyingparty/sendVerificationCode",
        url = "https://us-central1-befake-623af.cloudfunctions.net/login",
        #params={"key":google_api_key},
        #data={
         #       "phoneNumber": phone,
                #"iosReceipt": "AEFDNu_OEYwP_wtXAGYh-EwqHILEHOSN1s8f2YLL1b_vauehU_h7cbV6e07IxeqqWcXyXb_mWD73LqNPFEgId1dv4uSnh1gDZ3yN83cHfqINn0pcOoAETcAz8PjfYk1HIWvJ",
                #"iosSecret": "BmwqtXs9BqcM00ts",
          #  },
        data = {
            "phoneNumber": phone,
        },
    )
    print('----- SENT OTP -----')
    print(res)
    print(res.text)
    print(res.status_code)
    print('----- END -----')
    return {}
    #return {'error':'error'}
    return res.status_code

@app.route("/verifyotp/<otp>/<session>")
def verify_otp(otp: str, session: str):
    if session is None:
        raise Exception("No open otp session.")
    res = requests.post(
        url="https://www.googleapis.com/identitytoolkit/v3/relyingparty/verifyPhoneNumber",
        params={"key": google_api_key},
        data={
            "sessionInfo": session,
            "code": otp,
            "operation": "SIGN_UP_OR_IN",
        },
    ).json()
    print("----- VERIFIED OTP -----")
    print(res)
    print('----- END -----')
    return res

@app.route("/refresh/<token>")
def refresh(token: str):
    res = requests.post(
        url="https://securetoken.googleapis.com/v1/token",
        params={"key": google_api_key},
        data={
            "refresh_token": token,
            "grant_type": "refresh_token"
        }
    ).json()
    print("----- REFRESHED -----")
    #print(res)
    print('----- END -----')
    return res

@app.route("/instants/<token>")
def instants(token: str):
    #print('token', token)
    res = requests.get(
        url=api_url+'/feeds/friends',
        headers={"authorization": token},
    )
    if res.status_code != 200:
        print("instant fetch error", res.json())
        return res.json()
    res = res.json()
    print("----- INSTANTS -----")
    #print(res)
    #print("<>")
    ret = Parse.instant(res)
    #print(ret)
    print('----- END -----')
    return json.dumps(ret)

# does not work anymore, using signedpostinstant ==================================================
@app.route("/postinstant/<token>/<uid>/", methods=["POST"])
@app.route("/postinstant/<token>/<uid>/<caption>", methods=["POST"])
def postinstant(token:str, uid:str, caption:str=''):
    print('========================= attempt post =========================')
    print('CAPTION:', caption)
    def get_data(version):  
        version_data = io.BytesIO()
        version.save(version_data, format="JPEG", quality=90)
        version_data = version_data.getvalue()
        return version_data
    
    def extension(img):
        mime_type = Image.MIME[img.format]
        if mime_type != "image/jpeg":
            if not img.mode == "RGB":
                img = img.convert("RGB")
        return img

    p = request.files['primary'] 
    primary = Image.open(io.BytesIO(p.read()))
    primary = extension(primary)
    prim_data = get_data(primary) #this is the primary image file
    primarysize = str(len(prim_data))

    s = request.files['secondary']
    secondary = Image.open(io.BytesIO(s.read()))
    secondary = extension(secondary)
    sec_data = get_data(secondary) #this is the secondary image file
    secondarysize = str(len(sec_data))

    def upload(file_data, size, alt: bool):
        name = f"Photos/{uid}/bereal/{uuid.uuid4()}-{int(pendulum.now().timestamp())}{'-secondary' if alt else ''}.webp"
        print("name: ", name)

        json_data = {"cacheControl": "public,max-age=172800","contentType": "image/webp","metadata": {"type": "bereal"},"name": name}
        headers = {
            "x-goog-upload-protocol": "resumable",
            "x-goog-upload-command": "start",
            "x-firebase-storage-version": "ios/9.4.0",
            "x-goog-upload-content-type": "image/webp","content-type": "application/json","x-firebase-gmpid": "1:405768487586:ios:28c4df089ca92b89",
            "Authorization": f"Firebase {token}",
            "x-goog-upload-content-length": size,
            "content-type": "application/json",
            "x-firebase-gmpid": "1:405768487586:ios:28c4df089ca92b89",
        }
        params = {"uploadType": "resumable","name": name}

        uri = f"https://firebasestorage.googleapis.com/v0/b/storage.bere.al/o/{quote_plus(name)}"
        print("URI: ", uri)
        init_res = requests.post(uri, headers=headers, params=params, data=json.dumps(json_data))
        print("INITIAL RESULT: ", init_res)
        print("INITIAL RESULT MSG: ", init_res.text)
        if init_res.status_code != 200: raise Exception(f"Error initiating upload: {init_res.status_code}")
        upload_url = init_res.headers["x-goog-upload-url"]
        upheaders = {"x-goog-upload-command": "upload, finalize","x-goog-upload-protocol": "resumable",
        "x-goog-upload-offset": "0","content-type": "image/jpeg",}
        # upload the image
        print("UPLOAD URL", upload_url)
        upload_res = requests.put(url=upload_url, headers=upheaders, data=file_data)
        if upload_res.status_code != 200: raise Exception(f"Error uploading image: {upload_res.status_code}, {upload_res.text}")
        res_data = upload_res.json()
        return res_data
    
    primary_res = upload(prim_data, primarysize, False)
    secondary_res = upload(sec_data, secondarysize, True)

    print(primary_res)
    print(secondary_res)

    primary_ret_name = primary_res['name']
    secondary_ret_name = secondary_res['name']
    primary_bucket = primary_res['bucket']
    secondary_bucket = secondary_res['bucket']
    primary_url = f"https://{primary_bucket}/{primary_ret_name}"
    secondary_url = f"https://{secondary_bucket}/{secondary_ret_name}"

    now = pendulum.now()
    taken_at = f"{now.to_date_string()}T{now.to_time_string()}Z"

    payload = {
        "isPublic": False,
        "isLate": False,
        "retakeCounter": 0,
        "takenAt": taken_at,
        #"location": location,
        "caption": caption,
        "backCamera": {
            "bucket": "storage.bere.al",
            "height": 2000,
            "width": 1500,
            "path": primary_url.replace("https://storage.bere.al/", ""),
        },
        "frontCamera": {
            "bucket": "storage.bere.al",
            "height": 2000,
            "width": 1500,
            "path": secondary_url.replace("https://storage.bere.al/", ""),
        },
    }
    complete_res = requests.post(url=api_url+'/content/post',json=payload,headers={"authorization": token},)
    print(complete_res)
    print(complete_res.json())

    return complete_res.json()

@app.route("/signedpostinstant/<token>/<uid>/", methods=["POST"])
@app.route("/signedpostinstant/<token>/<uid>/<caption>", methods=["POST"])
def signedpostinstant(token:str, uid:str, caption:str=''):
    #==============================================================================================
    print(request.form.to_dict())
    print(request.files)
    print(caption)
    #==============================================================================================

    ispublic = json.loads(request.form.to_dict()['public'].lower())
    latitude = request.form.to_dict()['latitude']
    longitude = request.form.to_dict()['longitude']
    haslocation = json.loads(request.form.to_dict()['haslocation'].lower())
    print(ispublic, type(ispublic))
    print(latitude, type(latitude))
    print(longitude, type(longitude))
    print(haslocation, type(haslocation))

    #file manipulation
    def get_data(version):  
        version_data = io.BytesIO()
        version.save(version_data, format="JPEG", quality=90)
        version_data = version_data.getvalue()
        return version_data
    
    def extension(img):
        mime_type = Image.MIME[img.format]
        if mime_type != "image/jpeg":
            print("Converting Mime Type")
            if not img.mode == "RGB":
                img = img.convert("RGB")
        return img

    p = request.files['primary'] 
    primary = Image.open(io.BytesIO(p.read()))
    primary = extension(primary)
    prim_data = get_data(primary) #this is the primary image file
    primarysize = str(len(prim_data))

    s = request.files['secondary']
    secondary = Image.open(io.BytesIO(s.read()))
    secondary = extension(secondary)
    sec_data = get_data(secondary) #this is the secondary image file
    secondarysize = str(len(sec_data))
    #==============================================================================================

    apiurl = f"https://mobile.bereal.com/api/content/posts/upload-url?mimeType=image%2Fwebp"
    headers = {
        "authorization": "Bearer {}".format(token),
        "accept-encoding": "gzip",
        "user-agent": "okhttp/4.10.0",
        "if-none-match": 'W/"507-M16WxEgA1LffRgMAGSRIlonfNV8"'
    }
    signed_upload_res = requests.get(url=apiurl, headers=headers)
    print("----- SIGNED UPLOAD -----")
    print(signed_upload_res)
    print(signed_upload_res.json())
    if signed_upload_res.status_code != 200: return signed_upload_res.json()
    print('----- END -----')

    signed_upload_res = signed_upload_res.json()
    signed_upload_res = signed_upload_res["data"]

    prim_path = signed_upload_res[0]["path"]
    sec_path = signed_upload_res[1]["path"]

    def intostorage(signed_res, file):
        bucket = signed_res['bucket']
        expires = signed_res['expireAt']
        image_path = signed_res['path']
        bucket_headers = signed_res['headers']
        bucket_url = signed_res['url']

        print("----- BUCKET INFO -----")
        print(bucket, "\n >>>>")
        print(expires, "\n >>>>")
        print(image_path, "\n >>>>")
        print(bucket_headers, "\n >>>>")
        print(bucket_url, "\n >>>>")
        print('----- END -----')

        ret = requests.put(url=bucket_url, headers=bucket_headers, data=file)
        print("----- BUCKET PUT RESP -----")
        print(ret)
        print(ret.text)
        print('----- END -----')
        if ret.status_code != 200: raise Exception(f"Error uploading image: {ret.status_code}, {ret.text}")
        return ret

    prim_bucket_ret = intostorage(signed_upload_res[0] ,prim_data)
    sec_bucket_ret = intostorage(signed_upload_res[1] ,sec_data)
    print("----- BUCKET RET -----")
    print(prim_bucket_ret)
    print(">>>>>")
    print(sec_bucket_ret)
    print('----- END -----')

    now = pendulum.now()
    taken_at = f"{now.to_date_string()}T{now.to_time_string()}Z"

    payload = {
        "isPublic": ispublic,
        "isLate": False,
        "retakeCounter": 0,
        "takenAt": taken_at,
        #"location": location,
        "caption": caption,
        "backCamera": {
            "bucket": "storage.bere.al",
            "height": 2000,
            "width": 1500,
            "path": prim_path,
        },
        "frontCamera": {
            "bucket": "storage.bere.al",
            "height": 2000,
            "width": 1500,
            "path": sec_path,
        },
    }
    if haslocation: payload["location"] = {"latitude": latitude,"longitude": longitude,}

    complete_res = requests.post(url=api_url+'/content/post',json=payload,headers={"content-type" : "application/json", "authorization": token},)
    print(complete_res)
    print(complete_res.json())

    return complete_res.json()


@app.route("/me/<token>")
def me(token: str):
    res = requests.get(
        url=api_url+'/person/me',
        headers={"authorization": token},
    ).json()
    print("----- ME -----")
    print(res)
    print('----- END -----')
    return Parse.me(res)

@app.route("/comment/<postid>/<comment>/<token>")
def comment(postid: str, comment: str, token: str):
    print(postid)
    res = requests.post(
        url=api_url+'/content/comments',
        data={"content":comment}, 
        params={"postId":postid}, 
        headers={"authorization": token}
    ).json()
    print("----- COMMENT -----")
    print(res)
    print('----- END -----')
    return res

if __name__ == '__main__':
    #app.run(port=5100, debug=True)
    app.run(debug=True, port=os.getenv("PORT", default=5100))
    print('on')