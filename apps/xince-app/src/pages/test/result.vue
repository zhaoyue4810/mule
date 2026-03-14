<script setup lang="ts">
import { computed, ref } from "vue";
import { onLoad, onUnload } from "@dcloudio/uni-app";

import type { AppReportDetail } from "@/shared/models/reports";
import { createTimeCapsule } from "@/shared/services/capsule";
import {
  fetchReportAiStatus,
  fetchReportDetail,
  retryReportAi,
} from "@/shared/services/reports";
import { SoundManager } from "@/shared/utils/sound-manager";

const report = ref<AppReportDetail | null>(null);
const loading = ref(true);
const error = ref("");
const aiRefreshing = ref(false);
const capsuleMessage = ref("");
const capsuleDuration = ref(30);
const capsuleSaving = ref(false);
let currentRecordId = 0;
let pollTimer: ReturnType<typeof setInterval> | null = null;

const titleText = computed(() =>
  report.value?.persona.persona_name
    ? `你当前最接近 ${report.value.persona.persona_name}`
    : "你的结果已经生成",
);

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

function openSharePoster(mode: "report" | "challenge" = "report") {
  if (!currentRecordId) {
    return;
  }
  uni.navigateTo({
    url: `/pages/test/share-poster?recordId=${currentRecordId}&mode=${mode}`,
  });
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function shareCardThemeClass(theme: string) {
  return `share-card--${theme || "sunset"}`;
}

const capsulePrompt = computed(() => {
  if (!report.value?.persona.persona_name) {
    return "把今天的感受写给未来的自己，等时间把答案慢慢发酵。";
  }
  return `如果未来的你再读到这份「${report.value.persona.persona_name}」的时刻，会想对今天的自己说什么？`;
});

async function copyShareText() {
  if (!report.value?.share_card?.share_text) {
    return;
  }
  try {
    await uni.setClipboardData({
      data: report.value.share_card.share_text,
    });
    uni.showToast({
      title: "分享文案已复制",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "复制失败",
      icon: "none",
    });
  }
}

async function createCapsule() {
  if (!report.value || capsuleSaving.value) {
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
    console.error(err);
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

async function loadReport(recordId: number) {
  loading.value = true;
  error.value = "";
  try {
    report.value = await fetchReportDetail(recordId);
    if (report.value.ai_status === "PENDING" || report.value.ai_status === "RUNNING") {
      startPolling();
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : "报告加载失败";
  } finally {
    loading.value = false;
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
  loadReport(recordId);
});

onUnload(() => {
  stopPolling();
});
</script>

<template>
  <view class="page">
    <view v-if="loading" class="panel">
      <text class="panel__body">正在生成报告...</text>
    </view>

    <view v-else-if="error" class="panel">
      <text class="panel__body">{{ error }}</text>
    </view>

    <view v-else-if="report" class="report">
      <view class="hero">
        <text class="hero__eyebrow">{{ report.test_name }} · 测试报告</text>
        <text class="hero__title">{{ titleText }}</text>
        <text class="hero__tier">{{ report.result_tier }}</text>
        <view class="hero__metrics">
          <view class="hero__metric">
            <text class="hero__metric-value">{{ report.total_score || 0 }}</text>
            <text class="hero__metric-label">总分</text>
          </view>
          <view class="hero__metric">
            <text class="hero__metric-value">{{ report.answered_count }}</text>
            <text class="hero__metric-label">题数</text>
          </view>
          <view class="hero__metric">
            <text class="hero__metric-value">{{ report.duration_seconds || 0 }}s</text>
            <text class="hero__metric-label">用时</text>
          </view>
        </view>
      </view>

      <view class="persona-card" v-if="report.persona.persona_name">
        <text class="persona-card__title">{{ report.persona.persona_name }}</text>
        <text class="persona-card__body">
          {{ report.persona.description || report.summary }}
        </text>
        <view v-if="report.persona_tags.length" class="tags">
          <text
            v-for="tag in report.persona_tags"
            :key="`${tag.tone}-${tag.label}`"
            class="tag"
          >
            {{ tag.label }}
          </text>
        </view>
      </view>

      <view class="panel">
        <text class="panel__title">结果摘要</text>
        <text class="panel__body">{{ report.summary }}</text>
      </view>

      <view class="panel" v-if="report.share_card">
        <text class="panel__title">分享卡片</text>
        <view class="share-card" :class="shareCardThemeClass(report.share_card.theme)">
          <text class="share-card__badge">{{ report.share_card.badge }}</text>
          <text class="share-card__eyebrow">{{ report.share_card.subtitle }}</text>
          <text class="share-card__title">{{ report.share_card.title }}</text>
          <text class="share-card__accent">主色标签：{{ report.share_card.accent }}</text>
          <view class="share-card__chips">
            <text
              v-for="chip in report.share_card.stat_chips"
              :key="chip"
              class="share-card__chip"
            >
              {{ chip }}
            </text>
          </view>
          <view class="share-card__highlights">
            <text
              v-for="line in report.share_card.highlight_lines"
              :key="line"
              class="share-card__line"
            >
              {{ line }}
            </text>
          </view>
          <text class="share-card__footer">{{ report.share_card.footer }}</text>
        </view>
        <button class="mini-button" @tap="copyShareText">复制分享文案</button>
        <button class="mini-button mini-button--ghost" @tap="openSharePoster('report')">
          打开海报预览
        </button>
        <button class="mini-button mini-button--ghost" @tap="openSharePoster('challenge')">
          发起好友挑战
        </button>
      </view>

      <view class="panel" v-if="report.radar_dimensions.length">
        <text class="panel__title">维度雷达</text>
        <view class="radar-list">
          <view
            v-for="item in report.radar_dimensions"
            :key="item.dim_code"
            class="radar-item"
          >
            <view class="radar-item__head">
              <text class="radar-item__label">{{ item.label }}</text>
              <text class="radar-item__value">{{ item.score.toFixed(2) }}</text>
            </view>
            <view class="radar-item__track">
              <view
                class="radar-item__fill"
                :style="{ width: formatPercent(item.normalized_score) }"
              />
            </view>
          </view>
        </view>
      </view>

      <view class="panel" v-if="report.top_dimensions.length">
        <text class="panel__title">核心维度</text>
        <view class="chips">
          <view
            v-for="item in report.top_dimensions"
            :key="item.dim_code"
            class="chip"
          >
            <text class="chip__name">{{ item.dim_code.toUpperCase() }}</text>
            <text class="chip__score">{{ item.score.toFixed(2) }}</text>
          </view>
        </view>
      </view>

      <view class="panel">
        <text class="panel__title">灵魂天气</text>
        <text class="panel__meta">{{ report.soul_weather.title }}</text>
        <text class="panel__body">{{ report.soul_weather.description }}</text>
      </view>

      <view class="panel" v-if="report.metaphor_cards.length">
        <text class="panel__title">隐喻卡片</text>
        <view class="metaphors">
          <view
            v-for="item in report.metaphor_cards"
            :key="`${item.category}-${item.title}`"
            class="metaphor-card"
          >
            <text class="metaphor-card__emoji">{{ item.emoji }}</text>
            <text class="metaphor-card__category">{{ item.category }}</text>
            <text class="metaphor-card__title">{{ item.title }}</text>
            <text class="metaphor-card__body">{{ item.subtitle }}</text>
          </view>
        </view>
      </view>

      <view class="panel" v-if="report.dna_segments.length">
        <text class="panel__title">DNA 条形图</text>
        <view class="dna-list">
          <view
            v-for="item in report.dna_segments"
            :key="item.dim_code"
            class="dna-item"
          >
            <text class="dna-item__label">{{ item.label }}</text>
            <view class="dna-item__track">
              <view
                class="dna-item__fill"
                :style="{ width: `${item.percentage}%` }"
              />
            </view>
            <text class="dna-item__percent">{{ item.percentage }}%</text>
          </view>
        </view>
      </view>

      <view class="panel" v-if="report.action_guides.length">
        <text class="panel__title">成长建议</text>
        <view class="guide-list">
          <view
            v-for="item in report.action_guides"
            :key="item.title"
            class="guide-card"
          >
            <text class="guide-card__title">{{ item.title }}</text>
            <text class="guide-card__body">{{ item.description }}</text>
          </view>
        </view>
      </view>

      <view class="panel">
        <text class="panel__title">AI 解读</text>
        <text class="panel__meta">
          {{ report.ai_status === "COMPLETED" ? "已生成" : "待生成" }}
        </text>
        <text class="panel__body">
          {{
            report.ai_text ||
            "当前 MVP 先展示同步结构化报告，AI 深度文案会在后续异步网关阶段接入。"
          }}
        </text>
        <button
          v-if="report.ai_status !== 'COMPLETED'"
          class="mini-button"
          :disabled="aiRefreshing"
          @tap="handleRetryAi"
        >
          {{ aiRefreshing ? "处理中..." : "重新生成 AI 解读" }}
        </button>
      </view>

      <view class="panel">
        <text class="panel__title">写给未来的自己</text>
        <text class="panel__body">{{ capsulePrompt }}</text>
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
      </view>

      <view class="actions">
        <button class="button button--secondary" @tap="goProfile">查看我的画像</button>
        <button class="button" @tap="backHome">返回首页</button>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 28rpx 28rpx 40rpx;
}

.report {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.hero {
  padding: 36rpx 30rpx;
  border-radius: 30rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 240, 219, 0.98), rgba(255, 204, 170, 0.92)),
    linear-gradient(145deg, #fff0db, #ffd9bb);
  box-shadow: $xc-shadow;
}

.hero__eyebrow {
  display: block;
  font-size: 22rpx;
  color: $xc-accent;
}

.hero__title {
  display: block;
  margin-top: 14rpx;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 1.35;
}

.hero__tier {
  display: inline-flex;
  margin-top: 18rpx;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.7);
  color: $xc-accent;
  font-size: 22rpx;
}

.hero__metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 22rpx;
}

.hero__metric {
  padding: 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.72);
}

