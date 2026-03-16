<script setup lang="ts">
import { computed, ref } from "vue";

import XiaoCe from "@/components/mascot/XiaoCe.vue";
import { SoundManager } from "@/shared/utils/sound-manager";

type NotificationTab = "all" | "match" | "result" | "system";
type NotificationItem = {
  id: number;
  type: "match" | "result" | "badge" | "system";
  title: string;
  summary: string;
  time: string;
  unread: boolean;
};

const tabs: Array<{ key: NotificationTab; label: string }> = [
  { key: "all", label: "全部" },
  { key: "match", label: "匹配" },
  { key: "result", label: "测试" },
  { key: "system", label: "系统" },
];

const activeTab = ref<NotificationTab>("all");

const notifications = ref<NotificationItem[]>([
  {
    id: 1,
    type: "match",
    title: "你的灵魂搭子已经就位",
    summary: "对方刚完成配对测试，新的双人报告现在可以查看了。",
    time: "刚刚",
    unread: true,
  },
  {
    id: 2,
    type: "result",
    title: "报告已生成",
    summary: "《恋爱风格实验室》更新了你最新的人格画像和关键词卡片。",
    time: "10 分钟前",
    unread: true,
  },
  {
    id: 3,
    type: "badge",
    title: "新徽章已点亮",
    summary: "你解锁了“连续探索者”徽章，记得去个人页看看。",
    time: "今天 09:20",
    unread: false,
  },
  {
    id: 4,
    type: "system",
    title: "本周灵魂提问上线",
    summary: "小测准备了新的每日提问，打开首页就能继续记录心情。",
    time: "昨天",
    unread: false,
  },
  {
    id: 5,
    type: "match",
    title: "好友邀请你一起测试",
    summary: "新的 BFF 匹配邀请正在等待你，看看你们的默契能到几分。",
    time: "周四",
    unread: false,
  },
  {
    id: 6,
    type: "system",
    title: "发现页灵感更新",
    summary: "本周新增了星座内容和灵魂故事精选，可以去逛逛。",
    time: "周二",
    unread: false,
  },
]);

const unreadCount = computed(() => notifications.value.filter((item) => item.unread).length);
const heroSummary = computed(() =>
  unreadCount.value
    ? `当前有 ${unreadCount.value} 条需要优先查看的新消息。`
    : "当前消息都已经处理完了，可以安心去继续测试或匹配。",
);
const notificationStats = computed(() => [
  {
    label: "未读",
    value: `${unreadCount.value}`,
    emoji: "📬",
  },
  {
    label: "匹配提醒",
    value: `${notifications.value.filter((item) => item.type === "match").length}`,
    emoji: "💕",
  },
  {
    label: "系统动态",
    value: `${notifications.value.filter((item) => item.type === "system").length}`,
    emoji: "🪄",
  },
]);

const filteredNotifications = computed(() => {
  if (activeTab.value === "all") {
    return notifications.value;
  }
  if (activeTab.value === "result") {
    return notifications.value.filter((item) => item.type === "result" || item.type === "badge");
  }
  return notifications.value.filter((item) => item.type === activeTab.value);
});

function getIcon(type: NotificationItem["type"]) {
  if (type === "match") {
    return "💕";
  }
  if (type === "result") {
    return "📊";
  }
  if (type === "badge") {
    return "🏅";
  }
  return "🔔";
}

function getTypeLabel(type: NotificationItem["type"]) {
  if (type === "match") {
    return "匹配";
  }
  if (type === "result") {
    return "测试";
  }
  if (type === "badge") {
    return "勋章";
  }
  return "系统";
}

function switchTab(tab: NotificationTab) {
  if (activeTab.value === tab) {
    return;
  }
  activeTab.value = tab;
  SoundManager.haptic(10);
}

