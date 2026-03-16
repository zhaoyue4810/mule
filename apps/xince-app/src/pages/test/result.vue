<script setup lang="ts">
import { computed, getCurrentInstance, onBeforeUnmount, ref } from "vue";
import { onLoad, onUnload } from "@dcloudio/uni-app";

import XiaoCe from "@/components/mascot/XiaoCe.vue";
import XcBubble from "@/components/mascot/XcBubble.vue";
import PersonaRadarCanvas from "@/components/profile/PersonaRadarCanvas.vue";
import ReportDeepAnalysis from "@/components/report/ReportDeepAnalysis.vue";
import ReportHeroPanels from "@/components/report/ReportHeroPanels.vue";
import type { MemorySuggestPayload } from "@/shared/models/memory";
import type { AppReportDetail, ReportDNAItem, ReportRadarDimension } from "@/shared/models/reports";
import { createTimeCapsule } from "@/shared/services/capsule";
import { fetchMemorySuggest } from "@/shared/services/memory";
import {
  fetchReportAiStatus,
  fetchReportDetail,
  retryReportAi,
} from "@/shared/services/reports";
import { SoundManager } from "@/shared/utils/sound-manager";

type DeepPanelKey = "strength" | "growth" | "advice" | "social";

const report = ref<AppReportDetail | null>(null);
const loading = ref(true);
const error = ref("");
const aiRefreshing = ref(false);
const capsuleMessage = ref("");
const capsuleDuration = ref(30);
const capsuleSaving = ref(false);
const capsuleCreated = ref(false);
const suggestPayload = ref<MemorySuggestPayload | null>(null);
const countdown = ref(7265);
const activeDeepPanel = ref<DeepPanelKey | null>("strength");
const activeMetaphorIndex = ref<number | null>(0);
const percentileValues = ref([0, 0, 0, 0]);
const percentileAnimated = ref(false);
const dnaVisible = ref(false);
const hiddenUnlocked = ref(false);
const hiddenUnlockAnimating = ref(false);
let currentRecordId = 0;
let pollTimer: ReturnType<typeof setInterval> | null = null;
let countdownTimer: ReturnType<typeof setInterval> | null = null;
let percentileTimers: ReturnType<typeof setInterval>[] = [];
let aiObserver: UniApp.IntersectionObserver | null = null;
let dnaObserver: UniApp.IntersectionObserver | null = null;
let hiddenObserver: UniApp.IntersectionObserver | null = null;

const instance = getCurrentInstance();

const heroStyle = computed(() => {
  const fallback =
    "linear-gradient(135deg, rgba(155,126,216,0.95), rgba(232,114,154,0.85), rgba(242,166,139,0.92))";
  return {
    background: report.value?.share_card?.background || fallback,
  };
});

const personaName = computed(() => report.value?.persona.persona_name || "灵魂旅人");
const titleText = computed(() => `你当前最接近 ${personaName.value}`);
const tierText = computed(() => report.value?.result_tier || "稀有人格");
const totalScore = computed(() => Math.max(0, Math.round(report.value?.total_score || 0)));
const scoreProgress = computed(() => Math.max(0, Math.min(100, totalScore.value)));

const personaEmoji = computed(() => {
  const hint = `${report.value?.persona.persona_name || ""}${report.value?.persona.persona_key || ""}`.toLowerCase();
  if (hint.includes("光") || hint.includes("sun")) {
    return "☀️";
  }
  if (hint.includes("月") || hint.includes("moon")) {
    return "🌙";
  }
  if (hint.includes("星") || hint.includes("star")) {
    return "🌟";
  }
  if (hint.includes("海") || hint.includes("water")) {
    return "🌊";
  }
  if (hint.includes("猫")) {
    return "🐱";
  }
  return "✨";
});

const topThreeDimensions = computed(() =>
  (report.value?.radar_dimensions || [])
    .slice()
    .sort((a, b) => b.score - a.score)
    .slice(0, 3),
);

const quoteText = computed(
  () =>
    report.value?.persona.description ||
    report.value?.summary ||
    "你正在成为更真实、更稳定、更自由的自己。",
);

const personaKeywords = computed(() => {
  const source = [
    ...(report.value?.persona.keywords || []),
    ...(report.value?.persona_tags || []).map((item) => item.label),
    ...topThreeDimensions.value.map((item) => item.label),
  ];
  return Array.from(new Set(source.filter(Boolean))).slice(0, 4);
});

const heroStatChips = computed(() => {
  const source = report.value?.share_card?.stat_chips?.filter(Boolean) || [];
  if (source.length) {
    return source.slice(0, 3);
  }
  return [
    tierText.value,
    `${topThreeDimensions.value[0]?.label || "平衡"}突出`,
    `${totalScore.value} 分`,
  ];
});

const heroHighlightLines = computed(() => {
  const source = report.value?.share_card?.highlight_lines?.filter(Boolean) || [];
  if (source.length) {
    return source.slice(0, 2);
  }
  return [
    report.value?.summary || "",
    report.value?.action_guides?.[0]?.description || "",
  ].filter(Boolean);
});

const heroFooterText = computed(
  () => report.value?.share_card?.footer || `长按保存分享给好友 · ${report.value?.test_name || "心测"}`,
);

const rarityText = computed(() => {
  const percentile = Math.max(28, Math.min(98, scoreProgress.value + 6));
  return `超越 ${percentile}% 同类用户`;
});

const mascotComment = computed(() => {
  const hint = `${report.value?.persona.persona_name || ""}${report.value?.persona.persona_key || ""}`.toLowerCase();
  if (hint.includes("行动") || hint.includes("fire")) {
    return "你有很强的执行力，保持这个火花，会走得很远。";
  }
  if (hint.includes("理性") || hint.includes("think")) {
    return "你的洞察非常细腻，很多人会因为你的判断更安心。";
  }
  if (hint.includes("感性") || hint.includes("heart")) {
    return "你的共情力很珍贵，它会让关系变得柔软又有力量。";
  }
  return "这份报告很有你自己的味道，小测超喜欢。";
});

const guidePreview = computed(() => (report.value?.action_guides || []).slice(0, 3));

