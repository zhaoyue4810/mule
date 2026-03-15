<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { onShow } from "@dcloudio/uni-app";

import XiaoCe from "./XiaoCe.vue";

const TAB_BUDDY_LAST_INDEX_KEY = "xc_tab_buddy_last_index";
const TAB_COUNT = 4;

const tabIndex = ref(0);
const startIndex = ref(0);
const ready = ref(false);
const buddyAnimClass = ref("");
let hopInterval: ReturnType<typeof setInterval> | null = null;
let bounceTimeout: ReturnType<typeof setTimeout> | null = null;

const expression = computed(() => {
  if (tabIndex.value === 0) {
    return "happy";
  }
  if (tabIndex.value === 1) {
    return "thinking";
  }
  if (tabIndex.value === 2) {
    return "love";
  }
  return "default";
});

const left = computed(() => {
  const active = ready.value ? tabIndex.value : startIndex.value;
  return `calc(${((active + 0.5) / TAB_COUNT) * 100}% - 12px)`;
});

function routeToIndex(route: string) {
  if (route.includes("/pages/home/index")) {
    return 0;
  }
  if (route.includes("/pages/discover/index")) {
    return 1;
  }
  if (route.includes("/pages/match/index")) {
    return 2;
  }
  return 3;
}

function syncActiveTab() {
  const pages = getCurrentPages();
  const current = pages[pages.length - 1];
  const route = current?.route ? `/${current.route}` : "";
  const active = routeToIndex(route);
  tabIndex.value = active;
  const cached = Number(uni.getStorageSync(TAB_BUDDY_LAST_INDEX_KEY));
  startIndex.value = Number.isFinite(cached) ? Math.max(0, Math.min(3, cached)) : active;
  uni.setStorageSync(TAB_BUDDY_LAST_INDEX_KEY, active);
}

function triggerBounce() {
  buddyAnimClass.value = "buddy-bouncing";
  if (bounceTimeout) {
    clearTimeout(bounceTimeout);
  }
  bounceTimeout = setTimeout(() => {
    buddyAnimClass.value = "";
  }, 600);
}

function scheduleHop() {
  if (hopInterval) {
    clearInterval(hopInterval);
  }
  hopInterval = setInterval(() => {
    triggerBounce();
  }, 15000);
}

watch(tabIndex, (value, previous) => {
  if (!ready.value || value === previous) {
    return;
  }
  triggerBounce();
});

onMounted(() => {
  syncActiveTab();
  nextTick(() => {
    ready.value = true;
  });
  scheduleHop();
});

onShow(() => {
  syncActiveTab();
  nextTick(() => {
    ready.value = true;
  });
});

onBeforeUnmount(() => {
  if (hopInterval) {
    clearInterval(hopInterval);
  }
  if (bounceTimeout) {
    clearTimeout(bounceTimeout);
  }
});
</script>

<template>
  <view class="tab-buddy" :class="buddyAnimClass" :style="{ left }">
    <XiaoCe :expression="expression" size="sm" :animated="true" />
  </view>
</template>

<style lang="scss" scoped>
.tab-buddy {
  position: fixed;
  bottom: calc(68px + env(safe-area-inset-bottom, 0px) + 8rpx);
  z-index: 110;
  transition: left 0.3s $xc-ease;
  pointer-events: none;
}

.buddy-bouncing {
  animation: buddyBounce 0.6s ease;
}

@keyframes buddyBounce {
  0% {
    transform: translateY(0);
  }
  25% {
    transform: translateY(-12rpx);
  }
  45% {
    transform: translateY(0);
  }
  60% {
    transform: translateY(-6rpx);
  }
  75% {
    transform: translateY(0);
  }
  85% {
    transform: translateY(-2rpx);
  }
  100% {
    transform: translateY(0);
  }
}
</style>
