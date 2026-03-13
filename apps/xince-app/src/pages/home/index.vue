<script setup lang="ts">
import { computed, onMounted } from "vue";

import { useTestCatalogStore } from "@/stores/test-catalog";

const store = useTestCatalogStore();

const tests = computed(() => store.tests);
const loading = computed(() => store.loading);
const error = computed(() => store.error);

async function load() {
  try {
    await store.loadTests();
  } catch (err) {
    console.error(err);
  }
}

function openDetail(testCode: string) {
  uni.navigateTo({
    url: `/pages/test/detail?testCode=${testCode}`,
  });
}

onMounted(() => {
  load();
});
</script>

<template>
  <view class="page">
    <view class="hero">
      <text class="hero__eyebrow">Published Tests</text>
      <text class="hero__title">把已经上线的测试内容，变成真正能跑的用户入口。</text>
      <text class="hero__body">
        当前首页直接读取后端已发布版本，前台不会误吃到草稿内容。
      </text>
    </view>

    <view class="section-head">
      <text class="section-head__title">线上测试</text>
      <text class="section-head__meta">{{ tests.length }} 个可用</text>
    </view>

    <view v-if="loading" class="panel">
      <text class="panel__text">正在加载已发布测试...</text>
    </view>

    <view v-else-if="error" class="panel panel--error">
      <text class="panel__text">{{ error }}</text>
      <button class="panel__button" @tap="load">重新加载</button>
    </view>

    <view v-else-if="tests.length === 0" class="panel">
      <text class="panel__text">当前还没有发布内容，请先在后台发布至少一个测试版本。</text>
    </view>

    <view v-else class="cards">
      <view
        v-for="item in tests"
        :key="item.test_code"
        class="card"
        @tap="openDetail(item.test_code)"
      >
        <view class="card__top">
          <text class="card__category">{{ item.category }}</text>
          <text v-if="item.is_match_enabled" class="card__badge">匹配</text>
        </view>
        <text class="card__title">{{ item.name }}</text>
        <text class="card__meta">
          {{ item.question_count }} 题 · v{{ item.version }} · {{ item.duration_hint || "待补充时长" }}
        </text>
        <text class="card__footer">进入测试详情</text>
      </view>
    </view>
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 32rpx 28rpx 40rpx;
}

.hero {
  padding: 36rpx 32rpx;
  border-radius: 28rpx;
  background:
    linear-gradient(135deg, rgba(255, 241, 223, 0.95), rgba(255, 221, 193, 0.92)),
    #fff8f1;
  box-shadow: $xc-shadow;
}

.hero__eyebrow {
  display: block;
  font-size: 22rpx;
  color: $xc-accent;
  letter-spacing: 2rpx;
  text-transform: uppercase;
}

.hero__title {
  display: block;
  margin-top: 18rpx;
  font-size: 42rpx;
  line-height: 1.35;
  font-weight: 600;
  color: $xc-ink;
}

.hero__body {
  display: block;
  margin-top: 16rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 32rpx 4rpx 20rpx;
}

.section-head__title {
  font-size: 30rpx;
  font-weight: 600;
}

.section-head__meta {
  font-size: 24rpx;
  color: $xc-muted;
}

.panel {
  padding: 30rpx;
  border: 2rpx solid $xc-line;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.75);
}

.panel--error {
  border-color: rgba(196, 90, 60, 0.2);
  background: rgba(255, 240, 235, 0.92);
}

.panel__text {
  display: block;
  font-size: 26rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__button {
  margin-top: 20rpx;
  border-radius: 999rpx;
  background: $xc-accent;
  color: #fff7f0;
}

.cards {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.card {
  padding: 28rpx;
  border-radius: 26rpx;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
  box-shadow: $xc-shadow;
}

.card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card__category {
  font-size: 22rpx;
  color: $xc-muted;
}

.card__badge {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: $xc-accent-soft;
  font-size: 22rpx;
  color: $xc-accent;
}

.card__title {
  display: block;
  margin-top: 14rpx;
  font-size: 34rpx;
  font-weight: 600;
  color: $xc-ink;
}

.card__meta {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: $xc-muted;
}

.card__footer {
  display: block;
  margin-top: 20rpx;
  font-size: 24rpx;
  color: $xc-accent;
}
</style>
