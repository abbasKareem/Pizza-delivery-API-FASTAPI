from fastapi.encoders import jsonable_encoder


def success_response(data, status_code, message):
    print(data)
    response = {
        "data": data,
        "status_code": status_code,
        "message": message
    }
    return jsonable_encoder(response)


def error_response(status_code, message):
    response = {
        "status_code": status_code,
        "message": message
    }
    return jsonable_encoder(response)
