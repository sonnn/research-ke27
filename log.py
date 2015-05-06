def log(message, codes=None):
    codes = ["log"] if codes == None else codes

    for code in codes:
        if code == "log":
            message = "[Log] " + message
        elif code == "error":
            message = "[Error] " + message
        elif code == "request":
            message = "[Request] " + message
        elif code == "forum":
            message = "[Forum] " + message
        elif code == "thread":
            message = "[Thread] " + message
        elif code == "post":
            message = "[Post] " + message
        else:
            message = code + " " + message

    print message
