<script setup lang="ts">
import type { ProfileBadgeItem } from "@/shared/models/profile";

defineProps<{
  soloBadges: ProfileBadgeItem[];
  duoBadges: ProfileBadgeItem[];
  showDuoHint: boolean;
}>();

const emit = defineEmits<{
  (event: "open-badge", item: ProfileBadgeItem): void;
}>();

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
  const hour = `${date.getHours()}`.padStart(2, "0");
  const minute = `${date.getMinutes()}`.padStart(2, "0");
  return `${month}-${day} ${hour}:${minute}`;
}
</script>

<template>
  <view class="panel" v-if="soloBadges.length">
    <text class="panel__title">个人成就徽章</text>
    <view class="badge-grid">
      <view
        v-for="item in soloBadges"
        :key="item.badge_key"
        class="badge-card"
        :class="badgeTierClass(item.tier)"
        @tap="emit('open-badge', item)"
      >
        <text class="badge-card__emoji">{{ item.emoji }}</text>
        <text class="badge-card__name">{{ item.name }}</text>
        <text class="badge-card__tier">{{ badgeTierLabel(item.tier) }}阶 · {{ item.unlock_count }} 次</text>
        <text class="badge-card__time">{{ formatTime(item.unlocked_at) }}</text>
      </view>
    </view>
  </view>

  <view class="panel" v-if="duoBadges.length || showDuoHint">
    <text class="panel__title">双人徽章</text>
    <text class="panel__body" v-if="!duoBadges.length">参与更多匹配测试即可点亮双人徽章。</text>
    <view v-else class="badge-grid">
      <view
        v-for="item in duoBadges"
        :key="`duo-${item.badge_key}`"
        class="badge-card badge-card--duo"
        :class="badgeTierClass(item.tier)"
        @tap="emit('open-badge', item)"
      >
        <text class="badge-card__emoji">{{ item.emoji }}</text>
        <text class="badge-card__name">{{ item.name }}</text>
        <text class="badge-card__tier">{{ badgeTierLabel(item.tier) }}阶 · {{ item.unlock_count }} 次</text>
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

.badge-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.badge-card {
  border-radius: 20rpx;
  padding: 16rpx 12rpx;
  background: rgba(255, 255, 255, 0.85);
  border: 2rpx solid rgba(155, 126, 216, 0.16);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6rpx;
  text-align: center;
}

.badge-card__emoji {
  font-size: 36rpx;
}

.badge-card__name {
  font-size: 22rpx;
  color: $xc-ink;
}

.badge-card__tier,
.badge-card__time {
  font-size: 20rpx;
  color: $xc-muted;
}

.badge-card--duo {
  border-color: rgba(232, 114, 154, 0.22);
}

.badge-card--t1 {
  box-shadow: 0 8rpx 16rpx rgba(205, 127, 50, 0.14);
}

.badge-card--t2 {
  box-shadow: 0 8rpx 16rpx rgba(192, 192, 192, 0.2);
}

.badge-card--t3 {
  box-shadow: 0 10rpx 22rpx rgba(212, 168, 83, 0.24);
}

.badge-card--t4 {
  box-shadow: 0 12rpx 24rpx rgba(185, 242, 255, 0.3);
}
</style>
