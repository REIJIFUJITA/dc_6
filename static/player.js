// youtube_player.js

// YouTube Player APIを非同期で読み込む
let tag = document.createElement("script");
tag.src = "https://www.youtube.com/iframe_api";
let firstScriptTag = document.getElementsByTagName("script")[0];
firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);

let player;

// プレーヤーの初期化
function onYouTubeIframeAPIReady() {
  player = new YT.Player("player", {
    height: "360",
    width: "640",
    videoId: "", // 初期状態では空
    events: {
      onReady: onPlayerReady,
    },
  });
}

function onPlayerReady(event) {
  console.log("YouTube Player is ready");
}

// ラジオボタンの変更イベントで動画を再生
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('input[name="selected_video"]').forEach((radio) => {
    radio.addEventListener("change", (event) => {
      const [videoId] = event.target.value.split("|");

      // プレーヤーに動画をロードして再生
      if (player && player.loadVideoById) {
        player.loadVideoById(videoId);
      } else {
        console.error("YouTube Player is not initialized");
      }
    });
  });
});
