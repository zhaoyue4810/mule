<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import type { PublishedTestSummary } from "@/shared/models/tests";
import { useTestCatalogStore } from "@/stores/test-catalog";
import { SoundManager } from "@/shared/utils/sound-manager";

const SEARCH_HISTORY_KEY = "xc_search_history";
const HOT_TAGS = ["MBTI", "大五人格", "恋爱风格", "BFF 匹配", "九型人格", "职场性格"];

const catalog = useTestCatalogStore();
const loading = ref(false);
const keyword = ref("");
const searchHistory = ref<string[]>([]);
const searched = ref(false);

const tests = computed(() => catalog.tests);
const results = computed(() => {
  const query = keyword.value.trim().toLowerCase();
  if (!query) {
    return [] as PublishedTestSummary[];
  }
  return tests.value.filter((item) => {
    const title = item.name.toLowerCase();
    const category = item.category.toLowerCase();
    return title.includes(query) || category.includes(query);
  });
});

function fallbackGradient(index: number) {
  const gradients = [
    "linear-gradient(135deg, #EDE5F9, #FDE6EF)",
    "linear-gradient(135deg, #FFF4D7, #F8D9C8)",
    "linear-gradient(135deg, #E2F5EF, #EDE5F9)",
  ];
  return gradients[index % gradients.length];
}

function readHistory() {
  const stored = uni.getStorageSync(SEARCH_HISTORY_KEY);
  searchHistory.value = Array.isArray(stored)
    ? stored.filter((item): item is string => typeof item === "string" && item.trim().length > 0)
    : [];
}

function writeHistory(value: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    return;
  }
  const next = [trimmed, ...searchHistory.value.filter((item) => item !== trimmed)].slice(0, 10);
  searchHistory.value = next;
  uni.setStorageSync(SEARCH_HISTORY_KEY, next);
}

async function loadTests() {
  loading.value = true;
  try {
    await catalog.loadTests();
  } catch (error) {
    uni.showToast({
      title: error instanceof Error ? error.message : "搜索数据加载失败",
      icon: "none",
    });
  } finally {
    loading.value = false;
  }
}

function submitSearch(raw?: string) {
  const next = typeof raw === "string" ? raw : keyword.value;
  keyword.value = next.trim();
  searched.value = Boolean(keyword.value);
  if (keyword.value) {
    writeHistory(keyword.value);
    if (SoundManager.isSoundEnabled()) {
      SoundManager.play("ding");
    }
  }
}

function useHistory(item: string) {
  keyword.value = item;
  submitSearch(item);
}

function clearHistory() {
  searchHistory.value = [];
  uni.removeStorageSync(SEARCH_HISTORY_KEY);
}

function goBack() {
  const pages = getCurrentPages();
  if (pages.length > 1) {
    uni.navigateBack({ delta: 1 });
    return;
  }
  uni.switchTab({ url: "/pages/discover/index" });
}

function openDetail(testCode: string) {
  if (!testCode) {
    return;
  }
  uni.navigateTo({
    url: `/pages/test/detail?testCode=${testCode}`,
  });
}

function openHotTag(tag: string) {
  keyword.value = tag;
  submitSearch(tag);
  const matched = results.value[0];
  if (matched) {
    openDetail(matched.test_code);
    return;
  }
  uni.showToast({
    title: "暂时没有对应测试",
    icon: "none",
  });
}

onMounted(() => {
  readHistory();
  void loadTests();
});
</script>

