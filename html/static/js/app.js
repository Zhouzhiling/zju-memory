let animation = {};
animation.initAnimationItems = function () {
    $('.animated').each(function () {
        var aniDuration, aniDelay;

        $(this).attr('data-origin-class', $(this).attr('class'));

        aniDuration = $(this).data('ani-duration');
        aniDelay = $(this).data('ani-delay');

        $(this).css({
            'visibility': 'hidden',
            'animation-duration': aniDuration,
            '-webkit-animation-duration': aniDuration,
            'animation-delay': aniDelay,
            '-webkit-animation-delay': aniDelay
        });
    });
};

animation.playAnimation = function (dom) {
    this.clearAnimation();

    var aniItems = $(dom).find('.animated');

    $(aniItems).each(function () {
        var aniName;
        $(this).css({ 'visibility': 'visible' });
        aniName = $(this).data('ani-name');
        $(this).addClass(aniName);
    });
};

animation.clearAnimation = function () {
    $('.animated').each(function () {
        $(this).css({ 'visibility': 'hidden' });
        $(this).attr('class', $(this).data('origin-class'));
    });
};

let reloadPage = (url) => {
    url = url.replace(/([?|&]randomweixin)[^&]+/g, '');
    if (url.indexOf('?') < 0) {
        url += "?"
    }
    else if (url.indexOf('=') >= 0) {
        url += "&"
    }
    var random = Math.random();
    url += 'randomweixin=' + random;
    window.location.href = url;
}

let app = {};

app.check = () => {
    data = store.get('data');
    if (data === undefined) {
        let url = 'index.html';
        reloadPage(url);
        return false;
    }
    return true;
}

app.init = function () {
    animation.initAnimationItems();
    $(".item").show();
    $(".overlay").show();
    fullscreen.init({
        'type': 2, 'useArrow': true,
        'useMusic': {
            src: "http://music.163.com/song/media/outer/url?id=486188245.mp3"
        },
        'pageShow': function (dom) {
            animation.playAnimation(dom);
            if ($(dom).index() == 4) {
                app.initSport();
            }
        }, 'pageHide': function (dom) {
        }
    });
    $("#audio").bind('ended', function () {
        $(this).parent().removeClass('play');
    });
    animation.playAnimation($(".item2"));
};

app.initEcard = () => {
    data = store.get('data')['ecard'];
    $("#ecard-total").html(data['total']);
    $("#ecard-most").html(data['most'][0]['mercname']);
    $("#ecard-most-2").html(data['most'][1]['mercname']);
    $("#ecard-most-3").html(data['most'][2]['mercname']);
    $("#ecard-most-count").html(data['most'][0]['count']);
    $("#ecard-biggest").html(data['biggest']['occtime'] + " " + data['biggest']['mercname']);
    $("#ecard-biggest-count").html(data['biggest']['tranamt']);
    $("#ecard-shower").html(data['shower']);
    $("#ecard-market").html(data['market']);
    $("#ecard-normal").html(data['normal']);
    $("#ecard-bank").html(data['bank']);
    $("#ecard-day-time").html(data['day']['time']);
    $("#ecard-day-count").html(data['day']['count']);
}

app.initJwbinfosys = () => {
    data = store.get('data')['jwbinfosys']
    $("#course-total-count").html(data['total_count']);
    $("#course-major-count").html(data['major_count']);
    $("#course-total-credit").html(data['total_credit']);
    for (let i in data['score']) {
        let br = "<br />";
        let span = $("<span></span>").text(data['score'][i]['name'] + " 成绩是 " + data['score'][i]['count']);
        $("#course-highest").append(br, span);
    }
    $("#course-teacher-name").html(data['teacher']['name']);
    $("#course-teacher-count").html(data['teacher']['count']);
    for (let i in data['teacher']['course']) {
        let br = i % 2 ? " " : "<br/>";
        let span = $("<span></span>").text(data['teacher']['course'][i]);
        $("#course-teacher").append(br, span);
    }
    $("#course-semester-name").html(data['semester']['name']);
    $("#course-semester-count").html(data['semester']['count']);
    $("#course-semester-avg").html(data['semester']['avg']);

    $("#course-first-name").html(data['first_course']['name']);
    $("#course-first-teacher").html(data['first_course']['teacher']);
    $("#course-first-place").html(data['first_course']['place']);
}

