<script setup lang="ts">
import { computed } from "vue";

import type { ProfileBadgeItem } from "@/shared/models/profile";

const props = defineProps<{
  soloBadges: ProfileBadgeItem[];
  duoBadges: ProfileBadgeItem[];
  showDuoHint: boolean;
}>();

const emit = defineEmits<{
  (event: "open-badge", item: ProfileBadgeItem): void;
}>();

const soloTotalUnlock = computed(() =>
  props.soloBadges.reduce((total, item) => total + item.unlock_count, 0),
);

const duoTotalUnlock = computed(() =>
  props.duoBadges.reduce((total, item) => total + item.unlock_count, 0),
);

function badgeTierClass(tier: number) {
  const safe = Math.max(1, Math.min(4, tier || 1));
  return `badge-card--t${safe}`;
}

function badgeTierLabel(tier: number) {
  return ["铜", "银", "金", "钻"][Math.max(0, Math.min(3, tier - 1))] || "铜";
}

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
  return `${month}-${day}`;
}
</script>

<template>
  <view class="panel" v-if="soloBadges.length">
    <view class="panel__head">
      <view>
        <text class="panel__eyebrow">BADGE VAULT</text>
        <text class="panel__title">个人成就徽章</text>
      </view>
      <view class="panel__summary">
        <text class="panel__summary-value">{{ soloBadges.length }}</text>
        <text class="panel__summary-label">枚</text>
      </view>
    </view>

    <text class="panel__body">
      已累计解锁 {{ soloTotalUnlock }} 次成就，所有勋章都可以点开查看阶位和获得时间。
    </text>

    <view class="badge-grid">
      <view
        v-for="item in soloBadges"
        :key="item.badge_key"
        class="badge-card"
        :class="badgeTierClass(item.tier)"
        @tap="emit('open-badge', item)"
      >
        <view class="badge-card__halo" />
        <text class="badge-card__emoji">{{ item.emoji }}</text>
        <text class="badge-card__name">{{ item.name }}</text>
        <text class="badge-card__tier">{{ badgeTierLabel(item.tier) }}阶探索者</text>
        <text class="badge-card__count">累计 {{ item.unlock_count }} 次</text>
        <text class="badge-card__time">{{ formatTime(item.unlocked_at) }}</text>
      </view>
    </view>
  </view>

  <view class="panel panel--duo" v-if="duoBadges.length || showDuoHint">
    <view class="panel__head">
      <view>
        <text class="panel__eyebrow">DUO TROPHIES</text>
        <text class="panel__title">双人徽章</text>
      </view>
      <view class="panel__summary">
        <text class="panel__summary-value">{{ duoBadges.length }}</text>
        <text class="panel__summary-label">枚</text>
      </view>
    </view>

    <text v-if="!duoBadges.length" class="panel__body">
      已经有匹配记录了，继续完成更多双人测试就会点亮第一枚双人纪念徽章。
    </text>

    <text v-else class="panel__body">
      你们已经累计解锁 {{ duoTotalUnlock }} 次双人成就，越高阶的徽章越稀有。
    </text>

    <view v-if="duoBadges.length" class="duo-grid">
      <view
        v-for="item in duoBadges"
        :key="`duo-${item.badge_key}`"
        class="duo-card"
        :class="badgeTierClass(item.tier)"
        @tap="emit('open-badge', item)"
      >
        <text class="duo-card__emoji">{{ item.emoji }}</text>
        <text class="duo-card__name">{{ item.name }}</text>
        <text class="duo-card__tier">{{ badgeTierLabel(item.tier) }}阶关系勋章</text>
        <view class="duo-card__foot">
          <text class="duo-card__count">累计 {{ item.unlock_count }} 次</text>
          <text class="duo-card__time">{{ formatTime(item.unlocked_at) }}</text>
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
    radial-gradient(circle at top right, rgba(255, 234, 241, 0.58), transparent 34%),
    rgba(255, 255, 255, 0.8);
}

.panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14rpx;
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

.panel__summary {
  min-width: 86rpx;
  padding: 10rpx 14rpx;
  border-radius: 20rpx;
  background: rgba(124, 93, 191, 0.08);
  text-align: center;
}

.panel__summary-value {
  display: block;
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-purple-d;
}

.panel__summary-label {
  display: block;
  margin-top: 2rpx;
  font-size: 18rpx;
  color: $xc-muted;
}

.panel__body {
  margin-top: 16rpx;
  display: block;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.badge-grid {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.badge-card {
  position: relative;
  overflow: hidden;
  min-height: 228rpx;
  padding: 22rpx 18rpx 18rpx;
  border-radius: 28rpx;
  border: 1px solid rgba(155, 126, 216, 0.12);
  background: rgba(255, 255, 255, 0.84);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-end;
  gap: 8rpx;
}

.badge-card__halo {
  position: absolute;
  top: -26rpx;
  right: -12rpx;
  width: 132rpx;
  height: 132rpx;
  border-radius: 50%;
  opacity: 0.22;
}

.badge-card__emoji {
  position: absolute;
  top: 20rpx;
  left: 18rpx;
  font-size: 42rpx;
}

.badge-card__name {
  position: relative;
  font-size: 25rpx;
  line-height: 1.45;
  color: $xc-ink;
  font-weight: 700;
}

.badge-card__tier,
.badge-card__count,
.badge-card__time,
.duo-card__tier,
.duo-card__count,
.duo-card__time {
  position: relative;
  font-size: 20rpx;
  line-height: 1.5;
  color: $xc-muted;
}

.duo-grid {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.duo-card {
  position: relative;
  overflow: hidden;
  min-height: 196rpx;
  padding: 20rpx 18rpx;
  border-radius: 26rpx;
  border: 1px solid rgba(232, 114, 154, 0.12);
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.6), transparent 34%),
    linear-gradient(155deg, rgba(232, 114, 154, 0.12), rgba(123, 100, 199, 0.1)),
    rgba(255, 255, 255, 0.86);
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.duo-card__emoji {
  font-size: 40rpx;
}

.duo-card__name {
  font-size: 24rpx;
  line-height: 1.45;
  color: $xc-ink;
  font-weight: 700;
}

.duo-card__foot {
  margin-top: auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.badge-card--t1 .badge-card__halo,
.badge-card--t1.duo-card::before {
  background: radial-gradient(circle, rgba(205, 127, 50, 0.56), transparent 72%);
}

.badge-card--t2 .badge-card__halo,
.badge-card--t2.duo-card::before {
  background: radial-gradient(circle, rgba(168, 178, 198, 0.56), transparent 72%);
}

.badge-card--t3 .badge-card__halo,
.badge-card--t3.duo-card::before {
  background: radial-gradient(circle, rgba(228, 179, 73, 0.6), transparent 72%);
}

.badge-card--t4 .badge-card__halo,
.badge-card--t4.duo-card::before {
  background: radial-gradient(circle, rgba(127, 216, 255, 0.6), transparent 72%);
}

.duo-card::before {
  content: "";
  position: absolute;
  top: -32rpx;
  right: -18rpx;
  width: 132rpx;
  height: 132rpx;
  border-radius: 50%;
  opacity: 0.2;
}
</style>