function markAllRead() {
  if (!unreadCount.value) {
    return;
  }
  notifications.value = notifications.value.map((item) => ({
    ...item,
    unread: false,
  }));
  SoundManager.haptic(12);
  uni.showToast({
    title: "已全部标记为已读",
    icon: "success",
  });
}

function openNotification(item: NotificationItem) {
  notifications.value = notifications.value.map((entry) =>
    entry.id === item.id ? { ...entry, unread: false } : entry,
  );
  SoundManager.haptic(8);
  uni.showToast({
    title: `${item.title}`,
    icon: "none",
  });
}
</script>

<template>
  <view class="page">
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--mint" />
    <view class="shell">
      <view class="hero-card">
        <view class="hero-card__top">
          <view>
            <text class="hero-card__eyebrow">MESSAGE CENTER</text>
            <text class="hero-card__title">通知</text>
            <text class="hero-card__body">{{ heroSummary }}</text>
          </view>
          <view class="hero-card__badge">
            <text class="hero-card__badge-value">{{ unreadCount }}</text>
            <text class="hero-card__badge-label">未读</text>
          </view>
        </view>
        <view class="hero-card__actions">
          <button class="hero-card__button" :disabled="!unreadCount" @tap="markAllRead">全部标记已读</button>
          <text class="hero-card__hint">消息会汇总匹配、报告、勋章和系统动态。</text>
        </view>
      </view>

      <view class="stats">
        <view v-for="item in notificationStats" :key="item.label" class="stat-card">
          <text class="stat-card__emoji">{{ item.emoji }}</text>
          <text class="stat-card__value">{{ item.value }}</text>
          <text class="stat-card__label">{{ item.label }}</text>
        </view>
      </view>

      <view class="tabs">
        <text
          v-for="item in tabs"
          :key="item.key"
          class="tabs__item"
          :class="{ 'tabs__item--active': activeTab === item.key }"
          @tap="switchTab(item.key)"
        >
          {{ item.label }}
        </text>
      </view>

      <view v-if="filteredNotifications.length" class="list">
        <view
          v-for="item in filteredNotifications"
          :key="item.id"
          class="notif-card"
          :class="{ 'notif-card--unread': item.unread }"
          @tap="openNotification(item)"
        >
          <view class="notif-card__icon">
            <text>{{ getIcon(item.type) }}</text>
          </view>
          <view class="notif-card__body">
            <view class="notif-card__top">
              <view class="notif-card__title-wrap">
                <view v-if="item.unread" class="notif-card__dot" />
                <text class="notif-card__title">{{ item.title }}</text>
              </view>
              <text class="notif-card__time">{{ item.time }}</text>
            </view>
            <text class="notif-card__summary">{{ item.summary }}</text>
            <view class="notif-card__footer">
              <text class="notif-card__tag">{{ getTypeLabel(item.type) }}</text>
              <text class="notif-card__state">{{ item.unread ? "待查看" : "已查看" }}</text>
            </view>
          </view>
        </view>
      </view>

      <view v-else class="empty-card">
        <XiaoCe expression="happy" size="md" :animated="true" />
        <text class="empty-card__title">暂时没有新消息</text>
        <text class="empty-card__body">新的匹配、测试结果和系统提醒都会第一时间出现在这里。</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 28rpx 24rpx 56rpx;
  background:
    radial-gradient(circle at top left, rgba(155, 126, 216, 0.16), transparent 28%),
    radial-gradient(circle at bottom right, rgba(124, 197, 178, 0.14), transparent 22%),
    $xc-bg;
}

.page__glow {
  position: absolute;
  width: 420rpx;
  height: 420rpx;
  border-radius: 50%;
  filter: blur(32px);
  opacity: 0.42;
  pointer-events: none;
}

.page__glow--violet {
  top: -120rpx;
  right: -120rpx;
  background: rgba(155, 126, 216, 0.2);
}

.page__glow--mint {
  left: -120rpx;
  bottom: 220rpx;
  background: rgba(124, 197, 178, 0.16);
}

