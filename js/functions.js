function convertDatetime(dt) {
    dt = new Date(dt).toISOString().split('T')
    converted = dt[0]
    time = dt[1].substring(0, 5)
    if (time != "00:00") {
        converted += " " + time
    }
    return converted
}

function refreshToken() {
    var refreshCall = $.ajax({
        type: "GET",
        url: server_address + "backend/refresh_token",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('Authorization', 'Bearer ' + localStorage.getItem('token'));
        }
    });

    refreshCall.done(function (result) {
        localStorage.setItem('token', result.token)
        localStorage.setItem('token_expires_at', result.expires_at)
    });
}