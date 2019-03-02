var util = (function () {
    var u = navigator.userAgent.toLowerCase();
    return {
        isIphone: function () { return (RegExp("iphone").test(u) || RegExp("ipod touch").test(u)) },
        isIpad: function () { return RegExp("ipad").test(u) },
        isAndroid: function () { return (RegExp("android").test(u) || RegExp("android 2").test(u)) },
        isMB: function () { return (util.isIphone() || util.isIpad() || util.isAndroid()) }
    };
})();
window.util = util;
(function () {
    if (!util.isMB()) {
        window.location.href = 'mobile.html';
    }
})();


$(document).ready(function () {
    $(document).bind("click", (event) => {
        if ($(event.target).is('body')) {
            $('.notice').hide(1000);
        }
    });
    $("#close-btn").bind('click', (event) => {
        $('.notice').hide(1000);
    });
    wxInit();
});


loginFlag = false;
let login = () => {
    if (!loginFlag) {
        $('.notice').show();
        loginFlag = true;
        return
    }
    let username = $("#username").val();
    let password = $("#password").val();
    if (username && password) {
        $('#loading').show();
        $.ajax({
            type: "POST",
            url: "",
            data: { username: $("#username").val(), password: $("#password").val() },
            timeout: 30000,
            error: function (XMLHttpRequest, textStatus, errorThrown) {
                $('#loading').hide();
                $("body").overhang({
                    type: "error",
                    message: "网络超时",
                });
            },
            success: function (data) {
                if (data['status']) {
                    store.set('data', data);
                    var queue = new createjs.LoadQueue();
                    queue.on("complete", handleComplete, this);
                    queue.loadManifest([
                        { id: "t_8", src: "./static/font/WenYue-HouXianDaiTi-NC-W4-75.otf" },
                        { id: "t_1", src: "./static/images/1.jpg" },
                        { id: "t_3", src: "./static/images/3.jpg" },
                        { id: "t_4", src: "./static/images/4.jpg" },
                        // { id: "t_5", src: "./static/images/5.jpg" },
                        // { id: "t_6", src: "./static/images/6.jpg" },
                        // { id: "t_7", src: "./static/images/7.jpg" },
                    ]);
                    function handleComplete() {
                        let url = 'app.html';
                        window.location.href = url;
                    }
                } else {
                    $('#loading').hide();
                    if (data['msg'] === 'login error') {
                        $("body").overhang({
                            type: "error",
                            message: "检查账号密码",
                        });
                    }
                    if (data['msg'] === 'fetch error') {
                        $("body").overhang({
                            type: "error",
                            message: "数据拉取不完整",
                        });
                    }
                    if (data['msg'] === 'stuid error') {
                        $("body").overhang({
                            type: "error",
                            message: "学号不在允许范围",
                        });
                    }

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
