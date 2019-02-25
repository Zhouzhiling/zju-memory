let login = () => {
    let username = $("#username").val();
    let password = $("#password").val();
    if (username && password) {
        $('#loading').show();
        $.ajax({
            type: "POST",
            url: "http://localhost:8000/login",
            data: { username: $("#username").val(), password: $("#password").val() },
            success: function (data) {
                if (data['status']) {
                    store.set('data', data);
                    let url = 'index.html';
                    window.location.href = url;
                }
            }
        });
    } else {
        if (!password)
            $("#password").focus();
        if (!username)
            $("#username").focus();
    }
}