// ─────────────────────────────────────────────────────────────────
// BJJ NO-GI · Technique Of The Day — Configuration
// ─────────────────────────────────────────────────────────────────
//
// Each technique entry:
//   name  – short label, max 15 words
//   url   – video URL (any format, auto-converted to embed):
//             YouTube   → https://www.youtube.com/watch?v=ID  or  https://youtu.be/ID  or  /embed/ID
//             Vimeo     → https://player.vimeo.com/video/VIDEO_ID
//             Instagram → https://www.instagram.com/reel/CODE/embed/
//             Facebook  → https://www.facebook.com/reel/ID  (opens in new tab, no embed)
//   tags  – array of hashtag strings (use kebab-case)
//
// A random technique is picked on every page load.
// ─────────────────────────────────────────────────────────────────

window.TOD_CONFIG = {
  techniques: [

    {
      name: "@kuzure.co: Arm Triangle Threat To Kimura Trap",
      url:  "https://www.instagram.com/reel/DXIAkv5jPaW/embed/",
      tags: ["#arm-triangle", "#kimura", "#side-control", "#top-game"]
    },

    {
      name: "@presleybjj: 3 escapes from Turtle Position",
      url:  "https://www.instagram.com/p/DXHgdCzgE1x/embed/",
      tags: ["#turtle", "#escapes", "#defense", "#bottom-game"]
    }, 
    {
        name: "Two Handed Guard Pass",
        url: "https://www.instagram.com/reel/DW6fvitDNIK/embed/",
        tags: ["#guard-pass", "#two-handed", "#top-game"]
    },
    {
        name: "Renato Subotic: Triangle The Legs",
        url: "https://www.facebook.com/reel/2022685118662629",
        tags: ["#guard-pass", "#top-game", "#top-control"]
    },
    {
        name: "Getting To Half Guard From Split Squat",
        url: "https://www.instagram.com/reel/DXDshh3DYwe/embed/",
        tags: ["#half-guard", "#split-squat", "#top-game", "#guard-pass"]
    },
    {
        name: "Iwat BJJ: Jak użyć folding passa w HQ",  
        url: "https://www.facebook.com/reel/1709868740030349/embed/",
        tags: ["#guard-pass", "#folding-pass", "#top-game"]
    },
    {
        name: "@declan_moody: Back step against the inversio",
        url: "https://www.instagram.com/reel/DXAUgW5E8-z/embed/",
        tags: ["#south-north", "#back-step", "#guard-pass", "#top-game"]
    }, 
    {
        name: "Submission from failed americana",
        url: "https://www.instagram.com/reel/DT8BVfrkmBy/embed/",
        tags: ["#submission", "#americana", "#failed-attempt", "#bottom-game"]
    }, 
    {
        name: "How To Do The Perfect Armbar by John Danaher",
        url: "https://www.youtube.com/watch?v=GshEzcqlUbY",
        tags: ["#armbar", "#submission", "#john-danaher", "#bottom-game"]
    }, 
    {
        name: "A Sneaky Armbar that Everyone Should Know", 
        url: "https://youtu.be/yPHEGRnRem0?si=5zPxep8zwF4oEUMH",
        tags: ["#armbar", "#submission", "#sneaky", "#bottom-game"]
    }
  ]
};
