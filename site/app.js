"use strict";
const ranges = [[1,28],[29,56],[57,84],[85,109]];
const image = document.getElementById("score-image");
const select = document.getElementById("page-select");
const previous = document.getElementById("previous-page");
const next = document.getElementById("next-page");
const scroll = document.getElementById("score-scroll");
const zoom = document.getElementById("zoom-score");
const status = document.getElementById("viewer-status");
const error = document.getElementById("load-error");
const printButton = document.getElementById("print-score");
let currentPage = 1;
function showPage(number) {
  currentPage = Math.max(1, Math.min(4, Number(number)));
  const [first,last] = ranges[currentPage-1];
  select.value = String(currentPage);
  image.src = `./scores/juebieshu/page-${currentPage}.png`;
  image.alt = `诀别书萨克斯曲谱，第${currentPage}页，第${first}至${last}小节`;
  document.getElementById("measure-range").textContent = `第 ${first}–${last} 小节`;
  status.textContent = `第${currentPage}页，第${first}至${last}小节`;
  previous.disabled = currentPage === 1;
  next.disabled = currentPage === 4;
  scroll.scrollTop = 0;
  scroll.scrollLeft = 0;
  error.hidden = true;
}
select.disabled = false;
next.disabled = false;
zoom.disabled = false;
printButton.disabled = false;
select.addEventListener("change", () => showPage(select.value));
previous.addEventListener("click", () => showPage(currentPage-1));
next.addEventListener("click", () => showPage(currentPage+1));
image.addEventListener("error", () => { error.hidden = false; });
image.addEventListener("load", () => { error.hidden = true; });
zoom.addEventListener("click", () => {
  const expanded = scroll.classList.toggle("zoomed");
  zoom.setAttribute("aria-pressed", String(expanded));
  zoom.textContent = expanded ? "适合页面" : "放大阅读";
});
document.addEventListener("keydown", (event) => {
  if (["SELECT","INPUT","TEXTAREA","BUTTON"].includes(event.target.tagName) ||
      event.altKey || event.ctrlKey || event.metaKey || event.shiftKey ||
      scroll.classList.contains("zoomed")) return;
  if (event.key === "ArrowLeft") { event.preventDefault(); showPage(currentPage-1); }
  if (event.key === "ArrowRight") { event.preventDefault(); showPage(currentPage+1); }
});
printButton.addEventListener("click", async () => {
  printButton.disabled = true;
  printButton.textContent = "准备打印…";
  try {
    await Promise.all([...document.querySelectorAll(".print-pages img")].map(img => img.decode()));
    window.print();
  } catch {
    error.hidden = false;
    error.textContent = "打印谱页加载失败，请下载 A4 PDF 后打印。";
  } finally {
    printButton.disabled = false;
    printButton.textContent = "打印全部 4 页";
  }
});
