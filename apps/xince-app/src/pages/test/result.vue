<script setup lang="ts">
import { computed, getCurrentInstance, onBeforeUnmount, ref } from "vue";
import { onLoad, onReady, onUnload } from "@dcloudio/uni-app";

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
const activeDeepPanel = ref<DeepPanelKey | null>(null);
const percentileValues = ref([0, 0, 0, 0]);
const percentileAnimated = ref(false);
const dnaVisible = ref(false);
const hiddenUnlocked = ref(false);
const hiddenUnlockAnimating = ref(false);
const hiddenExpanded = ref(false);
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

const quoteText = computed(
  () =>
    report.value?.persona.description ||
    report.value?.summary ||
    "你正在成为更真实、更稳定、更自由的自己。",
);

const capsulePrompt = computed(
  () => `如果未来的你再读到「${personaName.value}」这一刻，会想对今天说什么？`,
);

const futureLetter = computed(
  () =>
    `亲爱的现在的我：\n\n谢谢你在这个阶段认真地认识自己。你并不需要马上成为完美的人，只要继续保持 ${personaName.value} 的勇气和温柔，未来会自然展开。\n\n愿你在下次打开胶囊时，依旧记得今天的初心。`,
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

onReady(() => {
  initObservers();
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
    <view v-if="loading" class="state-panel">
      <text class="state-panel__text">正在生成报告...</text>
    </view>

    <view v-else-if="error" class="state-panel state-panel--error">
      <text class="state-panel__text">{{ error }}</text>
    </view>

    <view v-else-if="report" class="report">
      <ReportHeroPanels
        :hero-style="heroStyle"
        :test-name="report.test_name"
        :persona-emoji="personaEmoji"
        :persona-name="personaName"
        :tier-text="tierText"
        :total-score="totalScore"
        :score-progress="scoreProgress"
        :top-three-dimensions="topThreeDimensions"
        :quote-text="quoteText"
        @share="openSharePoster('report')"
      />

      <view class="panel d3">
        <view class="mascot-comment">
          <XiaoCe expression="happy" size="md" :animated="true" />
          <view class="mascot-comment__bubble">
            <XcBubble :text="mascotComment" :typing="true" :persistent="true" />
          </view>
        </view>
      </view>

      <view class="panel d4">
        <text class="panel-title">灵魂隐喻</text>
        <view class="metaphors">
          <view
            v-for="item in metaphorCards"
            :key="`${item.category}-${item.title}`"
            class="metaphor-card"
            :class="{ 'metaphor-card--open': hiddenExpanded }"
            @tap="hiddenExpanded = !hiddenExpanded"
          >
            <text class="metaphor-card__emoji">{{ item.emoji }}</text>
            <text class="metaphor-card__category">{{ item.category }}</text>
            <text class="metaphor-card__title">{{ item.title }}</text>
            <text class="metaphor-card__body">{{ item.subtitle }}</text>
          </view>
        </view>
      </view>

      <view class="panel js-percentile d5">
        <text class="panel-title">人群百分比</text>
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

      <view class="panel">
        <text class="panel-title">维度分析</text>
        <view class="dimension-analysis">
          <view class="dimension-analysis__radar">
            <PersonaRadarCanvas :dimensions="radarCanvasDimensions" />
          </view>
          <view class="dimension-analysis__bars">
            <view v-for="(item, index) in report.radar_dimensions" :key="item.dim_code" class="dimension-bar">
              <view class="dimension-bar__head">
                <text class="dimension-bar__name">{{ item.label }}</text>
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

      <view class="panel weather">
        <text class="panel-title">灵魂天气</text>
        <view class="weather__head">
          <text class="weather__emoji">{{ soulWeather.emoji }}</text>
          <view>
            <text class="weather__title">{{ soulWeather.title }}</text>
            <text class="weather__temp">{{ soulWeather.temp }}</text>
          </view>
        </view>
        <text class="weather__desc">{{ report.soul_weather.description }}</text>
        <view class="weather__tags">
          <text v-for="tag in soulWeather.tags" :key="tag" class="weather__tag">{{ tag }}</text>
        </view>
      </view>

      <view class="panel js-dna">
        <text class="panel-title">人格 DNA</text>
        <view class="dna-list">
          <view v-for="(item, index) in report.dna_segments" :key="item.dim_code" class="dna-item">
            <text class="dna-item__label">{{ item.label }}</text>
            <view class="dna-item__track">
              <view
                class="dna-item__fill"
                :style="{ width: dnaWidth(item), background: dnaGradient(index), transitionDelay: `${index * 70}ms` }"
              />
            </view>
            <text class="dna-item__value">{{ item.percentage }}%</text>
          </view>
        </view>
      </view>

      <view class="panel hidden-persona js-hidden-persona" :class="{ 'hidden-persona--unlocked': hiddenUnlocked }">
        <text class="panel-title">隐藏人格</text>
        <view v-if="!hiddenUnlocked" class="hidden-lock" :class="{ 'hidden-lock--shake': hiddenUnlockAnimating }">
          <text class="hidden-lock__icon">🔒</text>
          <text class="hidden-lock__hint">↓ 下滑解锁</text>
        </view>
        <view v-else class="hidden-unlocked">
          <text class="hidden-unlocked__title">{{ weakestDimension?.label || "隐藏面向" }}</text>
          <text class="hidden-unlocked__body">{{ hiddenPersonaText }}</text>
        </view>
      </view>

      <ReportDeepAnalysis
        :pending="aiPending"
        :ai-refreshing="aiRefreshing"
        :ai-status="report.ai_status"
        :sections="aiSections"
        :active-key="activeDeepPanel"
        @toggle="toggleDeepPanel"
        @retry="handleRetryAi"
      />

      <view class="panel quote-card">
        <text class="quote-card__mark">“</text>
        <text class="quote-card__text">{{ quoteText }}</text>
      </view>

      <view class="panel capsule-letter">
        <text class="panel-title">来自未来的你</text>
        <text class="capsule-letter__text">{{ futureLetter }}</text>
      </view>

      <view class="panel">
        <text class="panel-title">写入时间胶囊</text>
        <view v-if="capsuleCreated" class="capsule-success">
          <text class="capsule-success__icon">✨</text>
          <text class="capsule-success__text">已写入成功，等时间来揭晓答案。</text>
        </view>
        <template v-else>
          <text class="panel-body">{{ capsulePrompt }}</text>
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
          <button class="mini-button" :loading="capsuleSaving" @tap="createCapsule">
            {{ capsuleSaving ? "封存中..." : "封存到时光胶囊" }}
          </button>
        </template>
      </view>

      <view class="panel limited-banner">
        <view class="limited-banner__shine" />
        <text class="limited-banner__title">限时挑战 · MBTI 进阶版</text>
        <text class="limited-banner__desc">倒计时 {{ countdownText }} 后结束，快邀请好友一起测。</text>
      </view>

      <view class="actions">
        <button class="button button--primary" @tap="openSharePoster('report')">分享报告</button>
        <button class="button button--glass" @tap="openSharePoster('challenge')">好友挑战</button>
        <button class="button button--glass" @tap="goMatch">灵魂匹配</button>
      </view>

      <view class="panel next-test">
        <text class="panel-title">推荐下一个测试</text>
        <view v-if="nextTest" class="next-test__card" @tap="openNextTest">
          <text class="next-test__name">{{ nextTest.name }}</text>
          <text class="next-test__meta">
            {{ nextTest.category }} · {{ nextTest.question_count }} 题 · {{ nextTest.duration_hint || "约 5 分钟" }}
          </text>
          <text class="next-test__cta">开始下一测 →</text>
        </view>
        <text v-else class="panel-body">去首页看看今天为你准备的热门测试。</text>
      </view>

      <view class="bottom-actions">
        <button class="mini-button mini-button--light" @tap="goProfile">查看我的画像</button>
        <button class="mini-button mini-button--light" @tap="backHome">返回首页</button>
      </view>
    </view>
  </scroll-view>
</template>

<style lang="scss" scoped>
.page {
  height: 100vh;
  animation: fadeInUp 0.45s $xc-ease both;
}

.state-panel {
  margin: 28rpx;
  padding: 32rpx 28rpx;
  border-radius: 24rpx;
  @include glass;
}

.state-panel--error {
  border-color: rgba(232, 114, 154, 0.24);
}

.state-panel__text {
  font-size: 28rpx;
  color: $xc-muted;
}

.report {
  padding: 24rpx 24rpx calc(56rpx + env(safe-area-inset-bottom, 0rpx));
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.d1 {
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.06s;
}

.d2 {
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.12s;
}

.d3 {
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.18s;
}

.d4 {
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.24s;
}

.d5 {
  animation: fadeInUp 0.5s $xc-ease both;
  animation-delay: 0.3s;
}

.hero {
  border-radius: $xc-r-xl;
  padding: 34rpx 28rpx;
  color: #fff;
  box-shadow: $xc-sh-lg;
}

.hero__eyebrow {
  display: block;
  font-size: 22rpx;
  opacity: 0.88;
}

.hero__main {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 20rpx;
  align-items: center;
}

.hero__emoji {
  font-size: 74rpx;
  line-height: 1;
}

.hero__title-wrap {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.hero__title {
  font-size: 50rpx;
  font-family: $xc-font-serif;
  font-weight: 700;
}

.hero__tier {
  align-self: flex-start;
  padding: 8rpx 16rpx;
  border-radius: $xc-r-pill;
  background: rgba(255, 255, 255, 0.2);
  font-size: 22rpx;
}

.score-ring__circle {
  width: 148rpx;
  height: 148rpx;
  border-radius: 50%;
  padding: 8rpx;
}

.score-ring__inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(31, 22, 41, 0.42);
}

.score-ring__value {
  font-size: 34rpx;
  font-weight: 700;
}

.score-ring__label {
  margin-top: 2rpx;
  font-size: 20rpx;
  opacity: 0.86;
}

.hero-top-dims {
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.hero-dim-card {
  padding: 16rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.18);
}

.hero-dim-card__name {
  display: block;
  font-size: 22rpx;
}

.hero-dim-card__score {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 700;
}

.panel {
  @include card-base;
  padding: 26rpx;
  border-radius: 26rpx;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.panel-title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.panel-body {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.persona-share {
  margin-top: 18rpx;
  border-radius: 22rpx;
  padding: 24rpx;
  background: linear-gradient(135deg, rgba(155, 126, 216, 0.9), rgba(232, 114, 154, 0.8));
  color: #fff;
}

.persona-share__name {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
}

.persona-share__emoji {
  display: block;
  margin-top: 12rpx;
  font-size: 56rpx;
}

.persona-share__signature,
.persona-share__top {
  display: block;
  margin-top: 12rpx;
  font-size: 23rpx;
  line-height: 1.65;
}

.mascot-comment {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.mascot-comment__bubble {
  flex: 1;
}

.metaphors {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.metaphor-card {
  padding: 18rpx 14rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 2rpx solid rgba(155, 126, 216, 0.12);
  transition: transform 0.24s $xc-ease;
}

.metaphor-card--open {
  transform: translateY(-4rpx) scale(1.02);
}

.metaphor-card__emoji {
  display: block;
  font-size: 34rpx;
}

.metaphor-card__category {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: $xc-muted;
}

.metaphor-card__title {
  display: block;
  margin-top: 6rpx;
  font-size: 24rpx;
  font-weight: 600;
}

.metaphor-card__body {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  line-height: 1.5;
  color: $xc-muted;
}

.percentile-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.percentile-card {
  @include glass;
  border-radius: 18rpx;
  padding: 16rpx 12rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.percentile-ring {
  width: 104rpx;
  height: 104rpx;
  border-radius: 50%;
  padding: 7rpx;
}

.percentile-ring__inner {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.92);
}

.percentile-ring__value {
  font-size: 22rpx;
  font-weight: 700;
  color: $xc-purple-d;
}

.percentile-card__title {
  margin-top: 12rpx;
  font-size: 22rpx;
  font-weight: 600;
}

.percentile-card__desc {
  margin-top: 6rpx;
  font-size: 20rpx;
  color: $xc-muted;
  text-align: center;
}

.dimension-analysis {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.dimension-analysis__bars {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.dimension-bar__head {
  display: flex;
  justify-content: space-between;
  font-size: 22rpx;
}

.dimension-bar__track {
  height: 16rpx;
  margin-top: 8rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.1);
  overflow: hidden;
}

.dimension-bar__fill {
  height: 100%;
  border-radius: inherit;
}

.weather {
  background:
    linear-gradient(135deg, rgba(58, 46, 66, 0.95), rgba(80, 62, 100, 0.85)),
    #3a2e42;
}

.weather .panel-title,
.weather__title,
.weather__temp,
.weather__desc,
.weather__tag {
  color: #fff;
}

.weather__head {
  margin-top: 14rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.weather__emoji {
  font-size: 58rpx;
}

.weather__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
}

.weather__temp {
  display: block;
  margin-top: 4rpx;
  font-size: 22rpx;
  opacity: 0.85;
}

.weather__desc {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.65;
}

.weather__tags {
  margin-top: 14rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.weather__tag {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  background: rgba(255, 255, 255, 0.14);
}

.dna-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.dna-item {
  display: grid;
  grid-template-columns: 112rpx 1fr auto;
  align-items: center;
  gap: 12rpx;
}

.dna-item__label,
.dna-item__value {
  font-size: 22rpx;
}

.dna-item__track {
  height: 16rpx;
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
    radial-gradient(circle at top, rgba(201, 181, 240, 0.14), transparent 60%),
    linear-gradient(180deg, rgba(58, 46, 66, 0.95), rgba(47, 36, 57, 0.98));
}

.hidden-persona .panel-title {
  color: #fff;
}

.hidden-lock,
.hidden-unlocked {
  margin-top: 14rpx;
  border-radius: 20rpx;
  min-height: 160rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.08);
}

.hidden-lock__icon {
  font-size: 56rpx;
}

.hidden-lock__hint {
  margin-top: 10rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.8);
}

.hidden-lock--shake {
  animation: shake 0.42s ease-in-out;
}

.hidden-unlocked {
  animation: flipIn 0.56s $xc-spring both;
  align-items: flex-start;
  padding: 20rpx;
}

.hidden-unlocked__title {
  font-size: 28rpx;
  font-weight: 700;
  color: #fff;
}

.hidden-unlocked__body {
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.72;
  color: rgba(255, 255, 255, 0.9);
}

.ai-skeleton {
  margin-top: 14rpx;
}

.ai-skeleton__line {
  height: 22rpx;
  border-radius: 8rpx;
  margin-bottom: 12rpx;
  background: linear-gradient(
    100deg,
    rgba(237, 229, 249, 0.25),
    rgba(237, 229, 249, 0.55),
    rgba(237, 229, 249, 0.2)
  );
  background-size: 220% 100%;
  animation: shimmer 1.5s linear infinite;
}

.ai-skeleton__line--short {
  width: 68%;
}

.ai-skeleton__hint {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.deep-list {
  margin-top: 14rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.deep-card {
  border-radius: 16rpx;
  border: 2rpx solid rgba(155, 126, 216, 0.1);
  overflow: hidden;
}

.deep-card__head {
  padding: 18rpx 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.deep-card__title {
  font-size: 24rpx;
  font-weight: 600;
}

.deep-card__icon {
  font-size: 30rpx;
  color: $xc-purple;
}

.deep-card__body {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.32s $xc-ease;
}

.deep-card__body text {
  display: block;
  padding: 0 16rpx 18rpx;
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.deep-card--open .deep-card__body {
  max-height: 280rpx;
}

.quote-card {
  background:
    linear-gradient(140deg, rgba(58, 46, 66, 0.95), rgba(80, 62, 100, 0.88)),
    #3a2e42;
}

.quote-card__mark {
  font-size: 82rpx;
  line-height: 1;
  color: rgba(255, 255, 255, 0.55);
}

.quote-card__text {
  display: block;
  margin-top: 6rpx;
  font-size: 32rpx;
  line-height: 1.6;
  font-family: $xc-font-serif;
  color: #fff;
}

.capsule-letter {
  background:
    repeating-linear-gradient(
      0deg,
      rgba(212, 168, 83, 0.06) 0,
      rgba(212, 168, 83, 0.06) 2rpx,
      transparent 2rpx,
      transparent 20rpx
    ),
    linear-gradient(145deg, rgba(255, 240, 232, 0.95), rgba(253, 244, 222, 0.92));
}

.capsule-letter__text {
  display: block;
  margin-top: 14rpx;
  white-space: pre-wrap;
  font-size: 24rpx;
  line-height: 1.8;
  color: #6a4f3c;
}

.capsule-input {
  width: 100%;
  min-height: 220rpx;
  margin-top: 16rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  border: 2rpx solid rgba(155, 126, 216, 0.15);
  background: rgba(255, 255, 255, 0.92);
  font-size: 24rpx;
  line-height: 1.7;
}

.capsule-durations {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10rpx;
}

.capsule-duration {
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.88);
  color: $xc-muted;
  font-size: 23rpx;
}

.capsule-duration--active {
  background: linear-gradient(135deg, #d4a853, #e5c97e);
  color: #fff;
}

.capsule-success {
  margin-top: 16rpx;
  border-radius: 18rpx;
  padding: 18rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  background: rgba(124, 197, 178, 0.15);
}

.capsule-success__icon {
  font-size: 34rpx;
}

.capsule-success__text {
  font-size: 24rpx;
  color: $xc-muted;
}

.limited-banner {
  position: relative;
  overflow: hidden;
  border: 2rpx solid rgba(212, 168, 83, 0.45);
  background:
    linear-gradient(140deg, rgba(201, 181, 240, 0.24), rgba(232, 114, 154, 0.18)),
    rgba(255, 255, 255, 0.92);
}

.limited-banner__shine {
  position: absolute;
  inset: 0;
  background: linear-gradient(100deg, transparent 20%, rgba(255, 255, 255, 0.6) 50%, transparent 80%);
  transform: translateX(-120%);
  animation: bannerShimmer 1.8s linear infinite;
}

.limited-banner__title,
.limited-banner__desc {
  position: relative;
  z-index: 1;
  display: block;
}

.limited-banner__title {
  font-size: 28rpx;
  font-weight: 700;
}

.limited-banner__desc {
  margin-top: 10rpx;
  font-size: 23rpx;
  color: $xc-muted;
}

.actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10rpx;
}

.button {
  border-radius: $xc-r-btn;
  font-size: 24rpx;
}

.button--primary {
  @include btn-primary;
}

.button--glass {
  @include glass;
  color: $xc-purple;
}

.next-test__card {
  margin-top: 14rpx;
  border-radius: 18rpx;
  padding: 20rpx;
  border: 2rpx solid rgba(155, 126, 216, 0.12);
  background:
    linear-gradient(120deg, rgba(255, 255, 255, 0.95), rgba(237, 229, 249, 0.42)),
    #fff;
}

.next-test__name {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
}

.next-test__meta {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.next-test__cta {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: $xc-purple;
}

.bottom-actions {
  display: flex;
  gap: 10rpx;
}

.mini-button {
  margin-top: 14rpx;
  border-radius: $xc-r-btn;
  background: linear-gradient(135deg, #9b7ed8, #e8729a);
  color: #fff;
  font-size: 23rpx;
}

.mini-button--light {
  margin-top: 0;
  flex: 1;
  background: rgba(255, 255, 255, 0.92);
  color: $xc-purple;
  border: 2rpx solid rgba(155, 126, 216, 0.18);
}

@keyframes bannerShimmer {
  0% {
    transform: translateX(-120%);
  }
  100% {
    transform: translateX(120%);
  }
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-6rpx);
  }
  75% {
    transform: translateX(6rpx);
  }
}

@keyframes flipIn {
  from {
    opacity: 0;
    transform: rotateY(90deg);
  }
  to {
    opacity: 1;
    transform: rotateY(0);
  }
}
</style>
