function stop_load() {
    // ロード停止
    let bg = document.getElementById('loader-bg');
    let loader = document.getElementById('loader');

    bg.classList.add('fadeout-bg');
    loader.classList.add('fadeout-loader');
    bg.setAttribute('class', 'is-hide');
}


function start_load() {
    let bg = document.getElementById('loader-bg'),
        loader = document.getElementById('loader');
    /* ロード画面の非表示を解除 */
    bg.classList.remove('is-hide');
    loader.classList.remove('is-hide');

}