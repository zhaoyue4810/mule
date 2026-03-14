<script setup lang="ts">
import { computed, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import TimeCapsuleReveal from "@/components/feedback/TimeCapsuleReveal.vue";
import type { TimeCapsuleItem } from "@/shared/models/capsule";
import type { MemoryGreetingPayload, MemorySuggestPayload } from "@/shared/models/memory";
import { checkRevealableCapsules, revealTimeCapsule } from "@/shared/services/capsule";
import { ensureAppSession } from "@/shared/services/auth";
import { fetchMemoryGreeting, fetchMemorySuggest } from "@/shared/services/memory";
import { useTestCatalogStore } from "@/stores/test-catalog";

const store = useTestCatalogStore();

const greeting = ref<MemoryGreetingPayload | null>(null);
const suggest = ref<MemorySuggestPayload | null>(null);
const revealItem = ref<TimeCapsuleItem | null>(null);
const revealVisible = ref(false);

const tests = computed(() => store.tests);
const loading = computed(() => store.loading);
const error = computed(() => store.error);
const mascotEmoji = computed(() => {
  const mood = greeting.value?.mood || "cheer";
  const mapping: Record<string, string> = {
    happy: "😄",
    thinking: "🤔",
    cheer: "💪",
    love: "💗",
    calm: "🙂",
    sleepy: "🌙",
    spark: "✨",
  };
  return mapping[mood] || "🧠";
});

async function load() {
  try {
    await ensureAppSession();
    await store.loadTests(true);
    const [greetingPayload, suggestPayload, capsulePayload] = await Promise.all([
      fetchMemoryGreeting(),
      fetchMemorySuggest(),
      checkRevealableCapsules(),
    ]);
    greeting.value = greetingPayload;
    suggest.value = suggestPayload;
    if (capsulePayload.has_revealable && capsulePayload.items.length) {
      revealItem.value = capsulePayload.items[0];
      revealVisible.value = true;
    }
  } catch (err) {
    console.error(err);
  }
}

function openDetail(testCode: string) {
  uni.navigateTo({
    url: `/pages/test/detail?testCode=${testCode}`,
  });
}

async function closeReveal() {
  if (revealItem.value) {
    try {
      await revealTimeCapsule(revealItem.value.id);
    } catch (err) {
      console.error(err);
    }
  }
  revealVisible.value = false;
  revealItem.value = null;
}

onShow(() => {
  void load();
});
</script>

<template>
  <view class="page">
    <view class="hero">
      <view class="hero__mascot">
        <text class="hero__emoji">{{ mascotEmoji }}</text>
      </view>
      <view class="hero__copy">
        <text class="hero__eyebrow">XinCe Memory</text>
        <text class="hero__title">{{ greeting?.greeting || "今天想先从哪一份测试开始？" }}</text>
        <text class="hero__body">
          记忆等级 Lv.{{ greeting?.know_level || 0 }} · 已完成 {{ greeting?.test_count || 0 }} 次测试
        </text>
        <view v-if="greeting?.behavior_tags?.length" class="hero__tags">
          <text v-for="tag in greeting.behavior_tags" :key="tag" class="hero__tag">{{ tag }}</text>
        </view>
      </view>
    </view>

    <view v-if="suggest?.items?.length" class="panel">
      <text class="panel__title">{{ suggest.title }}</text>
      <text class="panel__body">{{ suggest.reason }}</text>
      <scroll-view scroll-x class="suggest">
        <view class="suggest__list">
          <view
            v-for="item in suggest.items"
            :key="item.test_code"
            class="suggest__card"
            @tap="openDetail(item.test_code)"
          >
            <text class="suggest__category">{{ item.category }}</text>
            <text class="suggest__title">{{ item.name }}</text>
            <text class="suggest__meta">
              {{ item.question_count }} 题 · {{ item.duration_hint || "待补充时长" }}
            </text>
          </view>
        </view>
      </scroll-view>
    </view>

    <view class="section-head">
      <text class="section-head__title">线上测试</text>
      <text class="section-head__meta">{{ tests.length }} 个可用</text>
    </view>

    <view v-if="loading" class="panel">
      <text class="panel__body">正在加载已发布测试...</text>
    </view>

    <view v-else-if="error" class="panel panel--error">
      <text class="panel__body">{{ error }}</text>
      <button class="panel__button" @tap="load">重新加载</button>
    </view>

    <view v-else-if="tests.length === 0" class="panel">
      <text class="panel__body">当前还没有发布内容，请先在后台发布至少一个测试版本。</text>
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

    <TimeCapsuleReveal
      :visible="revealVisible"
      :item="revealItem"
      @close="closeReveal"
    />
  </view>
</template>

<style lang="scss" scoped>
.page {
  padding: 32rpx 28rpx 40rpx;
}

.hero {
  display: grid;
  grid-template-columns: 132rpx 1fr;
  gap: 20rpx;
  padding: 36rpx 32rpx;
  border-radius: 30rpx;
  background: linear-gradient(145deg, rgba(255, 239, 222, 0.96), rgba(255, 219, 194, 0.94));
  box-shadow: $xc-shadow;
}

.hero__mascot {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.62);
}

.hero__emoji {
  font-size: 72rpx;
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
  margin-top: 16rpx;
  font-size: 38rpx;
  line-height: 1.45;
  font-weight: 700;
}

.hero__body {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  color: $xc-muted;
}

.hero__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 16rpx;
}

.hero__tag {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.72);
  font-size: 22rpx;
  color: $xc-accent;
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
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.84);
  border: 2rpx solid $xc-line;
}

.panel--error {
  background: rgba(255, 240, 235, 0.92);
}

.panel__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
}

.panel__body {
  display: block;
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__button {
  margin-top: 20rpx;
  border-radius: 999rpx;
  background: $xc-accent;
  color: #fff7f0;
}

.suggest {
  margin-top: 18rpx;
}

.suggest__list {
  display: flex;
  gap: 14rpx;
}

.suggest__card,
.card {
  padding: 24rpx;
  border-radius: 24rpx;
  background: rgba(255, 253, 248, 0.94);
  border: 2rpx solid rgba(217, 111, 61, 0.08);
  box-shadow: $xc-shadow;
}

.suggest__card {
  width: 280rpx;
}

.suggest__category,
.card__category {
  font-size: 22rpx;
  color: $xc-muted;
}

.suggest__title,
.card__title {
  display: block;
  margin-top: 12rpx;
  font-size: 30rpx;
  font-weight: 600;
}

.suggest__meta,
.card__meta,
.card__footer {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.cards {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card__badge {
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: $xc-accent-soft;
  font-size: 22rpx;
  color: $xc-accent;
}

.card__footer {
  color: $xc-accent;
}
</style>
