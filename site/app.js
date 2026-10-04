"use strict";

const sources = {
  mark: {
    title: "萨克斯独奏谱与伴奏",
    owner: "马克也有Club",
    summary: "原视频标题：【萨克斯谱】诀别书 邓垚 附伴奏。",
    access: "查看原视频简介中的店铺与曲谱获取说明。",
    url: "https://www.bilibili.com/video/BV18t421W7ev/",
  },
  "sweet-performance": {
    title: "多乐器演奏与萨克斯谱",
    owner: "泪樱甜心",
    summary: "《诀别书》的多乐器接力演奏，发布标题注明萨克斯、单簧管等乐器曲谱及伴奏。",
    access: "查看原视频和发布者主页，确认适用的萨克斯版本与获取方式。",
    url: "https://www.bilibili.com/video/BV1Fk4y1f7Ny/",
  },
  "sweet-scores": {
    title: "萨克斯与其他管弦乐版本",
    owner: "甜心的音乐屋",
    summary: "《诀别书》多乐器曲谱入口，发布标题包含萨克斯、长笛、单簧管及弦乐等版本。",
    access: "原视频说明：各乐器乐谱与伴奏的获取或定制方式见发布者个人简介。",
    url: "https://www.bilibili.com/video/BV1gi4y1s7q2/",
  },
};

const dialog = document.getElementById("source-dialog");
document.querySelectorAll("[data-detail]").forEach((button) => {
  button.addEventListener("click", () => {
    const source = sources[button.dataset.detail];
    if (!source) return;
    if (typeof dialog.showModal !== "function") {
      window.open(source.url, "_blank", "noopener,noreferrer");
      return;
    }
    document.getElementById("dialog-title").textContent = source.title;
    document.getElementById("dialog-summary").textContent = source.summary;
    document.getElementById("dialog-owner").textContent = source.owner;
    document.getElementById("dialog-access").textContent = source.access;
    document.getElementById("dialog-link").href = source.url;
    dialog.showModal();
  });
});
document.getElementById("close-dialog").addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target !== dialog) return;
  const bounds = dialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right ||
      event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
});
