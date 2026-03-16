<script setup lang="ts">
import { computed } from "vue";

import type { ProfileReportHistoryItem } from "@/shared/models/profile";

const props = defineProps<{
  reports: ProfileReportHistoryItem[];
  matchReports: ProfileReportHistoryItem[];
}>();

const emit = defineEmits<{
  (event: "open-report", recordId: number): void;
}>();

const featuredReport = computed(() => props.reports[0] || null);
const timelineReports = computed(() => props.reports.slice(1, 5));

function formatTime(value?: string | null) {
  if (!value) {
    return "暂未记录";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  const hour = `${date.getHours()}`.padStart(2, "0");
  const minute = `${date.getMinutes()}`.padStart(2, "0");
  return `${month}-${day} ${hour}:${minute}`;
}

function reportPreview(text: string) {
  if (!text) {
    return "你的这份报告已经归档，点开就能继续查看完整解读。";
  }
  return text.length > 56 ? `${text.slice(0, 56)}...` : text;
}

function reportIcon(testName: string) {
  const safe = testName.toLowerCase();
  if (safe.includes("mbti")) {
    return "🪞";
  }
  if (safe.includes("恋") || safe.includes("match")) {
    return "💞";
  }
  if (safe.includes("职业")) {
    return "💼";
  }
  if (safe.includes("九型")) {
    return "🔮";
  }
  return "✨";
}

function scoreTone(score?: number | null) {
  const safe = score || 0;
  if (safe >= 90) {
    return "高能画像";
  }
  if (safe >= 75) {
    return "稳定人格";
  }
  if (safe > 0) {
    return "基础洞察";
  }
  return "等待分析";
}

function duoLabel(score?: number | null) {
  const safe = score || 0;
  if (safe >= 92) {
    return "天作之合";
  }
  if (safe >= 82) {
    return "灵魂共振";
  }
  if (safe >= 68) {
    return "高契合";
  }
  return "继续磨合";
}
</script>

<template>
  <view class="panel">
    <view class="panel__head">
      <view>
        <text class="panel__eyebrow">REPORT ATLAS</text>
        <text class="panel__title">我的测试轨迹</text>
      </view>
      <text class="panel__meta">{{ reports.length }} 份</text>
    </view>

    <view
      v-if="featuredReport"
      class="featured-card"
      @tap="emit('open-report', featuredReport.record_id)"
    >
      <view class="featured-card__top">
        <text class="featured-card__pill">最近完成</text>
        <text class="featured-card__time">{{ formatTime(featuredReport.completed_at) }}</text>
      </view>
      <view class="featured-card__body">
        <view class="featured-card__icon">{{ reportIcon(featuredReport.test_name) }}</view>
        <view class="featured-card__copy">
          <text class="featured-card__title">{{ featuredReport.test_name }}</text>
          <text class="featured-card__persona">
            {{ featuredReport.persona_name || "基础画像已生成" }}
          </text>
          <text class="featured-card__summary">
            {{ reportPreview(featuredReport.summary) }}
          </text>
        </view>
      </view>
      <view class="featured-card__foot">
        <text class="featured-card__score">
          {{ featuredReport.total_score || 0 }} 分 · {{ scoreTone(featuredReport.total_score) }}
        </text>
        <text class="featured-card__link">查看完整报告 →</text>
      </view>
    </view>

    <view v-if="timelineReports.length" class="history">
      <view
        v-for="item in timelineReports"
        :key="item.record_id"
        class="history-card"
        @tap="emit('open-report', item.record_id)"
      >
        <view class="history-card__line" />
        <view class="history-card__icon">{{ reportIcon(item.test_name) }}</view>
        <view class="history-card__copy">
          <view class="history-card__top">
            <text class="history-card__title">{{ item.test_name }}</text>
            <text class="history-card__time">{{ formatTime(item.completed_at) }}</text>
          </view>
          <text class="history-card__persona">
            {{ item.persona_name || "基础画像已生成" }} · {{ item.total_score || 0 }} 分
          </text>
          <text class="history-card__summary">{{ reportPreview(item.summary) }}</text>
        </view>
      </view>
    </view>

    <text v-else-if="!featuredReport" class="panel__body">
      你还没有可回看的历史报告，完成一套测试后这里会变成你的档案长廊。
    </text>
  </view>

  <view class="panel panel--duo" v-if="matchReports.length">
    <view class="panel__head">
      <view>
        <text class="panel__eyebrow">DUO ARCHIVE</text>
        <text class="panel__title">我的匹配记录</text>
      </view>
      <text class="panel__meta">{{ matchReports.length }} 份</text>
    </view>

    <view class="duo-grid">
      <view
        v-for="item in matchReports"
        :key="`match-${item.record_id}`"
        class="duo-card"
        @tap="emit('open-report', item.record_id)"
      >
        <view class="duo-card__avatars">
          <text class="duo-card__avatar">🙂</text>
          <text class="duo-card__heart">❤</text>
          <text class="duo-card__avatar duo-card__avatar--alt">✨</text>
        </view>
        <text class="duo-card__title">{{ item.test_name }}</text>
        <text class="duo-card__meta">
          匹配分 {{ item.total_score || 0 }} · {{ item.persona_name || "等待分析" }}
        </text>
        <view class="duo-card__foot">
          <text class="duo-card__chip">{{ duoLabel(item.total_score) }}</text>
          <text class="duo-card__time">{{ formatTime(item.completed_at) }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.panel {
  margin-top: 20rpx;
  padding: 26rpx;
  border-radius: 30rpx;
  border: 1px solid rgba(155, 126, 216, 0.12);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 20rpx 52rpx rgba(155, 126, 216, 0.12);

  // #ifdef H5
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  // #endif
}

.panel--duo {
  background:
    radial-gradient(circle at top right, rgba(255, 232, 240, 0.6), transparent 34%),
    rgba(255, 255, 255, 0.8);
}

.panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.panel__eyebrow {
  display: block;
  font-size: 20rpx;
  letter-spacing: 4rpx;
  text-transform: uppercase;
  color: rgba(124, 93, 191, 0.52);
}

.panel__title {
  display: block;
  margin-top: 10rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: $xc-ink;
}

.panel__meta {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(124, 93, 191, 0.08);
  font-size: 20rpx;
  color: $xc-purple;
}

.panel__body {
  margin-top: 18rpx;
  display: block;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.featured-card {
  margin-top: 20rpx;
  padding: 22rpx;
  border-radius: 28rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.6), transparent 34%),
    linear-gradient(145deg, rgba(123, 100, 199, 0.12), rgba(240, 147, 183, 0.12)),
    rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(155, 126, 216, 0.12);
}

.featured-card__top,
.featured-card__foot,
.history-card__top,
.duo-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.featured-card__pill {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(124, 93, 191, 0.1);
  font-size: 20rpx;
  color: $xc-purple;
}

.featured-card__time,
.history-card__time,
.duo-card__time {
  font-size: 20rpx;
  color: $xc-hint;
}

.featured-card__body {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 16rpx;
}

.featured-card__icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.84);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 38rpx;
}