const metaphorCards = computed(() => {
  if (report.value?.metaphor_cards?.length) {
    return report.value.metaphor_cards.slice(0, 3);
  }
  const top = topThreeDimensions.value[0];
  const dim = top?.label || "平衡";
  return [
    { category: "建筑", title: `${dim}灯塔`, subtitle: "坚定且温柔地照亮前路", emoji: "🏛️" },
    { category: "动物", title: `${dim}灵兽`, subtitle: "敏锐但不张扬，节奏稳定", emoji: "🦊" },
    { category: "星球", title: `${dim}轨道`, subtitle: "你在自己的秩序里持续发光", emoji: "🪐" },
  ];
});

const percentileTargets = computed(() => {
  const base = scoreProgress.value;
  const focus = Math.round((topThreeDimensions.value[0]?.normalized_score || 0.75) * 100);
  return [
    Math.max(35, Math.min(99, base + 8)),
    Math.max(30, Math.min(99, focus + 6)),
    Math.max(28, Math.min(99, Math.round(base * 0.84 + 12))),
    Math.max(25, Math.min(99, Math.round(base * 0.78 + 18))),
  ];
});

const percentileItems = computed(() => [
  { label: "情绪稳定度", desc: "超越同类测试者", value: percentileValues.value[0] || 0 },
  { label: "洞察清晰度", desc: "在维度判断上领先", value: percentileValues.value[1] || 0 },
  { label: "关系适配度", desc: "在人际感知中表现", value: percentileValues.value[2] || 0 },
  { label: "成长潜力值", desc: "未来三个月成长预期", value: percentileValues.value[3] || 0 },
]);

const radarCanvasDimensions = computed(() =>
  (report.value?.radar_dimensions || []).slice(0, 5).map((item) => ({
    dim_code: item.dim_code,
    label: item.label,
    score:
      item.normalized_score <= 1
        ? Math.round(item.normalized_score * 100)
        : Math.round(Math.max(0, Math.min(100, item.score))),
  })),
);

const maxRadarScore = computed(() => {
  const source = report.value?.radar_dimensions || [];
  const max = Math.max(...source.map((item) => item.score), 1);
  return max || 1;
});

function dimensionBarWidth(item: ReportRadarDimension) {
  return `${Math.round((item.score / maxRadarScore.value) * 100)}%`;
}

function dnaGradient(index: number) {
  const gradients = [
    "linear-gradient(90deg, #9B7ED8, #C9B5F0)",
    "linear-gradient(90deg, #E8729A, #F4A5BF)",
    "linear-gradient(90deg, #7CC5B2, #A8DDD0)",
    "linear-gradient(90deg, #D4A853, #E5C97E)",
    "linear-gradient(90deg, #F2A68B, #F8C9B5)",
  ];
  return gradients[index % gradients.length];
}

function dnaWidth(item: ReportDNAItem) {
  if (!dnaVisible.value) {
    return "0%";
  }
  return `${Math.max(0, Math.min(100, item.percentage))}%`;
}

const soulWeather = computed(() => {
  const score = totalScore.value;
  if (score >= 85) {
    return {
      emoji: "☀️",
      title: "晴天",
      temp: "26°C",
      tags: ["适合社交", "适合挑战", "适合表达"],
    };
  }
  if (score >= 75) {
    return {
      emoji: "🌤️",
      title: "多云转晴",
      temp: "22°C",
      tags: ["适合规划", "适合复盘", "适合运动"],
    };
  }
  if (score >= 65) {
    return {
      emoji: "🍃",
      title: "微风",
      temp: "20°C",
      tags: ["适合散步", "适合倾听", "适合慢节奏"],
    };
  }
  return {
    emoji: "🌈",
    title: "雨后彩虹",
    temp: "18°C",
    tags: ["适合休息", "适合整理", "适合重新出发"],
  };
});

const weakestDimension = computed(() => {
  const dims = report.value?.radar_dimensions || [];
  if (!dims.length) {
    return null;
  }
  return dims.slice().sort((a, b) => a.score - b.score)[0];
});

const hiddenPersonaText = computed(() => {
  const weakest = weakestDimension.value?.label || "柔软";
  return `在${weakest}这一面，你其实比自己以为的更敏感。它不是短板，而是你感知世界的备用翅膀。`;
});

const weatherMoodText = computed(
  () => report.value?.soul_weather.mood || `${soulWeather.value.title}的一天`,
);

const weatherGoodTags = computed(() => soulWeather.value.tags.slice(0, 2));

const weatherCautionTags = computed(() => {
  const source = [
    report.value?.soul_weather.mood,
    weakestDimension.value ? `留意${weakestDimension.value.label}` : "",
    report.value?.action_guides?.[0]?.title,
  ];
  return Array.from(new Set(source.filter(Boolean) as string[])).slice(0, 2);
});

const dnaIntro = computed(() => {
  const pair = topThreeDimensions.value
    .slice(0, 2)
    .map((item) => item.label)
    .join(" + ");
  return `${personaName.value} 的人格组成更偏向 ${pair || "稳定 + 觉察"}。`;
});

const aiSections = computed(() => {
  const ai = (report.value?.ai_text || "").trim();
  const lines = ai
    ? ai
        .split(/\n+/)
        .map((item) => item.trim())
        .filter(Boolean)
    : [];
  const fallback = [
    report.value?.summary || "你具备稳定自驱和向内观察的能力。",
    report.value?.action_guides?.[0]?.description || "建议把精力放在高价值关系和长期目标。",
    report.value?.action_guides?.[1]?.description || "给自己预留恢复时间，稳定节奏更容易进步。",
    report.value?.action_guides?.[2]?.description || "主动表达需求，会让关系更平衡。",
  ];
  return [
    { key: "strength" as const, title: "优势特质", text: lines[0] || fallback[0] },
    { key: "growth" as const, title: "成长空间", text: lines[1] || fallback[1] },
    { key: "advice" as const, title: "实用建议", text: lines[2] || fallback[2] },
    { key: "social" as const, title: "人际关系", text: lines[3] || fallback[3] },
  ];
});

const reportSummary = computed(() => report.value?.summary || quoteText.value);

const quoteAttr = computed(
  () => `—— 你的灵魂说明书 · ${report.value?.test_name || "心测"}`,
);

const capsulePrompt = computed(
  () => `如果未来的你再读到「${personaName.value}」这一刻，会想对今天说什么？`,
);

