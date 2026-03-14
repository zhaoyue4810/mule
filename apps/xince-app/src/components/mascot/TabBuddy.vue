<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import XiaoCe from "./XiaoCe.vue";

const TAB_BUDDY_LAST_INDEX_KEY = "xc_tab_buddy_last_index";
const TAB_COUNT = 4;

const tabIndex = ref(0);
const startIndex = ref(0);
const ready = ref(false);
const hopping = ref(false);
let hopInterval: ReturnType<typeof setInterval> | null = null;
let hopTimeout: ReturnType<typeof setTimeout> | null = null;

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

function scheduleHop() {
  if (hopInterval) {
    clearInterval(hopInterval);
  }
  hopInterval = setInterval(() => {
    hopping.value = true;
    if (hopTimeout) {
      clearTimeout(hopTimeout);
    }
    hopTimeout = setTimeout(() => {
      hopping.value = false;
    }, 700);
  }, 15000);
}

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
  if (hopTimeout) {
    clearTimeout(hopTimeout);
  }
});
</script>

<template>
  <view class="tab-buddy" :class="{ 'tab-buddy--hop': hopping }" :style="{ left }">
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

.tab-buddy--hop {
  animation: tabBuddyHop 0.65s $xc-spring both;
}

@keyframes tabBuddyHop {
  0%,
  100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-9px);
  }
}
</style>
