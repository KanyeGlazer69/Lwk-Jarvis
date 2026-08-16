const API = "https://sponsor.ajay.app/api/skipSegments/";

async function hashPrefix(videoId) {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(videoId));
  return Array.from(new Uint8Array(digest))
    .map((value) => value.toString(16).padStart(2, "0"))
    .join("").slice(0, 4);
}

chrome.runtime.onMessage.addListener((message, _sender, reply) => {
  if (message?.type !== "jarvisSponsorSegments" || !message.videoId) return false;
  (async () => {
    try {
      const query = new URLSearchParams();
      query.append("category", "sponsor");
      query.append("category", "selfpromo");
      query.append("actionType", "skip");
      const response = await fetch(API + await hashPrefix(message.videoId) + "?" + query, {cache: "no-store"});
      if (response.status === 404) return reply({segments: []});
      if (!response.ok) throw new Error(`SponsorBlock returned ${response.status}`);
      const matches = await response.json();
      const video = matches.find((entry) => entry.videoID === message.videoId);
      const segments = (video?.segments || []).map((entry) => entry.segment)
        .filter((segment) => Array.isArray(segment) && segment.length === 2);
      reply({segments});
    } catch (error) {
      reply({segments: [], error: String(error)});
    }
  })();
  return true;
});
