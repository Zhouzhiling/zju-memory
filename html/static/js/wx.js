let wxParam = {};

let wxInit = () => {
    let wx_share = (param, url) => {
        $.ajax({
            type: "GET",
            url: "",
            data: { url: url },
            timeout: 30000,
            success: function (res) {
                if (res.code == 0) {
                    let data = res['signature'];
                    wxParam = param;
                    store.set('signature', data);
                    wx.config({
                        debug: false,
                        appId: data['appid'],
                        timestamp: data['timestamp'],
                        nonceStr: data['nonceStr'],
                        signature: data['signature'],
                        jsApiList: ['onMenuShareTimeline', 'onMenuShareAppMessage', 'onMenuShareQQ', 'onMenuShareWeibo', 'onMenuShareQZone'] // 必填，需要使用的JS接口列表，所有JS接口列表见附录2
                    });
                }
            },
            error: function (res) { }
        });
    };
    wx_share({
        title: "浙大记忆",
        desc: "领取属于你的浙大记忆",
        link: "https://api.96486d9b.cn",
        imgUrl: "https://api.96486d9b.cn/static/images/zju.png",
        successFn: function () {
            // 用户确认分享后执行的回调函数
        },
        cancelFn: function () {
            // 用户取消分享后执行的回调函数
        }
    }, location.href.split('#')[0].replace(/&/g, '%26'));

    wx.ready(function () {
        //分享到朋友圈
        wx.onMenuShareTimeline({
            title: wxParam.title,
            link: wxParam.link,
            imgUrl: wxParam.imgUrl,
            success: function () {
                if (wxParam.successFn) { wxParam.successFn(); }
            }, cancel: function () {
                if (wxParam.cancelFn) { wxParam.cancelFn(); }
            }
        });

        //分享给朋友
        wx.onMenuShareAppMessage({
            title: wxParam.title,
            desc: wxParam.desc,
            link: wxParam.link,
            imgUrl: wxParam.imgUrl,
            type: wxParam.type,
            dataUrl: wxParam.dataUrl,
            success: function () {
                if (wxParam.successFn) { wxParam.successFn(); }
            }, cancel: function () {
                if (wxParam.cancelFn) { wxParam.cancelFn(); }
            }
        });

        //分享到QQ
        wx.onMenuShareQQ({
            title: wxParam.title,
            desc: wxParam.desc,
            link: wxParam.link,
            imgUrl: wxParam.imgUrl,
            success: function () {
                if (wxParam.successFn) { wxParam.successFn(); }
            }, cancel: function () {
                if (wxParam.cancelFn) { wxParam.cancelFn(); }
            }
        });

        //分享到腾讯微博
        wx.onMenuShareWeibo({
            title: wxParam.title,
            desc: wxParam.desc,
            link: wxParam.link,
            imgUrl: wxParam.imgUrl,
            success: function () {
                if (wxParam.successFn) { wxParam.successFn(); }
            }, cancel: function () {
                if (wxParam.cancelFn) { wxParam.cancelFn(); }
            }
        });

        //分享到QQ空间
        wx.onMenuShareQZone({
            title: wxParam.title,
            desc: wxParam.desc,
            link: wxParam.link,
            imgUrl: wxParam.imgUrl,
            success: function () {
                if (wxParam.successFn) { wxParam.successFn(); }
            }, cancel: function () {
                if (wxParam.cancelFn) { wxParam.cancelFn(); }
            }
        });
    });
}