const futureLetter = computed(
  () =>
    `亲爱的现在的我：\n\n谢谢你在这个阶段认真地认识自己。你并不需要马上成为完美的人，只要继续保持 ${personaName.value} 的勇气和温柔，未来会自然展开。\n\n愿你在下次打开胶囊时，依旧记得今天的初心。`,
);

const limitedBannerTitle = computed(
  () => `限时挑战 · ${report.value?.test_name || "灵魂进阶版"}`,
);

const nextTest = computed(() => suggestPayload.value?.items?.[0] || null);

const aiPending = computed(
  () => report.value?.ai_status === "PENDING" || report.value?.ai_status === "RUNNING",
);

const countdownText = computed(() => {
  const safe = Math.max(0, countdown.value);
  const hour = `${Math.floor(safe / 3600)}`.padStart(2, "0");
  const minute = `${Math.floor((safe % 3600) / 60)}`.padStart(2, "0");
  const second = `${safe % 60}`.padStart(2, "0");
  return `${hour}:${minute}:${second}`;
});

function resolveNextTestEmoji(category?: string) {
  const hint = (category || "").toLowerCase();
  if (hint.includes("关系")) {
    return "💞";
  }
  if (hint.includes("职业")) {
    return "🚀";
  }
  if (hint.includes("性格")) {
    return "🪞";
  }
  return "✨";
}

function backHome() {
  uni.switchTab({
    url: "/pages/home/index",
  });
}

function goProfile() {
  uni.switchTab({
    url: "/pages/profile/index",
  });
}

function goMatch() {
  uni.switchTab({
    url: "/pages/match/index",
  });
}

function openSharePoster(mode: "report" | "challenge" = "report") {
  if (!currentRecordId) {
    return;
  }
  uni.navigateTo({
    url: `/pages/test/share-poster?recordId=${currentRecordId}&mode=${mode}`,
  });
}

function openDetail(testCode?: string) {
  if (!testCode) {
    return;
  }
  uni.navigateTo({
    url: `/pages/test/detail?testCode=${testCode}`,
  });
}

function openNextTest() {
  openDetail(nextTest.value?.test_code);
}

function toggleMetaphor(index: number) {
  activeMetaphorIndex.value = activeMetaphorIndex.value === index ? null : index;
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function stopCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
}

function stopPercentileTimers() {
  percentileTimers.forEach((timer) => clearInterval(timer));
  percentileTimers = [];
}

function triggerPercentileAnimation() {
  if (percentileAnimated.value) {
    return;
  }
  percentileAnimated.value = true;
  stopPercentileTimers();
  percentileValues.value = [0, 0, 0, 0];
  percentileTargets.value.forEach((target, index) => {
    const tick = setInterval(() => {
      const now = percentileValues.value[index] || 0;
      const next = Math.min(target, now + Math.max(1, Math.ceil((target - now) / 10)));
      percentileValues.value = percentileValues.value.map((item, itemIndex) =>
        itemIndex === index ? next : item,
      );
      if (next >= target) {
        clearInterval(tick);
      }
    }, 28 + index * 6);
    percentileTimers.push(tick);
  });
}

function initObservers() {
  const vm = instance?.proxy;
  if (!vm) {
    return;
  }
  aiObserver?.disconnect();
  dnaObserver?.disconnect();
  hiddenObserver?.disconnect();

  aiObserver = uni.createIntersectionObserver(vm, { observeAll: false });
  aiObserver.relativeToViewport({ bottom: 0 }).observe(".js-percentile", (res) => {
    if (res.intersectionRatio > 0.2) {
      triggerPercentileAnimation();
    }
  });

  dnaObserver = uni.createIntersectionObserver(vm, { observeAll: false });
  dnaObserver.relativeToViewport({ bottom: 0 }).observe(".js-dna", (res) => {
    if (res.intersectionRatio > 0.2) {
      dnaVisible.value = true;
    }
  });

  hiddenObserver = uni.createIntersectionObserver(vm, { observeAll: false });
  hiddenObserver.relativeToViewport({ bottom: 0 }).observe(".js-hidden-persona", (res) => {
    if (res.intersectionRatio > 0.6 && !hiddenUnlocked.value) {
      hiddenUnlockAnimating.value = true;
      SoundManager.play("whoosh");
      SoundManager.haptic(35);
      setTimeout(() => {
        hiddenUnlocked.value = true;
        hiddenUnlockAnimating.value = false;
      }, 650);
    }
  });
}

function disposeObservers() {
  aiObserver?.disconnect();
  dnaObserver?.disconnect();
  hiddenObserver?.disconnect();
  aiObserver = null;
  dnaObserver = null;
  hiddenObserver = null;
}

function startCountdown() {
  stopCountdown();
  countdownTimer = setInterval(() => {
    countdown.value = Math.max(0, countdown.value - 1);
  }, 1000);
}

async function createCapsule() {
  if (!report.value || capsuleSaving.value || capsuleCreated.value) {
    return;
  }
  if (!capsuleMessage.value.trim()) {
    uni.showToast({
      title: "先写下一句话吧",
      icon: "none",
    });
    return;
  }
  capsuleSaving.value = true;
  try {
    await createTimeCapsule({
      message: capsuleMessage.value.trim(),
      duration_days: capsuleDuration.value,
      report_id: report.value.report_id,
    });
    capsuleMessage.value = "";
    capsuleCreated.value = true;
    SoundManager.play("chime");
    SoundManager.haptic(50);
    uni.showToast({
      title: "时光胶囊已封存",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "封存失败",
      icon: "none",
    });
  } finally {
    capsuleSaving.value = false;
  }
}

async function refreshAiStatus() {
  if (!currentRecordId || !report.value) {
    return;
  }
  try {
    aiRefreshing.value = true;
    const statusPayload = await fetchReportAiStatus(currentRecordId);
    report.value = {
      ...report.value,
      ai_status: statusPayload.status,
      ai_text: statusPayload.content || report.value.ai_text,
    };
    if (statusPayload.status === "COMPLETED" || statusPayload.status === "FAILED") {
      stopPolling();
    }
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "AI 状态刷新失败",
      icon: "none",
    });
    stopPolling();
  } finally {
    aiRefreshing.value = false;
  }
}

