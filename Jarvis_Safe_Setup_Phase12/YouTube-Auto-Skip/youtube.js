(() => {
  "use strict";
  let currentVideoId = "";
  let sponsorSegments = [];
  let lastSponsorSkip = 0;
  const getVideoId = () => new URL(location.href).searchParams.get("v") || "";
  const visible = (element) => {
    const box = element.getBoundingClientRect();
    const style = getComputedStyle(element);
    return box.width > 0 && box.height > 0 && style.visibility !== "hidden" && style.display !== "none";
  };
  function clickSkipButton() {
    for (const selector of [".ytp-skip-ad-button", ".ytp-ad-skip-button-modern", "button.ytp-ad-skip-button", "button[id^='skip-button']"]) {
      const button = document.querySelector(selector);
      if (button && visible(button) && !button.disabled) { button.click(); return; }
    }
  }
  function refreshSegments() {
    const nextId = getVideoId();
    if (!nextId || nextId === currentVideoId) return;
    currentVideoId = nextId;
    sponsorSegments = [];
    chrome.runtime.sendMessage({type: "jarvisSponsorSegments", videoId: nextId}, (response) => {
      if (!chrome.runtime.lastError && currentVideoId === nextId)
        sponsorSegments = Array.isArray(response?.segments) ? response.segments : [];
    });
  }
  function skipSponsor() {
    const video = document.querySelector("video.html5-main-video");
    if (!video || video.paused || !Number.isFinite(video.currentTime)) return;
    const now = performance.now();
    if (now - lastSponsorSkip < 1000) return;
    const match = sponsorSegments.find(([start, end]) => video.currentTime >= start && video.currentTime < end - 0.15);
    if (match) {
      video.currentTime = Math.min(match[1] + 0.05, video.duration || match[1] + 0.05);
      lastSponsorSkip = now;
    }
  }
  setInterval(() => { refreshSegments(); clickSkipButton(); skipSponsor(); }, 500);
})();
