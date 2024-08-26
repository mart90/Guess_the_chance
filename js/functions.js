function convertDatetime(dt) {
    dt = new Date(dt).toISOString().split('T')
    converted = dt[0]
    time = dt[1].substring(0, 5)
    if (time != "00:00") {
        converted += " " + time
    }
    return converted
}