function startPolling() {
  stopPolling();
  pollTimer = setInterval(() => {
    refreshAiStatus();
  }, 2500);
}

async function handleRetryAi() {
  if (!currentRecordId || aiRefreshing.value) {
    return;
  }
  try {
    aiRefreshing.value = true;
    const statusPayload = await retryReportAi(currentRecordId);
    if (report.value) {
      report.value = {
        ...report.value,
        ai_status: statusPayload.status,
        ai_text: statusPayload.content || null,
      };
    }
    if (statusPayload.status !== "COMPLETED") {
      startPolling();
    }
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "重试失败",
      icon: "none",
    });
  } finally {
    aiRefreshing.value = false;
  }
}

function toggleDeepPanel(key: DeepPanelKey) {
  activeDeepPanel.value = activeDeepPanel.value === key ? null : key;
}

async function loadReport(recordId: number) {
  loading.value = true;
  error.value = "";
  percentileAnimated.value = false;
  percentileValues.value = [0, 0, 0, 0];
  dnaVisible.value = false;
  hiddenUnlocked.value = false;
  hiddenUnlockAnimating.value = false;
  activeDeepPanel.value = "strength";
  activeMetaphorIndex.value = 0;
  capsuleCreated.value = false;
  capsuleMessage.value = "";

  try {
    const [reportPayload, suggest] = await Promise.all([
      fetchReportDetail(recordId),
      fetchMemorySuggest().catch(() => null),
    ]);
    report.value = reportPayload;
    suggestPayload.value = suggest;
    if (report.value.ai_status === "PENDING" || report.value.ai_status === "RUNNING") {
      startPolling();
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : "报告加载失败";
  } finally {
    loading.value = false;
    setTimeout(() => {
      initObservers();
    }, 120);
  }
}

onLoad((query) => {
  const recordId =
    query && typeof query.recordId === "string" ? Number(query.recordId) : 0;
  if (!recordId) {
    error.value = "缺少 recordId 参数";
    loading.value = false;
    return;
  }
  currentRecordId = recordId;
  startCountdown();
  loadReport(recordId);
});

onBeforeUnmount(() => {
  stopPolling();
  stopCountdown();
  stopPercentileTimers();
  disposeObservers();
});

onUnload(() => {
  stopPolling();
  stopCountdown();
  stopPercentileTimers();
  disposeObservers();
});
</script>

<template>
  <scroll-view class="page" scroll-y>
    <view class="page-bg">
      <view class="page-glow page-glow--one" />
      <view class="page-glow page-glow--two" />
      <view class="page-glow page-glow--three" />
    </view>

    <view v-if="loading" class="state-panel">
      <text class="state-panel__text">正在生成你的灵魂说明书...</text>
    </view>

    <view v-else-if="error" class="state-panel state-panel--error">
      <text class="state-panel__text">{{ error }}</text>
    </view>

    <view v-else-if="report" class="report xc-enter">
      <ReportHeroPanels
        :hero-style="heroStyle"
        :test-name="report.test_name"
        :title-text="titleText"
        :persona-emoji="personaEmoji"
        :persona-name="personaName"
        :tier-text="tierText"
        :total-score="totalScore"
        :score-progress="scoreProgress"
        :rarity-text="rarityText"
        :top-three-dimensions="topThreeDimensions"
        :quote-text="quoteText"
        :keywords="personaKeywords"
        :stat-chips="heroStatChips"
        :highlight-lines="heroHighlightLines"
        :footer-text="heroFooterText"
        @share="openSharePoster('report')"
      />

      <view class="report-callout d3 xc-enter xc-enter--1">
        <view class="report-callout__bubble">
          <XcBubble :text="mascotComment" :typing="true" :persistent="true" />
        </view>
        <view class="report-callout__aside">
          <view class="report-callout__mascot">
            <XiaoCe expression="happy" size="md" :animated="true" />
          </view>
          <view class="report-callout__chips">
            <text
              v-for="item in guidePreview"
              :key="item.title"
              class="report-callout__chip"
            >
              {{ item.title }}
            </text>
          </view>
        </view>
      </view>

      <view class="panel panel--metaphor d4 xc-card-lift xc-enter xc-enter--2">
        <view class="section-head">
          <view>
            <text class="section-eyebrow">Soul Metaphor</text>
            <text class="section-title">灵魂隐喻</text>
          </view>
        </view>
        <text class="section-subtitle">如果把你的灵魂具象化，它会更像哪一种存在？</text>

        <view class="metaphors">
          <view
            v-for="(item, index) in metaphorCards"
            :key="`${item.category}-${item.title}`"
            class="metaphor-card"
            :class="{ 'metaphor-card--open': activeMetaphorIndex === index }"
            @tap="toggleMetaphor(index)"
          >
            <text class="metaphor-card__watermark">心测 · 灵魂说明书</text>
            <text class="metaphor-card__emoji">{{ item.emoji }}</text>
            <text class="metaphor-card__category">{{ item.category }}</text>
            <text class="metaphor-card__title">{{ item.title }}</text>
            <text class="metaphor-card__body">{{ item.subtitle }}</text>
            <text class="metaphor-card__toggle">
              {{ activeMetaphorIndex === index ? "轻点收起" : "展开看看" }}
            </text>
          </view>
        </view>
      </view>

      <view class="panel panel--percentile js-percentile d5 xc-card-lift xc-enter xc-enter--2">
        <view class="section-head">
          <view>
            <text class="section-eyebrow">Percentile</text>
            <text class="section-title">人群百分位</text>
          </view>
          <text class="section-badge">Top Insights</text>
        </view>
        <text class="section-subtitle">你的一些维度，已经明显走到了人群前面。</text>

        <view class="percentile-grid">
          <view v-for="item in percentileItems" :key="item.label" class="percentile-card">
            <view
              class="percentile-ring"
              :style="{ background: `conic-gradient(#9B7ED8 ${item.value * 3.6}deg, rgba(155,126,216,0.14) 0)` }"
            >
              <view class="percentile-ring__inner">
                <text class="percentile-ring__value">{{ item.value }}%</text>
              </view>
            </view>
            <text class="percentile-card__title">{{ item.label }}</text>
            <text class="percentile-card__desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>

      <view class="panel panel--dimension xc-card-lift xc-enter xc-enter--3">
        <view class="section-head">
          <view>
            <text class="section-eyebrow">Dimension Story</text>
            <text class="section-title">维度分析</text>
          </view>
        </view>
        <text class="section-subtitle">
          以 {{ topThreeDimensions[0]?.label || "平衡感" }} 为主轴，你的画像已经很清晰了。
        </text>

        <view class="dimension-analysis">
          <view class="dimension-analysis__radar">
            <PersonaRadarCanvas :dimensions="radarCanvasDimensions" />
          </view>

          <view class="dimension-analysis__bars">
            <view
              v-for="(item, index) in report.radar_dimensions"
              :key="item.dim_code"
              class="dimension-bar"
            >
              <view class="dimension-bar__head">
                <view class="dimension-bar__name-wrap">
                  <text class="dimension-bar__index">{{ index + 1 }}</text>
                  <text class="dimension-bar__name">{{ item.label }}</text>
                </view>
                <text class="dimension-bar__score">{{ item.score.toFixed(1) }}</text>
              </view>
              <view class="dimension-bar__track">
                <view
                  class="dimension-bar__fill"
                  :style="{ width: dimensionBarWidth(item), background: dnaGradient(index) }"
                />
              </view>
            </view>
          </view>
        </view>
      </view>

      <view class="panel weather xc-card-lift xc-enter xc-enter--3">
        <view class="section-head section-head--light">
          <view>
            <text class="section-eyebrow section-eyebrow--light">Soul Weather</text>
            <text class="section-title section-title--light">灵魂天气</text>
          </view>
          <text class="weather__mood">{{ weatherMoodText }}</text>
        </view>

        <view class="weather__head">
          <view class="weather__symbol">
            <text class="weather__emoji">{{ soulWeather.emoji }}</text>
          </view>
          <view class="weather__info">
            <text class="weather__title">{{ soulWeather.title }}</text>
            <text class="weather__temp">{{ soulWeather.temp }}</text>
            <text class="weather__status">{{ report.soul_weather.title }}</text>
          </view>
        </view>

        <text class="weather__desc">{{ report.soul_weather.description }}</text>

        <view class="weather__tags">
          <text
            v-for="tag in weatherGoodTags"
            :key="`good-${tag}`"
            class="weather__tag weather__tag--good"
          >
            {{ tag }}
          </text>
          <text
            v-for="tag in weatherCautionTags"
            :key="`caution-${tag}`"
            class="weather__tag weather__tag--caution"
          >
            {{ tag }}
          </text>
        </view>
      </view>

      <view class="panel panel--dna js-dna xc-card-lift xc-enter xc-enter--4">
        <view class="section-head">
          <view>
            <text class="section-eyebrow">DNA Map</text>
            <text class="section-title">人格 DNA 图谱</text>
          </view>
        </view>
        <text class="section-subtitle">{{ dnaIntro }}</text>

        <view class="dna-list">
          <view v-for="(item, index) in report.dna_segments" :key="item.dim_code" class="dna-item">
            <view class="dna-item__row">
              <view class="dna-item__label-wrap">
                <view class="dna-item__dot" :style="{ background: dnaGradient(index) }" />
                <text class="dna-item__label">{{ item.label }}</text>
              </view>
              <text class="dna-item__value">{{ item.percentage }}%</text>
            </view>
            <view class="dna-item__track">
              <view
                class="dna-item__fill"
                :style="{ width: dnaWidth(item), background: dnaGradient(index), transitionDelay: `${index * 70}ms` }"
              />
            </view>
          </view>
        </view>
      </view>

      <view
        class="panel hidden-persona js-hidden-persona xc-card-lift xc-enter xc-enter--4"
        :class="{ 'hidden-persona--unlocked': hiddenUnlocked }"
      >
        <view class="section-head section-head--light">
          <view>
            <text class="section-eyebrow section-eyebrow--light">Hidden Layer</text>
            <text class="section-title section-title--light">隐藏人格</text>
          </view>
        </view>

        <view v-if="!hiddenUnlocked" class="hidden-lock" :class="{ 'hidden-lock--shake': hiddenUnlockAnimating }">
          <text class="hidden-lock__icon">🔒</text>
          <text class="hidden-lock__hint">继续下滑解锁隐藏人格</text>
          <view class="hidden-lock__line" />
        </view>

        <view v-else class="hidden-unlocked">
          <text class="hidden-unlocked__emoji">{{ personaEmoji }}</text>
          <text class="hidden-unlocked__title">
            其实你骨子里也很 {{ weakestDimension?.label || "敏感" }}
          </text>
          <text class="hidden-unlocked__body">{{ hiddenPersonaText }}</text>
        </view>
      </view>

      <ReportDeepAnalysis
        :pending="aiPending"
        :ai-refreshing="aiRefreshing"
        :ai-status="report.ai_status"
        :summary="reportSummary"
        :sections="aiSections"
        :active-key="activeDeepPanel"
        @toggle="toggleDeepPanel"
        @retry="handleRetryAi"
      />

      <view class="quote-card xc-enter xc-enter--5">
        <text class="quote-card__mark">“</text>
        <text class="quote-card__text">{{ quoteText }}</text>
        <text class="quote-card__attr">{{ quoteAttr }}</text>
      </view>

      <view class="capsule-letter xc-enter xc-enter--5">
        <text class="capsule-letter__stamp">💌</text>
        <text class="capsule-letter__dear">来自未来的你</text>
        <text class="capsule-letter__text">{{ futureLetter }}</text>
        <text class="capsule-letter__sign">等下次拆封时，你会看见今天的勇气。</text>
      </view>

      <view class="panel panel--capsule-input xc-card-lift xc-enter xc-enter--5">
        <view class="section-head">
          <view>
            <text class="section-eyebrow">Time Capsule</text>
            <text class="section-title">写入时间胶囊</text>
          </view>
        </view>

        <view v-if="capsuleCreated" class="capsule-success">
          <text class="capsule-success__icon">✨</text>
          <text class="capsule-success__text">已成功封存，未来的你会收到这份答案。</text>
        </view>

        <template v-else>
          <text class="section-subtitle">{{ capsulePrompt }}</text>
          <textarea
            v-model="capsuleMessage"
            class="capsule-input"
            maxlength="1000"
            placeholder="写下此刻的心情、想记住的答案，或者一句想留给未来的提醒。"
          />

          <view class="capsule-durations">
            <button
              v-for="value in [30, 90, 365]"
              :key="value"
              class="capsule-duration"
              :class="{ 'capsule-duration--active': capsuleDuration === value }"
              @tap="capsuleDuration = value"
            >
              {{ value }} 天
            </button>
          </view>

          <button class="button button--primary" :loading="capsuleSaving" @tap="createCapsule">
            {{ capsuleSaving ? "封存中..." : "封存到时光胶囊" }}
          </button>
        </template>
      </view>

      <view class="limited-banner xc-card-lift xc-enter xc-enter--5">
        <view class="limited-banner__shine" />
        <text class="limited-banner__title">{{ limitedBannerTitle }}</text>
        <text class="limited-banner__desc">倒计时 {{ countdownText }} 后结束，快邀请好友一起测。</text>
      </view>

      <view class="actions xc-enter xc-enter--5">
        <button class="button button--primary xc-card-lift" @tap="openSharePoster('report')">分享报告</button>
        <button class="button button--glass xc-card-lift" @tap="openSharePoster('challenge')">好友挑战</button>
        <button class="button button--glass" @tap="goMatch">灵魂匹配</button>
      </view>

      <view class="panel next-test">
        <view class="section-head">
          <view>
            <text class="section-eyebrow">Next Test</text>
            <text class="section-title">推荐下一个测试</text>
          </view>
        </view>

        <view v-if="nextTest" class="next-test__card" @tap="openNextTest">
          <view class="next-test__icon">
            <text>{{ resolveNextTestEmoji(nextTest.category) }}</text>
          </view>
          <view class="next-test__body">
            <text class="next-test__name">{{ nextTest.name }}</text>
            <text class="next-test__meta">
              {{ nextTest.category }} · {{ nextTest.question_count }} 题 · {{ nextTest.duration_hint || "约 5 分钟" }}
            </text>
          </view>
          <text class="next-test__cta">去测试 ›</text>
        </view>
        <text v-else class="section-subtitle">去首页看看今天为你准备的热门测试。</text>
      </view>

      <view class="bottom-actions">
        <button class="button button--soft" @tap="goProfile">查看我的画像</button>
        <button class="button button--soft" @tap="backHome">返回首页</button>
      </view>
    </view>
  </scroll-view>
</template>

<style lang="scss" scoped>
.page {
  position: relative;
  min-height: 100vh;
  height: 100vh;
  background:
    linear-gradient(180deg, #fbf7ff 0%, #fff9f5 44%, #fffdf8 100%);
  animation: fadeInUp 0.45s $xc-ease both;
}

.page-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.page-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(24rpx);
  opacity: 0.8;
}

.page-glow--one {
  top: -80rpx;
  right: -80rpx;
  width: 360rpx;
  height: 360rpx;
  background: radial-gradient(circle, rgba(155, 126, 216, 0.16), transparent 72%);
}

.page-glow--two {
  top: 520rpx;
  left: -120rpx;
  width: 300rpx;
  height: 300rpx;
  background: radial-gradient(circle, rgba(232, 114, 154, 0.12), transparent 72%);
}

.page-glow--three {
  bottom: 120rpx;
  right: -90rpx;
  width: 280rpx;
  height: 280rpx;
  background: radial-gradient(circle, rgba(212, 168, 83, 0.12), transparent 72%);
}

.state-panel {
  position: relative;
  z-index: 1;
  margin: 28rpx;
  padding: 34rpx 28rpx;
  border-radius: 30rpx;
  @include glass;
}

.state-panel--error {
  border-color: rgba(232, 114, 154, 0.24);
}

.state-panel__text {
  font-size: 28rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.report {
  position: relative;
  z-index: 1;
  padding: 24rpx 24rpx calc(56rpx + env(safe-area-inset-bottom, 0rpx));
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.d3 {
  animation: fadeInUp 0.55s $xc-ease both;
  animation-delay: 0.18s;
}

.d4 {
  animation: fadeInUp 0.55s $xc-ease both;
  animation-delay: 0.24s;
}

.d5 {
  animation: fadeInUp 0.55s $xc-ease both;
  animation-delay: 0.3s;
}

.panel {
  position: relative;
  overflow: hidden;
  @include card-base;
  padding: 28rpx;
  border-radius: 30rpx;
  box-shadow: 0 16rpx 42rpx rgba(113, 87, 152, 0.08);
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.section-head--light {
  color: #fff;
}

.section-eyebrow {
  display: block;
  font-size: 20rpx;
  letter-spacing: 1.4rpx;
  text-transform: uppercase;
  color: $xc-muted;
}

.section-eyebrow--light {
  color: rgba(255, 255, 255, 0.72);
}

.section-title {
  display: block;
  margin-top: 6rpx;
  font-size: 31rpx;
  line-height: 1.2;
  font-weight: 900;
  color: $xc-ink;
}

.section-title--light {
  color: #fff;
}

.section-subtitle {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.section-badge {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 700;
  background: rgba(155, 126, 216, 0.1);
  color: $xc-purple-d;
}

.report-callout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 16rpx;
  align-items: flex-start;
}

.report-callout__bubble {
  min-width: 0;
}

.report-callout__aside {
  width: 144rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.report-callout__mascot {
  align-self: center;
}

.report-callout__chips {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.report-callout__chip {
  padding: 10rpx 14rpx;
  border-radius: 999rpx;
  text-align: center;
  font-size: 20rpx;
  color: $xc-purple-d;
  background: rgba(155, 126, 216, 0.1);
}

.panel--metaphor {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(255, 249, 253, 0.96));
}

.metaphors {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.metaphor-card {
  position: relative;
  overflow: hidden;
  border-radius: 28rpx;
  padding: 24rpx 22rpx 20rpx;
  background:
    linear-gradient(145deg, rgba(124, 93, 191, 0.94), rgba(232, 114, 154, 0.86), rgba(242, 166, 139, 0.82));
  color: #fff;
  box-shadow: 0 18rpx 48rpx rgba(124, 93, 191, 0.16);
  transition: transform 0.24s $xc-spring, box-shadow 0.24s $xc-ease;
}

.metaphor-card--open {
  transform: translateY(-4rpx) scale(1.01);
  box-shadow: 0 22rpx 54rpx rgba(124, 93, 191, 0.22);
}

.metaphor-card__watermark {
  position: absolute;
  right: 18rpx;
  top: 16rpx;
  font-size: 18rpx;
  letter-spacing: 1rpx;
  opacity: 0.28;
}

.metaphor-card__emoji,
.metaphor-card__category,
.metaphor-card__title,
.metaphor-card__body,
.metaphor-card__toggle {
  position: relative;
  z-index: 1;
}

.metaphor-card__emoji {
  display: block;
  font-size: 44rpx;
}

.metaphor-card__category {
  display: block;
  margin-top: 14rpx;
  font-size: 20rpx;
  opacity: 0.78;
}

.metaphor-card__title {
  display: block;
  margin-top: 10rpx;
  font-size: 32rpx;
  font-family: $xc-font-serif;
  font-weight: 800;
}

.metaphor-card__body {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.72;
}

.metaphor-card__toggle {
  display: block;
  margin-top: 14rpx;
  font-size: 20rpx;
  opacity: 0.84;
}

.panel--percentile {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(248, 243, 255, 0.96));
}

.percentile-grid {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.percentile-card {
  border-radius: 22rpx;
  padding: 18rpx 14rpx;
  background: rgba(255, 255, 255, 0.82);
  border: 2rpx solid rgba(155, 126, 216, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.percentile-ring {
  width: 118rpx;
  height: 118rpx;
  padding: 8rpx;
  border-radius: 50%;
}

.percentile-ring__inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.94);
}

.percentile-ring__value {
  font-size: 24rpx;
  font-weight: 800;
  color: $xc-purple-d;
}

.percentile-card__title {
  margin-top: 14rpx;
  font-size: 22rpx;
  font-weight: 700;
  color: $xc-ink;
}

.percentile-card__desc {
  margin-top: 8rpx;
  font-size: 20rpx;
  line-height: 1.5;
  color: $xc-muted;
}

.panel--dimension {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 251, 247, 0.96));
}

.dimension-analysis {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.dimension-analysis__radar {
  border-radius: 26rpx;
  padding: 12rpx;
  background: rgba(255, 255, 255, 0.78);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.dimension-analysis__bars {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.dimension-bar {
  padding: 16rpx 18rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.76);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.dimension-bar__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.dimension-bar__name-wrap {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.dimension-bar__index {
  width: 34rpx;
  height: 34rpx;
  border-radius: 50%;
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 18rpx;
  font-weight: 800;
  background: rgba(155, 126, 216, 0.1);
  color: $xc-purple-d;
}

.dimension-bar__name {
  font-size: 23rpx;
  font-weight: 700;
  color: $xc-ink;
}

.dimension-bar__score {
  font-size: 22rpx;
  font-weight: 700;
  color: $xc-purple-d;
}

.dimension-bar__track {
  margin-top: 12rpx;
  height: 16rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.1);
  overflow: hidden;
}

.dimension-bar__fill {
  height: 100%;
  border-radius: inherit;
  transition: width 0.6s $xc-ease;
}

.weather {
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.2), transparent 34%),
    linear-gradient(160deg, #3a2552, #5b3d7a, #7c5dbf);
  color: #fff;
}

.weather__mood {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.14);
  font-size: 20rpx;
  font-weight: 600;
}

.weather__head {
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.weather__symbol {
  width: 120rpx;
  height: 120rpx;
  border-radius: 32rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.14);
}

.weather__emoji {
  font-size: 58rpx;
}

.weather__info {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.weather__title {
  font-size: 34rpx;
  font-weight: 800;
}

.weather__temp {
  font-size: 44rpx;
  font-weight: 900;
}

.weather__status {
  font-size: 22rpx;
  opacity: 0.82;
}

.weather__desc {
  display: block;
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 1.76;
  color: rgba(255, 255, 255, 0.92);
}

.weather__tags {
  margin-top: 16rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.weather__tag {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
}

.weather__tag--good {
  background: rgba(124, 197, 178, 0.22);
  color: #ebfffa;
}

.weather__tag--caution {
  background: rgba(255, 238, 209, 0.18);
  color: #fff2d1;
}

.panel--dna {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(253, 248, 240, 0.96));
}

.dna-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.dna-item {
  padding: 16rpx 18rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.78);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.dna-item__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.dna-item__label-wrap {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.dna-item__dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.dna-item__label {
  font-size: 22rpx;
  font-weight: 700;
  color: $xc-ink;
}

.dna-item__value {
  font-size: 22rpx;
  font-weight: 800;
  color: $xc-purple-d;
}

.dna-item__track {
  margin-top: 12rpx;
  height: 18rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.1);
  overflow: hidden;
}

.dna-item__fill {
  height: 100%;
  border-radius: inherit;
  transition: width 0.72s $xc-ease;
}

.hidden-persona {
  background:
    radial-gradient(circle at top, rgba(201, 181, 240, 0.14), transparent 58%),
    linear-gradient(180deg, rgba(34, 21, 48, 0.98), rgba(47, 31, 66, 0.98));
}

.hidden-lock,
.hidden-unlocked {
  margin-top: 18rpx;
  border-radius: 26rpx;
  min-height: 190rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
}

.hidden-lock__icon {
  font-size: 60rpx;
}

.hidden-lock__hint {
  margin-top: 12rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.82);
}

.hidden-lock__line {
  width: 160rpx;
  height: 6rpx;
  margin-top: 16rpx;
  border-radius: 999rpx;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.44), rgba(255, 255, 255, 0.14));
}

.hidden-lock--shake {
  animation: shake 0.42s ease-in-out;
}

.hidden-unlocked {
  align-items: flex-start;
  padding: 24rpx;
  animation: fadeInUp 0.55s $xc-spring both;
}

.hidden-unlocked__emoji {
  font-size: 42rpx;
}

.hidden-unlocked__title {
  margin-top: 12rpx;
  font-size: 30rpx;
  font-weight: 800;
  color: #fff;
}

.hidden-unlocked__body {
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.76;
  color: rgba(255, 255, 255, 0.92);
}

.quote-card {
  position: relative;
  overflow: hidden;
  padding: 34rpx 28rpx;
  border-radius: 30rpx;
  background:
    linear-gradient(160deg, #3a2552, #5b3d7a, #7c5dbf);
  color: #fff;
  box-shadow: 0 18rpx 52rpx rgba(91, 61, 122, 0.22);
}

.quote-card__mark {
  position: absolute;
  top: 6rpx;
  left: 18rpx;
  font-size: 120rpx;
  line-height: 1;
  opacity: 0.08;
}

.quote-card__text {
  position: relative;
  z-index: 1;
  display: block;
  font-size: 30rpx;
  line-height: 1.88;
  font-family: $xc-font-serif;
  font-style: italic;
}

.quote-card__attr {
  position: relative;
  z-index: 1;
  display: block;
  margin-top: 18rpx;
  font-size: 20rpx;
  letter-spacing: 1rpx;
  opacity: 0.74;
}

.capsule-letter {
  position: relative;
  overflow: hidden;
  padding: 34rpx 28rpx;
  border-radius: 30rpx;
  background:
    linear-gradient(160deg, #faf6ee, #f7efe2, #f5ede2);
  border: 2rpx solid rgba(212, 168, 83, 0.16);
  box-shadow: 0 16rpx 42rpx rgba(212, 168, 83, 0.1);
}

.capsule-letter::before {
  content: "";
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 30rpx,
    rgba(155, 126, 216, 0.03) 30rpx,
    rgba(155, 126, 216, 0.03) 31rpx
  );
  pointer-events: none;
}

.capsule-letter__stamp,
.capsule-letter__dear,
.capsule-letter__text,
.capsule-letter__sign {
  position: relative;
  z-index: 1;
}

.capsule-letter__stamp {
  position: absolute;
  top: 20rpx;
  right: 22rpx;
  font-size: 30rpx;
  opacity: 0.56;
  transform: rotate(12deg);
}

.capsule-letter__dear {
  display: block;
  font-size: 30rpx;
  font-family: $xc-font-serif;
  font-weight: 800;
  color: $xc-ink;
}

.capsule-letter__text {
  display: block;
  margin-top: 18rpx;
  font-size: 24rpx;
  line-height: 2;
  color: $xc-muted;
  white-space: pre-line;
  font-family: $xc-font-serif;
  font-style: italic;
}

.capsule-letter__sign {
  display: block;
  margin-top: 18rpx;
  font-size: 21rpx;
  color: $xc-muted;
  text-align: right;
}

.panel--capsule-input {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(250, 245, 237, 0.94));
}

.capsule-success {
  margin-top: 18rpx;
  border-radius: 24rpx;
  padding: 26rpx 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  background: linear-gradient(145deg, rgba(124, 197, 178, 0.16), rgba(255, 255, 255, 0.86));
}

.capsule-success__icon {
  font-size: 42rpx;
}

.capsule-success__text {
  font-size: 24rpx;
  line-height: 1.72;
  color: $xc-muted;
  text-align: center;
}

.capsule-input {
  width: 100%;
  box-sizing: border-box;
  min-height: 260rpx;
  margin-top: 18rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.86);
  border: 2rpx solid rgba(212, 168, 83, 0.16);
  font-size: 24rpx;
  line-height: 1.78;
  color: $xc-ink;
}

.capsule-durations {
  margin-top: 16rpx;
  display: flex;
  gap: 12rpx;
}

.capsule-duration {
  flex: 1;
  border: none;
  border-radius: 999rpx;
  padding: 14rpx 0;
  font-size: 22rpx;
  color: $xc-muted;
  background: rgba(255, 255, 255, 0.82);
}

.capsule-duration--active {
  background: linear-gradient(135deg, rgba(155, 126, 216, 0.16), rgba(232, 114, 154, 0.14));
  color: $xc-purple-d;
  font-weight: 800;
}

.capsule-duration::after {
  border: none;
}

.limited-banner {
  position: relative;
  overflow: hidden;
  padding: 22rpx 22rpx 24rpx;
  border-radius: 28rpx;
  background: linear-gradient(145deg, #fff0e8, #fde6ef);
  border: 2rpx solid rgba(232, 114, 154, 0.12);
}

.limited-banner__shine {
  position: absolute;
  top: -26rpx;
  right: -10rpx;
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.6), transparent 70%);
}

.limited-banner__title,
.limited-banner__desc {
  position: relative;
  z-index: 1;
  display: block;
}

.limited-banner__title {
  font-size: 28rpx;
  font-weight: 900;
  color: $xc-ink;
}

.limited-banner__desc {
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.actions,
.bottom-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.bottom-actions {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.button {
  border: none;
  border-radius: 999rpx;
  padding: 18rpx 18rpx;
  font-size: 23rpx;
  font-weight: 800;
  line-height: 1.2;
}

.button::after {
  border: none;
}

.button--primary {
  color: #fff;
  @include btn-primary;
}

.button--glass {
  color: $xc-purple-d;
  background: rgba(255, 255, 255, 0.78);
  border: 2rpx solid rgba(155, 126, 216, 0.12);
  box-shadow: 0 12rpx 28rpx rgba(155, 126, 216, 0.08);
}

.button--soft {
  color: $xc-ink;
  background: rgba(255, 255, 255, 0.82);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.next-test__card {
  margin-top: 18rpx;
  border-radius: 26rpx;
  padding: 20rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.84), rgba(249, 243, 255, 0.96));
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.next-test__icon {
  width: 84rpx;
  height: 84rpx;
  border-radius: 26rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  background: linear-gradient(135deg, rgba(155, 126, 216, 0.16), rgba(232, 114, 154, 0.12));
}

.next-test__body {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.next-test__name {
  font-size: 26rpx;
  font-weight: 800;
  color: $xc-ink;
}

.next-test__meta {
  font-size: 21rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.next-test__cta {
  font-size: 22rpx;
  font-weight: 800;
  color: $xc-purple-d;
}

@keyframes shake {
  0%,
  100% {
    transform: rotate(0deg);
  }

  25% {
    transform: rotate(-4deg);
  }

  75% {
    transform: rotate(4deg);
  }
}

@media (max-width: 420px) {
  .report-callout {
    grid-template-columns: 1fr;
  }

  .report-callout__aside {
    width: auto;
  }

  .report-callout__chips {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .percentile-grid,
  .actions {
    grid-template-columns: 1fr;
  }
}
</style>
