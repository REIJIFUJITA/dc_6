let tag = document.createElement("script");
tag.src = "https://www.youtube.com/iframe_api";
let firstScriptTag = document.getElementsByTagName("script")[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

let player;

function onYouTubeIframeAPIReady() {
  player = new YT.Player("player", {
    height: "300",
    width: "550",
    videoId: "",
    events: {
      onReady: onPlayerReady,
    },
  });
}

// プレイヤー準備完了時に呼ばれる
function onPlayerReady(event) {
  document.querySelectorAll('input[name="track_name"]').forEach((input) => {
    input.addEventListener("change", function () {
      const videoId = this.dataset.videoId;
      if (videoId) {
        player.loadVideoById(videoId); // 選択された動画を再生
      }
    });
  });
}