app.initSport = () => {
    let option = {
        title: {
            text: '',
            textStyle: {
                color: '#414141',
                fontStyle: 'normal',
                fontWeight: 'normal',
                fontFamily: "wenyue-houxiandai",
            }
        },
        tooltip: {
            trigger: 'axis',
            show: false,
        },
        calculable: true,
        xAxis: [
            {
                type: 'category',
                data: []
            }
        ],
        yAxis: [
            {
                type: 'value',
                show: false,
                scale: true
            }
        ],
        series: [
            {
                name: '身高',
                type: 'bar',
                clickable: false,
                data: [],
                markLine: {
                    data: [
                        { type: 'average', name: '平均值' }
                    ]
                },
                itemStyle: {
                    normal: {
                        label: {
                            show: true,
                            position: 'top',
                        }
                    }

                }
            }
        ]
    };

    data = store.get('data')['sport']
    let myChart1 = echarts.init(document.getElementById('height'), 'macarons');
    option['xAxis'][0]['data'] = data['year']
    option['series'][0]['data'] = data['height'];
    option['title']['text'] = '身高';
    option['series'][0]['type'] = 'line';
    option['series'][0]['name'] = '身高';
    myChart1.setOption(option);
    let myChart2 = echarts.init(document.getElementById('weight'));
    option['series'][0]['data'] = data['weight'];
    option['title']['text'] = '体重';
    option['series'][0]['type'] = 'bar';
    option['series'][0]['name'] = '体重';
    myChart2.setOption(option);
    bmi_data = data['bmi'];
    $("#sport-bmi").html(bmi_data[bmi_data.length - 1]);
    if (bmi_data[bmi_data.length - 1] > bmi_data[bmi_data.length - 2]) {
        $("#sport-change").html("↗");
    } else {
        $("#sport-change").html("↘");
    }
    $("#sport-score").html(data['score']);
}


app.initLibrary = () => {
    data = store.get('data')['library'];
    if (data['total_count'] !== 0) {
        $("#library-first-book-date").html(data['first_book']['date']);
        $("#library-first-book-author").html(data['first_book']['author']);
        $("#library-first-book-name").html(data['first_book']['name']);

        $("#library-last-book-date").html(data['last_book']['date']);
        $("#library-last-book-author").html(data['last_book']['author']);
        $("#library-last-book-name").html(data['last_book']['name']);

        $("#library-total-count").html(data['total_count']);

        $("#library-author-name").html(data['author']['name']);
        $("#library-author-count").html(data['author']['count']);

        $("#library-place-count").html(data['place']['count']);
        $("#library-place-most-name").html(data['place']['most_name']);

        let topic = "";
        for (let i in data['topic']) {
            topic += data['topic'][i];
            topic += " ";
        }
        $("#library-topic").html(topic);
    }
    else {
        // $("#library-normal").hide();
        $("#library-none").show();
    }
}

app.initCC98 = () => {
    data = store.get('data')['cc98'];
    gender = data['gender'];
    if (gender === 'boy')
        $("#cc98-avatar").attr('src', 'static/images/cc98_boy.png');
    else
        $("#cc98-avatar").attr('src', 'static/images/cc98_gril.png');
    $("#cc98-count").html(data['count']);
    $("#cc98-login-times").html(data['login_times']);
    $("#cc98-comment-times").html(data['comment_times']);
    $("#cc98-follow-count").html(data['follow_count']);
    $("#cc98-fan-count").html(data['fan_count']);
    $("#cc98-register-time").html(data['register_time']);
    $("#cc98-post-count").html(data['post_count']);
    if (data['count'] !== 0) {
        if (data['count'] > 1) {
            $("#cc98-comment1").html("多面");
        } else {
            $("#cc98-comment1").html("简单");
        }
        if (data['comment_times'] > 50) {
            $("#cc98-comment2").html("灌水怪");
        } else {
            $("#cc98-comment2").html("潜水党");
        }
    } else {
        $("#cc98-normal").hide();
        $("#cc98-none").show();
    }
}

$(document).ready(function () {
    if (!app.check())
        return;
    app.initEcard();
    app.initJwbinfosys();
    app.initLibrary();
    app.initCC98();
    app.init();

    // //开启下一页
    // $(".btn").click(function () {
    //     var item = $('.item2');
    //     item.attr('state', 'prev');
    //     item.siblings('.item').removeAttr('state');

    //     var currentItem = item.next();
    //     currentItem.attr('state', 'next');

    //     item.css('-webkit-transform', 'scale(.8)');
    //     item.next().css('-webkit-transform', 'translate3d(0,0,0)');
    //     return false;
    // });
});

!(function (win, doc) {
    function setFontSize() {
        var winWidth = window.innerWidth;
        var size = (winWidth / 640) * 100;
        doc.documentElement.style.fontSize = (size < 100 ? size : 100) + 'px';
    }

    var evt = 'onorientationchange' in win ? 'orientationchange' : 'resize';

    var timer = null;

    win.addEventListener(evt, function () {
        clearTimeout(timer);

        timer = setTimeout(setFontSize, 300);
    }, { passive: false });

    win.addEventListener("pageshow", function (e) {
        if (e.persisted) {
            clearTimeout(timer);

            timer = setTimeout(setFontSize, 300);
        }
    }, { passive: false });

    // 初始化
    setFontSize();

}(window, document));