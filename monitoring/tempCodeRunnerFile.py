location = data["location"]
    # statuscodeid = data["statuscodeid"]
    # errcodeid = data["errcodeid"]
    # if request.json["payment"] == None:
    #     payment = 0
    # else:
    #     payment =1

    # date_time = date.today()

    # payload = {
    #     "m_id": 1,
    #     "machineid": machineid,
    #     "location": location,
    #     "statuscodeid": statuscodeid,
    #     "errcodeid": errcodeid,
    #     "payment": payment,
    #     "date_time": date_time
    # }   

    # try:
    #     db.session.add(payload)
    #     db.session.commit()
    # except:
    #     code = 500
    #     result = {"code": code, "message": "Error Updating Data"}
    # if code == 200:
    #     result = payload.json()
    # return str(result), code