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

function switchTab(tab: NotificationTab) {
  if (activeTab.value === tab) {
    return;
  }
  activeTab.value = tab;
  SoundManager.haptic(10);
}
</script>

<template>
  <view class="page">
    <view class="shell">
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
        <view v-for="item in filteredNotifications" :key="item.id" class="notif-card">
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
          </view>
        </view>
      </view>

      <view v-else class="empty-card">
        <XiaoCe expression="happy" size="md" :animated="true" />
        <text class="empty-card__title">暂时没有新消息哦~</text>
        <text class="empty-card__body">新的匹配、测试结果和系统提醒都会第一时间出现在这里。</text>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 28rpx 24rpx 56rpx;
  animation: fadeInUp 0.45s $xc-ease both;
  background:
    radial-gradient(circle at top left, rgba(155, 126, 216, 0.16), transparent 28%),
    radial-gradient(circle at bottom right, rgba(124, 197, 178, 0.14), transparent 22%),
    $xc-bg;
}

.shell {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.tabs {
  display: flex;
  gap: 12rpx;
  padding: 10rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: $xc-shadow;
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

.notif-card,
.empty-card {
  @include card-base;
}

.notif-card {
  padding: 24rpx;
  display: flex;
  gap: 18rpx;
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