.hero__metric-value {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
}

.hero__metric-label {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: rgba(43, 33, 24, 0.7);
}

.panel,
.persona-card {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 2rpx solid rgba(43, 33, 24, 0.06);
}

.persona-card {
  background:
    linear-gradient(145deg, rgba(255, 251, 245, 0.98), rgba(255, 239, 228, 0.9)),
    #fff;
}

.persona-card__title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.persona-card__body {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  line-height: 1.75;
  color: $xc-muted;
}

.panel__title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
}

.panel__body {
  display: block;
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 1.75;
  color: $xc-muted;
}

.panel__meta {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: $xc-accent;
}

.tags,
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 18rpx;
}

.tag,
.chip {
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 238, 224, 0.92);
  color: $xc-accent;
  font-size: 22rpx;
}

.chip {
  min-width: 152rpx;
  border-radius: 20rpx;
}

.chip__name,
.chip__score {
  display: block;
}

.chip__score {
  margin-top: 8rpx;
  font-size: 30rpx;
  font-weight: 700;
}

.radar-list,
.dna-list,
.guide-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 18rpx;
}

.radar-item__head,
.dna-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.radar-item__head {
  justify-content: space-between;
  margin-bottom: 10rpx;
}

.radar-item__label,
.radar-item__value,
.dna-item__label,
.dna-item__percent {
  font-size: 24rpx;
}