<template>
  <view class="page">
    <view class="shell">
      <view class="search-bar">
        <view class="search-bar__input-wrap">
          <text class="search-bar__icon">🔍</text>
          <input
            v-model.trim="keyword"
            class="search-bar__input"
            confirm-type="search"
            focus
            placeholder="搜索测试、分类或灵感关键词"
            @confirm="submitSearch()"
          />
        </view>
        <text class="search-bar__cancel" @tap="goBack">取消</text>
      </view>

      <view v-if="searchHistory.length" class="card">
        <view class="section-head">
          <text class="section-head__title">搜索历史</text>
          <text class="section-head__action" @tap="clearHistory">清除</text>
        </view>
        <view class="tag-wrap">
          <text v-for="item in searchHistory" :key="item" class="tag" @tap="useHistory(item)">
            {{ item }}
          </text>
        </view>
      </view>

      <view class="card">
        <view class="section-head">
          <text class="section-head__title">热门搜索</text>
        </view>
        <view class="tag-wrap">
          <text v-for="item in HOT_TAGS" :key="item" class="tag tag--hot" @tap="openHotTag(item)">
            {{ item }}
          </text>
        </view>
      </view>

      <view class="card">
        <view class="section-head">
          <text class="section-head__title">搜索结果</text>
          <text v-if="searched && keyword" class="section-head__meta">“{{ keyword }}”</text>
        </view>

        <view v-if="loading" class="placeholder">
          <text>正在整理测试目录...</text>
        </view>
        <view v-else-if="searched && results.length === 0" class="placeholder">
          <text>没有找到相关测试</text>
        </view>
        <view v-else-if="searched" class="result-list">
          <view
            v-for="(item, index) in results"
            :key="item.test_code"
            class="result-card"
            :style="{ background: item.cover_gradient || fallbackGradient(index) }"
            @tap="openDetail(item.test_code)"
          >
            <view class="result-card__top">
              <text class="result-card__category">{{ item.category }}</text>
              <text class="result-card__meta">{{ item.participant_count }} 人参与</text>
            </view>
            <text class="result-card__title">{{ item.name }}</text>
            <text class="result-card__desc">{{ item.question_count }} 题 · {{ item.duration_hint || "约 5 分钟" }}</text>
          </view>
        </view>
        <view v-else class="placeholder">
          <text>输入关键词后，这里会出现匹配的测试。</text>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.page {
  min-height: 100vh;
  padding: 24rpx;
  animation: fadeInUp 0.45s $xc-ease both;
  background:
    radial-gradient(circle at top, rgba(155, 126, 216, 0.16), transparent 28%),
    radial-gradient(circle at bottom right, rgba(232, 114, 154, 0.14), transparent 24%),
    $xc-bg;
}

.shell {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.search-bar__input-wrap,
.card {
  @include card-base;
}

.search-bar__input-wrap {
  flex: 1;
  padding: 18rpx 20rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.search-bar__icon {
  font-size: 28rpx;
}

.search-bar__input {
  flex: 1;
  font-size: 26rpx;
}

.search-bar__cancel {
  font-size: 26rpx;
  color: $xc-purple-d;
  font-weight: 600;
}

.card {
  padding: 26rpx;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.section-head__title {
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-ink;
}

.section-head__action,
.section-head__meta {
  font-size: 22rpx;
  color: $xc-muted;
}

.tag-wrap {
  margin-top: 16rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.tag {
  padding: 12rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(248, 246, 255, 0.95);
  color: $xc-purple-d;
  font-size: 23rpx;
}

.tag--hot {
  background: linear-gradient(135deg, rgba(237, 229, 249, 0.92), rgba(253, 230, 239, 0.92));
}

.placeholder {
  min-height: 180rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-size: 24rpx;
  color: $xc-muted;
}

.result-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.result-card {
  padding: 24rpx;
  border-radius: 28rpx;
  box-shadow: 0 18rpx 36rpx rgba(123, 110, 133, 0.08);
}

.result-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.result-card__category {
  font-size: 22rpx;
  color: rgba(67, 49, 141, 0.82);
}

.result-card__meta {
  font-size: 21rpx;
  color: rgba(123, 110, 133, 0.75);
}

.result-card__title {
  display: block;
  margin-top: 14rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.result-card__desc {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  color: rgba(67, 49, 141, 0.72);
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