.featured-card__copy {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.featured-card__title,
.history-card__title,
.duo-card__title {
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-ink;
}

.featured-card__persona,
.history-card__persona,
.duo-card__meta {
  font-size: 22rpx;
  color: $xc-purple-d;
}

.featured-card__summary,
.history-card__summary {
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.featured-card__foot {
  margin-top: 18rpx;
}

.featured-card__score {
  font-size: 22rpx;
  color: $xc-ink;
}

.featured-card__link {
  font-size: 22rpx;
  color: $xc-purple-d;
  font-weight: 600;
}

.history {
  position: relative;
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.history-card {
  position: relative;
  padding: 18rpx 18rpx 18rpx 104rpx;
  min-height: 124rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.82);
}

.history-card__line {
  position: absolute;
  left: 54rpx;
  top: 0;
  bottom: 0;
  width: 2rpx;
  background: linear-gradient(180deg, rgba(155, 126, 216, 0.1), rgba(232, 114, 154, 0.12));
}

.history-card__icon {
  position: absolute;
  left: 26rpx;
  top: 22rpx;
  width: 56rpx;
  height: 56rpx;
  border-radius: 18rpx;
  background: rgba(155, 126, 216, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
}

.history-card__copy {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.duo-grid {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.duo-card {
  padding: 20rpx;
  border-radius: 26rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.52), transparent 34%),
    linear-gradient(150deg, rgba(232, 114, 154, 0.12), rgba(123, 100, 199, 0.1)),
    rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(232, 114, 154, 0.12);
}

.duo-card__avatars {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.duo-card__avatar,
.duo-card__heart {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.duo-card__avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.84);
  font-size: 24rpx;
}

.duo-card__avatar--alt {
  background: rgba(255, 243, 247, 0.9);
}

.duo-card__heart {
  width: 26rpx;
  color: $xc-pink;
  font-size: 18rpx;
}

.duo-card__title {
  display: block;
  margin-top: 18rpx;
}

.duo-card__meta {
  display: block;
  margin-top: 8rpx;
  line-height: 1.6;
}

.duo-card__foot {
  margin-top: 18rpx;
}

.duo-card__chip {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(232, 114, 154, 0.1);
  font-size: 19rpx;
  color: #b24b70;
}
</style>
