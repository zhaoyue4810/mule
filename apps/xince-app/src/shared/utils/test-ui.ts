export interface TestTheme {
  heroClass: string;
  accentClass: string;
  buttonClass: string;
  emoji: string;
  gradient: string;
  softGradient: string;
  chipGradient: string;
}

export interface InteractionUiMeta {
  icon: string;
  label: string;
  prompt: string;
}

const themeMap: Array<{
  match: (category: string) => boolean;
  theme: TestTheme;
}> = [
  {
    match: (category) => category.includes("性格"),
    theme: {
      heroClass: "bg-purple",
      accentClass: "accent-purple",
      buttonClass: "purple",
      emoji: "🧠",
      gradient: "linear-gradient(160deg,#7C5DBF 0%,#B57FE0 36%,#E8729A 100%)",
      softGradient: "linear-gradient(180deg,rgba(237,229,249,0.96) 0%,rgba(253,230,239,0.84) 100%)",
      chipGradient: "linear-gradient(135deg,rgba(155,126,216,0.18),rgba(201,181,240,0.3))",
    },
  },
  {
    match: (category) => category.includes("情感"),
    theme: {
      heroClass: "bg-pink",
      accentClass: "accent-pink",
      buttonClass: "pink",
      emoji: "💗",
      gradient: "linear-gradient(160deg,#D4548A 0%,#E8729A 38%,#F4A5BF 100%)",
      softGradient: "linear-gradient(180deg,rgba(253,230,239,0.94) 0%,rgba(255,240,232,0.88) 100%)",
      chipGradient: "linear-gradient(135deg,rgba(232,114,154,0.18),rgba(244,165,191,0.32))",
    },
  },
  {
    match: (category) => category.includes("关系"),
    theme: {
      heroClass: "bg-peach",
      accentClass: "accent-peach",
      buttonClass: "pink",
      emoji: "🤝",
      gradient: "linear-gradient(160deg,#D4894D 0%,#F2A68B 45%,#F4A5BF 100%)",
      softGradient: "linear-gradient(180deg,rgba(255,240,232,0.96) 0%,rgba(253,230,239,0.84) 100%)",
      chipGradient: "linear-gradient(135deg,rgba(242,166,139,0.18),rgba(248,201,181,0.34))",
    },
  },
  {
    match: (category) => category.includes("职业"),
    theme: {
      heroClass: "bg-gold",
      accentClass: "accent-gold",
      buttonClass: "gold",
      emoji: "💼",
      gradient: "linear-gradient(160deg,#B8923A 0%,#D4A853 38%,#F2A68B 100%)",
      softGradient: "linear-gradient(180deg,rgba(253,244,222,0.96) 0%,rgba(255,240,232,0.86) 100%)",
      chipGradient: "linear-gradient(135deg,rgba(212,168,83,0.2),rgba(229,201,126,0.35))",
    },
  },
];

const defaultTheme: TestTheme = {
  heroClass: "bg-mint",
  accentClass: "accent-mint",
  buttonClass: "mint",
  emoji: "✨",
  gradient: "linear-gradient(160deg,#4DA68C 0%,#7CC5B2 44%,#A8DDD0 100%)",
  softGradient: "linear-gradient(180deg,rgba(226,245,239,0.96) 0%,rgba(237,229,249,0.82) 100%)",
  chipGradient: "linear-gradient(135deg,rgba(124,197,178,0.18),rgba(168,221,208,0.36))",
};

const interactionMetaMap: Record<string, InteractionUiMeta> = {
  bubble: {
    icon: "🫧",
    label: "气泡选择",
    prompt: "跟着第一直觉点开那个最像你的泡泡。",
  },
  swipe: {
    icon: "↔️",
    label: "滑动判断",
    prompt: "向左或向右拖动，像刷直觉卡片一样给出倾向。",
  },
  slider: {
    icon: "🎚️",
    label: "情绪刻度",
    prompt: "把刻度推到刚刚好的位置，不用追求标准答案。",
  },
  star: {
    icon: "⭐",
    label: "星级评分",
    prompt: "越靠近满星，代表它越像真实的你。",
  },
  versus: {
    icon: "⚡",
    label: "二选一",
    prompt: "别想太久，选那个身体更先有反应的答案。",
  },
  tarot: {
    icon: "🔮",
    label: "塔罗翻牌",
    prompt: "凭直觉翻开一张牌，让潜意识先开口。",
  },
  hotcold: {
    icon: "🌡️",
    label: "灵魂温度",
    prompt: "上下拖动找到你此刻最真实的温度。",
  },
  fortune: {
    icon: "🎡",
    label: "命运轮盘",
    prompt: "先转起来，再在停下的一刻接住答案。",
  },
  rank: {
    icon: "🪜",
    label: "排序拖拽",
    prompt: "把更重要、更像你的放在前面。",
  },
  scratch: {
    icon: "✨",
    label: "刮刮揭晓",
    prompt: "轻轻刮开表层，惊喜会自己浮出来。",
  },
  plot2d: {
    icon: "📍",
    label: "坐标定位",
    prompt: "把自己放进二维坐标里，找到最合适的位置。",
  },
  scenario: {
    icon: "🎭",
    label: "情景代入",
    prompt: "代入那个场景，选你最自然会做的事。",
  },
  colorpick: {
    icon: "🎨",
    label: "色彩感知",
    prompt: "挑一抹最贴近当下心境的颜色。",
  },
  pressure: {
    icon: "⏱️",
    label: "按压测感",
    prompt: "按住节奏，看看你在压力下的直觉反馈。",
  },
  constellation: {
    icon: "🌌",
    label: "星图连线",
    prompt: "点亮那颗最像你当前轨迹的星。",
  },
};

export function resolveTestTheme(category?: string | null): TestTheme {
  const safeCategory = category || "";
  return themeMap.find((item) => item.match(safeCategory))?.theme || defaultTheme;
}

export function resolveInteractionUiMeta(interactionType?: string | null): InteractionUiMeta {
  const key = (interactionType || "").trim().toLowerCase();
  return (
    interactionMetaMap[key] || {
      icon: "✨",
      label: "灵感选择",
      prompt: "按你的第一反应作答就很好。",
    }
  );
}
