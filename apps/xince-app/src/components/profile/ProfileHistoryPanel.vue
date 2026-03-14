<script setup lang="ts">
import type { ProfileReportHistoryItem } from "@/shared/models/profile";

defineProps<{
  reports: ProfileReportHistoryItem[];
  matchReports: ProfileReportHistoryItem[];
}>();

const emit = defineEmits<{
  (event: "open-report", recordId: number): void;
}>();

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
</script>

<template>
  <view class="panel">
    <text class="panel__title">我的测试历史</text>
    <view v-if="reports.length" class="history history--timeline">
      <view
        v-for="item in reports"
        :key="item.record_id"
        class="history-card"
        @tap="emit('open-report', item.record_id)"
      >
        <view class="history-card__dot" />
        <view class="history-card__top">
          <text class="history-card__title">{{ item.test_name }}</text>
          <text class="history-card__time">{{ formatTime(item.completed_at) }}</text>
        </view>
        <text class="history-card__persona">
          {{ item.persona_name || "已生成基础结果" }} · {{ item.total_score || 0 }}分
        </text>
        <text class="history-card__footer">点击查看报告</text>
      </view>
    </view>
    <text v-else class="panel__body">你还没有可回看的历史报告。</text>
  </view>

  <view class="panel" v-if="matchReports.length">
    <text class="panel__title">我的匹配记录</text>
    <view class="history">
      <view
        v-for="item in matchReports"
        :key="`match-${item.record_id}`"
        class="match-card"
        @tap="emit('open-report', item.record_id)"
      >
        <view class="match-card__avatars">
          <text class="match-card__avatar">🧑</text>
          <text class="match-card__avatar">🧑</text>
        </view>
        <view class="match-card__body">
          <text class="match-card__title">{{ item.test_name }}</text>
          <text class="match-card__meta">
            匹配分 {{ item.total_score || 0 }} · {{ item.persona_name || "等待分析" }}
          </text>
        </view>
        <text class="match-card__tag">{{ (item.total_score || 0) >= 80 ? "高契合" : "进行中" }}</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.panel {
  margin-top: 20rpx;
  padding: 24rpx;
  border-radius: 24rpx;
  @include glass;
}

.panel__title {
  display: block;
  font-size: 30rpx;
  color: $xc-ink;
  font-weight: 600;
}

.panel__body {
  margin-top: 16rpx;
  display: block;
  font-size: 24rpx;
  color: $xc-muted;
}

.history {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.history--timeline {
  position: relative;
}

.history-card {
  position: relative;
  padding: 20rpx 20rpx 20rpx 28rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.82);
}

.history-card__dot {
  position: absolute;
  left: 10rpx;
  top: 28rpx;
  width: 10rpx;
  height: 10rpx;
  border-radius: 50%;
  background: $xc-purple;
}

.history-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.history-card__title {
  font-size: 26rpx;
  color: $xc-ink;
  font-weight: 600;
}

.history-card__time {
  font-size: 22rpx;
  color: $xc-hint;
}

.history-card__persona {
  margin-top: 8rpx;
  display: block;
  font-size: 24rpx;
  color: $xc-muted;
}

.history-card__footer {
  margin-top: 8rpx;
  display: block;
  font-size: 22rpx;
  color: $xc-purple-d;
}

.match-card {
  padding: 18rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.82);
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 14rpx;
}

.match-card__avatars {
  display: flex;
}

.match-card__avatar {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: rgba(155, 126, 216, 0.16);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  margin-left: -8rpx;
}

.match-card__avatar:first-child {
  margin-left: 0;
}

.match-card__title {
  display: block;
  font-size: 25rpx;
  color: $xc-ink;
}

.match-card__meta {
  margin-top: 4rpx;
  display: block;
  font-size: 22rpx;
  color: $xc-muted;
}

.match-card__tag {
  padding: 8rpx 12rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  color: #fff;
  background: linear-gradient(135deg, $xc-pink, $xc-purple);
}
</style>
