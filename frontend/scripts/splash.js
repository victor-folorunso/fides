window.addEventListener("load", () => {
  const splash = document.getElementById("splash-screen");
  const content = document.getElementById("main-content");
  const splashImg = document.getElementById("splash-image");

  const page = document.body.dataset.page || "default";
  splashImg.src = `/assets/splash-${page}.jpeg`;

  splash.classList.add("fade-out");
  setTimeout(() => {
    splash.style.display = "none";
    content.style.display = "block";
  }, 1000);
});