.radar-item__track,
.dna-item__track {
  flex: 1;
  height: 18rpx;
  border-radius: 999rpx;
  background: rgba(43, 33, 24, 0.08);
  overflow: hidden;
}

.radar-item__fill,
.dna-item__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, #d96f3d, #f1b17a);
}

.metaphors {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 18rpx;
}

.metaphor-card {
  padding: 22rpx 18rpx;
  border-radius: 22rpx;
  background: rgba(255, 248, 240, 0.95);
}

.metaphor-card__emoji {
  display: block;
  font-size: 34rpx;
}

.metaphor-card__category {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.metaphor-card__title {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  font-weight: 600;
}

.metaphor-card__body {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.guide-card {
  padding: 22rpx;
  border-radius: 20rpx;
  background: rgba(255, 248, 240, 0.95);
}

.guide-card__title {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
}

.guide-card__body {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.share-card {
  margin-top: 18rpx;
  padding: 26rpx 24rpx;
  border-radius: 24rpx;
  border: 2rpx solid rgba(217, 111, 61, 0.1);
  overflow: hidden;
  position: relative;
}

.share-card--dawn {
  background:
    radial-gradient(circle at top right, rgba(255, 245, 230, 0.98), rgba(255, 206, 171, 0.9)),
    linear-gradient(145deg, #fff1df, #ffc8a4);
}

.share-card--aurora {
  background:
    radial-gradient(circle at top right, rgba(241, 255, 245, 0.98), rgba(190, 246, 214, 0.92)),
    linear-gradient(145deg, #ebfff2, #b9efcf);
}

.share-card--ember {
  background:
    radial-gradient(circle at top right, rgba(255, 245, 240, 0.98), rgba(255, 190, 155, 0.92)),
    linear-gradient(145deg, #fff0e8, #ffb48f);
}

.share-card--nightfall {
  background:
    radial-gradient(circle at top right, rgba(243, 246, 255, 0.98), rgba(207, 218, 255, 0.92)),
    linear-gradient(145deg, #eef2ff, #c7d2ff);
}

.share-card--sunset {
  background:
    radial-gradient(circle at top right, rgba(255, 238, 214, 0.98), rgba(255, 219, 189, 0.92)),
    linear-gradient(145deg, #fff7ef, #ffd7bf);
}

.share-card__badge {
  display: inline-flex;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.66);
  font-size: 20rpx;
  color: $xc-accent;
}

.share-card__eyebrow {
  display: block;
  margin-top: 16rpx;
  font-size: 22rpx;
  color: $xc-accent;
}

.share-card__title {
  display: block;
  margin-top: 12rpx;
  font-size: 34rpx;
  font-weight: 700;
}

.share-card__accent {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  color: rgba(43, 33, 24, 0.7);
}

.share-card__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 16rpx;
}

.share-card__chip {
  display: inline-flex;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.62);
  font-size: 20rpx;
  color: rgba(43, 33, 24, 0.78);
}

.share-card__highlights {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  margin-top: 18rpx;
}

.share-card__line {
  display: block;
  font-size: 24rpx;
  line-height: 1.6;
  color: $xc-ink;
}

.share-card__footer {
  display: block;
  margin-top: 18rpx;
  font-size: 20rpx;
  color: rgba(43, 33, 24, 0.58);
}

.capsule-input {
  width: 100%;
  min-height: 220rpx;
  margin-top: 18rpx;
  padding: 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 249, 242, 0.96);
  border: 2rpx solid rgba(217, 111, 61, 0.1);
  font-size: 24rpx;
  line-height: 1.7;
}

.capsule-durations {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
  margin-top: 18rpx;
}

.capsule-duration {
  border-radius: 18rpx;
  background: rgba(255, 243, 231, 0.96);
  color: $xc-accent;
  font-size: 24rpx;
}

.capsule-duration--active {
  background: linear-gradient(135deg, #d96f3d, #bf5321);
  color: #fff9f3;
}

.actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.button {
  border-radius: 999rpx;
  background: linear-gradient(135deg, #d96f3d, #bf5321);
  color: #fff9f3;
}

.button--secondary {
  background: rgba(255, 255, 255, 0.92);
  color: $xc-accent;
  border: 2rpx solid rgba(217, 111, 61, 0.18);
}

.mini-button {
  margin-top: 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 238, 224, 0.92);
  color: $xc-accent;
  font-size: 24rpx;
}
</style>
