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
        name: "A Simple Trick To Escape Closed Guard and Crush Your Opponent",
        url: "https://www.youtube.com/watch?v=r6mDDpc5474",
        tags: ["#closed-guard", "#escape", "#top-game"]
    }, 
    {
        name: "Danaher: Escape Closed Guard to Ashi Garami",
        url: "https://www.youtube.com/shorts/VKxCRh1jODk",
        tags: ["#closed-guard", "#escape", "#ashi-garami", "#bottom-game"]
    },
    {
        name: "Closed guard escape no-gi",
        noEmbed: true,
        url: "https://www.youtube.com/shorts/JfGU1KFeblY", 
        tags: ["#closed-guard", "#escape", "#bottom-game"]
    },
    {
        name: "Marcelo Garcia on Breaking Closed Guard",
        url: "https://www.youtube.com/watch?v=032wIsVv0hY",
    }, 
    {
        name: "Break Open Anynone's Closed Guard",
        url: "https://www.youtube.com/shorts/Ht43PYmXaNM",
        tags: ["#closed-guard", "#break-open", "#top-game"]
    },
    {
        name: "Closed Guard Escape",
        url: "https://www.youtube.com/shorts/xYW7CCmA3ow",
        tags: ["#closed-guard", "#escape", "#bottom-game"]
    }, 
    {
        name: "Ankle pick take down",
        url: "https://www.youtube.com/shorts/3UV6nzWwm68",
        tags: ["#ankle-pick", "#takedown", "#top-game"]
    },
    {
        name: "Misdirection Single Leg Attack", 
        url: "https://www.youtube.com/shorts/r6WcSrPqLaU",
        tags: ["#single-leg", "#misdirection", "#takedown", "#top-game"]
    },
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
    }, 
    {
        name: "How to never get stuck in Closed Guard Again!",
        url: "https://www.youtube.com/watch?v=d_zfY7Kjezo",
        noEmbed: true,
        tags: ["#closed-guard", "#escape", "#top-game"]
    }, 
    {
        name: "Escaping Closed Guard with Gordon Ryan",
        url: "https://www.youtube.com/watch?v=RDrrWZosCMw",
        tags: ["#closed-guard", "#escape", "#top-game"]
    }, 
    {
        name: "Lachlan: Improve your Log Splitter closed guard openning",
        url: "https://www.youtube.com/shorts/4O0C267NKt0",
        tags: ["#closed-guard", "#escape", "#top-game"]
    }, 
    {
        name: "Elevated Basics: The Ultimate No-Gi Closed Guard Guide", 
        url: "https://www.youtube.com/watch?v=tWUkxvM8ppA", 
        tags: ["#closed-guard", "#no-gi", "#guide", "#bottom-game"]
    },
    {
        name: "The Best Way To Esape Closed Guard",
        url: "https://www.youtube.com/shorts/ztpvgMFYEiw",
        tags: ["#closed-guard", "#escape", "#top-game"]
    }, 
    {
        name: "Close guard hip heist pass",
        url: "https://www.youtube.com/watch?v=6bZ5FBXgSm8",
        tags: ["#closed-guard", "#hip-heist", "#guard-pass", "#top-game"]
    }, 
    {
        name: "No-Gi: Three Best Ways To open/pass closed guard",
        url: "https://www.youtube.com/watch?v=rfaaPWZ-ugY",
        tags: ["#closed-guard", "#guard-pass", "#top-game"]
    }, 
    {
        name: "6 basic but effective guard passes",
        url: "https://www.youtube.com/watch?v=7v_M_ea_7Ik", 
        tags: ["#guard-pass", "#top-game", "#close-guard"]
    }, 
    {
        name: "@officer_grimy: Balacha z bocznej nogami (foto)", 
        url: "https://www.instagram.com/p/DXYb0cUCbEE/embed/",
        tags: ["#side-control", "#balacha", "#armbar", "#top-game"]
    }, 
    {
        name: "@officer_grimy: Balacha z bocznej nogami (wideo)",
        url: "https://www.instagram.com/p/CyjEVJeRceY/embed/",
        tags: ["#side-control", "#balacha", "#armbar", "#top-game"]
    }, 
    {
        name: "@officer_grimy: Balacha z bocznej nogami (wideo 2)",
        url: "https://www.instagram.com/p/CukQ_clJNld/embed/",
        tags: ["#side-control", "#balacha", "#armbar", "#top-game"]
    }, 
    { name: "Guard break to submission",
      url: "https://www.instagram.com/reel/DXCLf-gjpud/embed/",
      tags: ["#guard-break", "#closed-guard", "#submission", "#top-game"]
    }, 
    {
        name: "BJJ Moves: Arm Bar From Guard by John Danaher",
        url: "https://www.youtube.com/watch?v=pQ43Oy5k9yQ", 
        tags: ["#armbar", "#submission", "#john-danaher", "#bottom-game"]
    }, 
    {
        "name": "No Gi Pendulum Sweep and Arm Bar from Closed Guard (Lachlan Giles)",
        url: "https://www.youtube.com/watch?v=58ItAArEM4s", 
        tags: ["#pendulum-sweep", "#armbar", "#closed-guard", "#bottom-game"]
    }, 
    {
        name: "Far armbar from side control (Lachlan Giles)",
        url: "https://www.youtube.com/watch?v=qouu5qFtZZA", 
        tags: ["#armbar", "#side-control", "#top-game"]
    },
    {
        name: "Armbar from mount",
        url: "https://www.youtube.com/watch?v=QwQRDEydJCM",
        tags: ["#armbar", "#mount", "#top-game"]
    },
    {
        name: "The Best Guard For No Gi: Comprehensive Breakdown of the Reverse De La Riva Guard",
        url: "https://www.youtube.com/watch?v=zDl9hklGM-o", 
        tags: ["#reverse-de-la-riva", "#guard", "#no-gi", "#bottom-game"]
    }, 
    {
        name: "Armbar from Closed Guard No-Gi | BJJ for All Levels",
        url: "https://www.youtube.com/watch?v=xcq2Gqn-cVw", 
        tags: ["#armbar", "#closed-guard", "#no-gi", "#bottom-game"]
    }, 
    {
        name: "@tomeralroy: Side Control Escape Rules", 
        url: "https://www.instagram.com/p/DXeWcy7q5_A/embed/",
        tags: ["#side-control", "#escape", "#defense", "#bottom-game"]
    }, 
    {
        name: "Tye Ruotolo’s brilliant armbar from the half guard knee shield",
        url: "https://www.facebook.com/reel/1407326453992218",
        tags: ["#armbar", "#half-guard", "#knee-shield", "#top-game"]
    },
    {
        name: "@luukaaronbjj: Buggy escape",
        url: "https://www.instagram.com/reel/DXelITLjFT2/embed/",
        tags: ["#buggy-escape", "#escape", "#defense", "#bottom-game"]
    }, 
    {   
        name: "5 tips to play guard against bigger opponents",
        url: "https://www.instagram.com/reel/DWoRQX_qA7C/embed/",
        tags: ["#guard", "#tips", "#bigger-opponents", "#bottom-game"]
    }, 
    {
        name: "4 passes from HQ",
        url: "https://www.facebook.com/reel/1522172702920090",
        tags: ["#half-guard", "#guard-pass", "#top-game"]
    }, 
    {
        name: "3 best passes from the split squat",
        url: "https://www.facebook.com/reel/1307997081296257",
        tags: ["#split-squat", "#guard-pass", "#top-game"]
    },
    {
        name: "Sposoby żeby wykończyć balachę na gdy przeciwnik oporuje",
        url: "https://www.instagram.com/reel/DY5saZQtZUl/",
        tags: ["#armbar", "#top-game", "#submissions", "#poddanie", "#balacha"]
    }, 
    {
        name: "This is how to pass with Headquarters",
        url: "https://www.youtube.com/watch?v=3x7Mgxcy3Wo",
        tags: ["#half-guard", "#headquarters", "#guard-pass", "#top-game"]
    }, 
    {
        name: "Pass the Knee Shield with These 3 Strategies",
        url: "https://www.youtube.com/watch?v=i_zvYu5w92g",
        tags: ["#half-guard", "#knee-shield", "#guard-pass", "#top-game"]
    }
  ]
};