.shell {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  animation: fadeInUp 0.45s $xc-ease both;
}

.hero-card,
.notif-card,
.empty-card,
.tabs,
.stat-card {
  @include card-base;
}

.hero-card {
  padding: 28rpx;
}

.hero-card__top {
  display: flex;
  gap: 18rpx;
  align-items: flex-start;
  justify-content: space-between;
}

.hero-card__eyebrow {
  display: block;
  font-size: 20rpx;
  font-weight: 700;
  letter-spacing: 2.8rpx;
  color: rgba(123, 110, 133, 0.76);
}

.hero-card__title {
  display: block;
  margin-top: 10rpx;
  font-size: 40rpx;
  font-weight: 800;
  color: $xc-ink;
}

.hero-card__body {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.hero-card__badge {
  min-width: 132rpx;
  padding: 18rpx 16rpx;
  border-radius: 24rpx;
  text-align: center;
  background:
    linear-gradient(145deg, rgba(255, 248, 242, 0.96), rgba(246, 240, 255, 0.9));
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.hero-card__badge-value {
  display: block;
  font-size: 34rpx;
  font-weight: 800;
  color: $xc-accent;
}

.hero-card__badge-label {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  color: $xc-muted;
}

.hero-card__actions {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 18rpx;
}

.hero-card__button {
  height: 84rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  color: $xc-white;
  font-size: 26rpx;
  font-weight: 700;
}

.hero-card__hint {
  font-size: 22rpx;
  color: $xc-muted;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.stat-card {
  padding: 20rpx 16rpx;
  text-align: center;
}

.stat-card__emoji {
  display: block;
  font-size: 28rpx;
}

.stat-card__value {
  display: block;
  margin-top: 10rpx;
  font-size: 32rpx;
  font-weight: 800;
  color: $xc-accent;
}

.stat-card__label {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  color: $xc-muted;
}

.tabs {
  display: flex;
  gap: 12rpx;
  padding: 10rpx;
}

.tabs__item {
  flex: 1;
  padding: 16rpx 0;
  border-radius: 999rpx;
  text-align: center;
  font-size: 24rpx;
  color: $xc-muted;
  transition: all 0.28s $xc-ease;
}

.tabs__item--active {
  color: $xc-white;
  background: linear-gradient(135deg, $xc-purple, $xc-pink);
  box-shadow: 0 14rpx 28rpx rgba(155, 126, 216, 0.18);
}

.list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.notif-card {
  padding: 24rpx;
  display: flex;
  gap: 18rpx;
}

.notif-card--unread {
  box-shadow: 0 18rpx 36rpx rgba(155, 126, 216, 0.14);
}

.notif-card__icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 24rpx;
  background: rgba(248, 246, 255, 0.92);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  flex-shrink: 0;
}

.notif-card__body {
  flex: 1;
}

.notif-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12rpx;
}

.notif-card__title-wrap {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex: 1;
}

.notif-card__dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: $xc-purple;
  box-shadow: 0 0 0 6rpx rgba(155, 126, 216, 0.12);
}

.notif-card__title {
  flex: 1;
  font-size: 27rpx;
  font-weight: 700;
  color: $xc-ink;
}

.notif-card__time {
  font-size: 21rpx;
  color: rgba(123, 110, 133, 0.76);
}

.notif-card__summary {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.notif-card__footer {
  display: flex;
  gap: 10rpx;
  margin-top: 16rpx;
}

.notif-card__tag,
.notif-card__state {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
}

.notif-card__tag {
  background: rgba(155, 126, 216, 0.12);
  color: $xc-purple;
}

.notif-card__state {
  background: rgba(255, 242, 231, 0.96);
  color: $xc-muted;
}

.empty-card {
  min-height: 420rpx;
  padding: 38rpx 30rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-card__title {
  margin-top: 18rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.empty-card__body {
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(16rpx);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
