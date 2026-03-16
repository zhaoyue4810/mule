<script setup lang="ts">
import { computed, ref } from "vue";

import TabBuddy from "@/components/mascot/TabBuddy.vue";
import { SoundManager } from "@/shared/utils/sound-manager";

const activeTab = ref<"hot" | "story" | "zodiac">("hot");

const tabOptions = [
  { key: "hot", label: "热门讨论", eyebrow: "Hot Topics" },
  { key: "story", label: "测试故事", eyebrow: "Story Feed" },
  { key: "zodiac", label: "星座运势", eyebrow: "Daily Zodiac" },
] as const;

const hotPosts = ref([
  {
    id: 1,
    avatar: "🦊",
    nickname: "阿狐",
    time: "5分钟前",
    content: "做完关系匹配发现我们在「冲突处理」维度差异超大，太准了😂",
    tags: ["关系匹配", "情侣"],
    likes: 126,
    comments: 32,
    shares: 19,
    tone: "pink",
  },
  {
    id: 2,
    avatar: "🐱",
    nickname: "小猫",
    time: "12分钟前",
    content: "今天的每日灵魂提问很戳我，居然一句话说中了最近的状态。",
    tags: ["每日提问", "成长"],
    likes: 89,
    comments: 14,
    shares: 6,
    tone: "mint",
  },
  {
    id: 3,
    avatar: "🦄",
    nickname: "栗子",
    time: "1小时前",
    content: "MBTI 快速版只要几分钟，结果出来后又去测了完整版，差别挺有意思。",
    tags: ["MBTI", "性格测试"],
    likes: 241,
    comments: 55,
    shares: 23,
    tone: "gold",
  },
  {
    id: 4,
    avatar: "🐰",
    nickname: "桃桃",
    time: "2小时前",
    content: "发现页的故事专栏内容好温柔，晚上看完会安心很多。",
    tags: ["发现页", "故事"],
    likes: 67,
    comments: 9,
    shares: 4,
    tone: "purple",
  },
  {
    id: 5,
    avatar: "🐼",
    nickname: "慢慢",
    time: "3小时前",
    content: "最近在用心情日历补签，连续天数终于又拉回来了。",
    tags: ["心情日历", "打卡"],
    likes: 113,
    comments: 22,
    shares: 8,
    tone: "peach",
  },
]);

const stories = ref([
  {
    id: 1,
    emoji: "🌌",
    title: "高敏感不是脆弱，而是一种更细致的感知力",
    summary: "当我们把“敏感”从缺点转为天赋，它会成为理解自己和他人的桥梁。",
    author: "小测编辑部",
    authorAvatar: "🪄",
    reads: 1208,
    likes: 346,
    gradient: "linear-gradient(135deg,#9B7ED8,#E8729A)",
    tag: "深读特稿",
  },
  {
    id: 2,
    emoji: "🧭",
    title: "为什么你总在关系里退后一步",
    summary: "回避并不代表不在乎，很多时候只是大脑在保护你。",
    author: "心理研究组",
    authorAvatar: "🧠",
    reads: 982,
    likes: 271,
    gradient: "linear-gradient(135deg,#7CC5B2,#9B7ED8)",
    tag: "关系专题",
  },
  {
    id: 3,
    emoji: "🌙",
    title: "睡前五分钟，和自己的情绪和解",
    summary: "一个轻量夜间复盘练习，帮助你把焦虑感停留在今天。",
    author: "夜读社",
    authorAvatar: "🫧",
    reads: 743,
    likes: 220,
    gradient: "linear-gradient(135deg,#5F4C8A,#9B7ED8)",
    tag: "夜间疗愈",
  },
  {
    id: 4,
    emoji: "✨",
    title: "人格报告怎么读，才不被标签困住",
    summary: "把类型当作起点而不是终点，你会看到更立体的自己。",
    author: "XinCe Team",
    authorAvatar: "💫",
    reads: 1584,
    likes: 498,
    gradient: "linear-gradient(135deg,#D4A853,#E8729A)",
    tag: "使用指南",
  },
]);

const zodiacList = [
  { key: "aries", emoji: "♈", name: "白羊", brief: "行动力满格，适合启动计划", luck: "92 分" },
  { key: "taurus", emoji: "♉", name: "金牛", brief: "稳中有进，节奏感很好", luck: "88 分" },
  { key: "gemini", emoji: "♊", name: "双子", brief: "表达欲上升，社交顺滑", luck: "95 分" },
  { key: "cancer", emoji: "♋", name: "巨蟹", brief: "情绪细腻，适合疗愈自己", luck: "86 分" },
  { key: "leo", emoji: "♌", name: "狮子", brief: "魅力在线，适合主导发声", luck: "91 分" },
  { key: "virgo", emoji: "♍", name: "处女", brief: "细节加分，推进效率高", luck: "87 分" },
  { key: "libra", emoji: "♎", name: "天秤", brief: "关系平衡感增强", luck: "93 分" },
  { key: "scorpio", emoji: "♏", name: "天蝎", brief: "洞察力很强，适合深聊", luck: "89 分" },
  { key: "sagittarius", emoji: "♐", name: "射手", brief: "灵感充足，适合探索新鲜感", luck: "94 分" },
  { key: "capricorn", emoji: "♑", name: "摩羯", brief: "执行稳定，目标清晰", luck: "84 分" },
  { key: "aquarius", emoji: "♒", name: "水瓶", brief: "创意跃迁，脑洞在线", luck: "90 分" },
  { key: "pisces", emoji: "♓", name: "双鱼", brief: "共情力提升，适合创作", luck: "96 分" },
];

const featuredStory = computed(() => stories.value[0] || null);
const storyList = computed(() => stories.value.slice(1));
const zodiacScroller = computed(() => zodiacList.slice(0, 12));
const currentTabMeta = computed(
  () => tabOptions.find((item) => item.key === activeTab.value) || tabOptions[0],
);
const discoverStats = computed(() => [
  { label: "正在热聊", value: `${hotPosts.value.length} 个话题` },
  { label: "故事专栏", value: `${stories.value.length} 篇精选` },
  { label: "今日运势", value: `${zodiacList[0]?.luck || "88 分"} 起` },
]);

function openSearch() {
  uni.navigateTo({
    url: "/pages/discover/search",
  });
}

function setActiveTab(tab: "hot" | "story" | "zodiac") {
  if (activeTab.value === tab) {
    return;
  }
  activeTab.value = tab;
  SoundManager.haptic(10);
}

function openPostAction(action = "互动") {
  uni.showToast({ title: `${action}功能即将上线`, icon: "none" });
}

function openStory() {
  uni.showToast({ title: "故事详情即将上线", icon: "none" });
}

function openZodiac(item: { key: string; name: string; emoji: string }) {
  uni.navigateTo({
    url: `/pages/discover/zodiac-detail?key=${item.key}&name=${item.name}&emoji=${item.emoji}`,
  });
}
</script>

<template>
  <view class="page">
    <view class="page-bg">
      <view class="page-glow page-glow--one" />
      <view class="page-glow page-glow--two" />
      <view class="page-glow page-glow--three" />
    </view>

    <view class="hero d1">
      <view class="hero__top">
        <view>
          <text class="hero__eyebrow">Discover</text>
          <text class="hero__title">发现</text>
          <text class="hero__body">看看大家都测了什么，也给自己一点新的灵感。</text>
        </view>
        <view class="hero__badge">
          <text class="hero__badge-value">{{ currentTabMeta.eyebrow }}</text>
          <text class="hero__badge-label">今日焦点</text>
        </view>
      </view>

      <view class="hero__search" @tap="openSearch">
        <text class="hero__search-icon">🔍</text>
        <text class="hero__search-placeholder">搜索测试、话题、关键词...</text>
      </view>

      <view class="hero__stats">
        <view v-for="item in discoverStats" :key="item.label" class="hero__stat">
          <text class="hero__stat-label">{{ item.label }}</text>
          <text class="hero__stat-value">{{ item.value }}</text>
        </view>
      </view>
    </view>

    <view class="tabs-card d2">
      <view class="tabs-card__rail">
        <text
          v-for="item in tabOptions"
          :key="item.key"
          class="tabs-card__item"
          :class="{ 'tabs-card__item--active': activeTab === item.key }"
          @tap="setActiveTab(item.key)"
        >
          {{ item.label }}
        </text>
      </view>
    </view>

    <template v-if="activeTab === 'hot'">
      <view class="section d3">
        <view class="section-head">
          <view>
            <text class="section-head__eyebrow">Daily Zodiac</text>
            <text class="section-head__title">今日星座运势</text>
          </view>
          <text class="section-head__meta">轻触查看详情</text>
        </view>

        <scroll-view scroll-x class="horoscope-rail">
          <view class="horoscope-rail__list">
            <view
              v-for="item in zodiacScroller"
              :key="item.key"
              class="horoscope-card"
              @tap="openZodiac(item)"
            >
              <text class="horoscope-card__emoji">{{ item.emoji }}</text>
              <text class="horoscope-card__name">{{ item.name }}</text>
              <text class="horoscope-card__brief">{{ item.brief }}</text>
              <text class="horoscope-card__score">{{ item.luck }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="section d4">
        <view class="section-head">
          <view>
            <text class="section-head__eyebrow">Hot Discussion</text>
            <text class="section-head__title">热门讨论</text>
          </view>
          <text class="section-head__meta">真实分享</text>
        </view>

        <view class="post-list">
          <view
            v-for="post in hotPosts"
            :key="post.id"
            class="post-card"
            :class="`post-card--${post.tone}`"
          >
            <view class="post-card__head">
              <view class="post-card__avatar">{{ post.avatar }}</view>
              <view class="post-card__meta">
                <view class="post-card__userline">
                  <text class="post-card__name">{{ post.nickname }}</text>
                  <text class="post-card__time">{{ post.time }}</text>
                </view>
                <view class="post-card__tags">
                  <text v-for="tag in post.tags" :key="tag" class="post-card__tag">#{{ tag }}</text>
                </view>
              </view>
            </view>

            <text class="post-card__content">{{ post.content }}</text>

            <view class="post-card__footer">
              <text class="post-card__action" @tap="openPostAction('点赞')">❤️ {{ post.likes }}</text>
              <text class="post-card__action" @tap="openPostAction('评论')">💬 {{ post.comments }}</text>
              <text class="post-card__action" @tap="openPostAction('分享')">🔁 {{ post.shares }}</text>
            </view>
          </view>
        </view>
      </view>
    </template>

    <template v-else-if="activeTab === 'story'">
      <view v-if="featuredStory" class="section d3">
        <view class="section-head">
          <view>
            <text class="section-head__eyebrow">Editor Pick</text>
            <text class="section-head__title">本期深读</text>
          </view>
          <text class="section-head__meta">编辑精选</text>
        </view>

        <view class="feature-story" @tap="openStory">
          <view class="feature-story__cover" :style="{ background: featuredStory.gradient }">
            <text class="feature-story__tag">{{ featuredStory.tag }}</text>
            <text class="feature-story__emoji">{{ featuredStory.emoji }}</text>
            <text class="feature-story__title">{{ featuredStory.title }}</text>
          </view>
          <view class="feature-story__body">
            <text class="feature-story__summary">{{ featuredStory.summary }}</text>
            <view class="feature-story__foot">
              <view class="feature-story__author">
                <text class="feature-story__author-avatar">{{ featuredStory.authorAvatar }}</text>
                <text>{{ featuredStory.author }}</text>
              </view>
              <text class="feature-story__meta">{{ featuredStory.reads }} 阅读 · {{ featuredStory.likes }} 点赞</text>
            </view>
          </view>
        </view>
      </view>

      <view class="section d4">
        <view class="section-head">
          <view>
            <text class="section-head__eyebrow">Story Feed</text>
            <text class="section-head__title">测试故事</text>
          </view>
          <text class="section-head__meta">按热度排序</text>
        </view>

        <view class="story-list">
          <view v-for="item in storyList" :key="item.id" class="story-card" @tap="openStory">
            <view class="story-card__cover" :style="{ background: item.gradient }">
              <text class="story-card__emoji">{{ item.emoji }}</text>
              <text class="story-card__tag">{{ item.tag }}</text>
            </view>
            <view class="story-card__body">
              <text class="story-card__title">{{ item.title }}</text>
              <text class="story-card__summary">{{ item.summary }}</text>
              <view class="story-card__foot">
                <view class="story-card__author">
                  <text>{{ item.authorAvatar }}</text>
                  <text>{{ item.author }}</text>
                </view>
                <text class="story-card__read">阅读全文 ›</text>
              </view>
            </view>
          </view>
        </view>
      </view>
    </template>

    <template v-else>
      <view class="section d3">
        <view class="zodiac-hero">
          <view>
            <text class="section-head__eyebrow section-head__eyebrow--light">Daily Energy</text>
            <text class="zodiac-hero__title">十二星座运势</text>
            <text class="zodiac-hero__body">今天整体能量偏温柔和缓，适合做一点小而确定的推进。</text>
          </view>
          <view class="zodiac-hero__chip">
            <text class="zodiac-hero__chip-label">今日最高</text>
            <text class="zodiac-hero__chip-value">{{ zodiacList[zodiacList.length - 1].luck }}</text>
          </view>
        </view>
      </view>

      <view class="section d4">
        <view class="section-head">
          <view>
            <text class="section-head__eyebrow">Zodiac Grid</text>
            <text class="section-head__title">全部星座</text>
          </view>
          <text class="section-head__meta">点击卡片查看今日详情</text>
        </view>

        <view class="zodiac-grid">
          <view
            v-for="item in zodiacList"
            :key="item.key"
            class="zodiac-card"
            @tap="openZodiac(item)"
          >
            <text class="zodiac-card__emoji">{{ item.emoji }}</text>
            <text class="zodiac-card__name">{{ item.name }}</text>
            <text class="zodiac-card__brief">{{ item.brief }}</text>
            <text class="zodiac-card__luck">{{ item.luck }}</text>
          </view>
        </view>
      </view>
    </template>

    <TabBuddy />
  </view>
</template>

<style lang="scss" scoped>
.page {
  position: relative;
  padding: 24rpx 24rpx calc(48rpx + env(safe-area-inset-bottom, 0rpx));
  background:
    linear-gradient(180deg, #fffaf5 0%, #fffdf9 42%, #fbf8ff 100%);
}

.page-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.page-glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(28rpx);
}

.page-glow--one {
  top: -60rpx;
  right: -40rpx;
  width: 320rpx;
  height: 320rpx;
  background: radial-gradient(circle, rgba(232, 114, 154, 0.16), transparent 72%);
}

.page-glow--two {
  top: 420rpx;
  left: -80rpx;
  width: 280rpx;
  height: 280rpx;
  background: radial-gradient(circle, rgba(124, 197, 178, 0.16), transparent 72%);
}

.page-glow--three {
  bottom: 180rpx;
  right: -70rpx;
  width: 260rpx;
  height: 260rpx;
  background: radial-gradient(circle, rgba(212, 168, 83, 0.14), transparent 72%);
}

.hero,
.tabs-card,
.section {
  position: relative;
  z-index: 1;
}

.d1 {
  animation: fadeInUp 0.52s $xc-ease both;
}

.d2 {
  animation: fadeInUp 0.52s $xc-ease both;
  animation-delay: 0.08s;
}

.d3 {
  animation: fadeInUp 0.52s $xc-ease both;
  animation-delay: 0.16s;
}

.d4 {
  animation: fadeInUp 0.52s $xc-ease both;
  animation-delay: 0.24s;
}

.hero {
  padding: 30rpx 28rpx 24rpx;
  border-radius: 34rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.28), transparent 36%),
    linear-gradient(145deg, #f7b48c, #ec8aa0, #9f87d8);
  color: #fff;
  box-shadow: 0 24rpx 60rpx rgba(197, 136, 155, 0.22);
}

.hero__top {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
}

.hero__eyebrow {
  display: block;
  font-size: 20rpx;
  letter-spacing: 1.8rpx;
  text-transform: uppercase;
  opacity: 0.82;
}

.hero__title {
  display: block;
  margin-top: 8rpx;
  font-size: 54rpx;
  line-height: 1.04;
  font-family: $xc-font-serif;
  font-weight: 900;
}

.hero__body {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.76;
  max-width: 440rpx;
  color: rgba(255, 255, 255, 0.92);
}

.hero__badge {
  width: 168rpx;
  flex-shrink: 0;
  align-self: flex-start;
  padding: 16rpx 14rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.16);
  text-align: center;
  // #ifdef H5
  backdrop-filter: blur(14rpx);
  // #endif
}

.hero__badge-value {
  display: block;
  font-size: 24rpx;
  font-weight: 800;
}

.hero__badge-label {
  display: block;
  margin-top: 8rpx;
  font-size: 18rpx;
  opacity: 0.74;
}

.hero__search {
  margin-top: 20rpx;
  border-radius: 999rpx;
  padding: 18rpx 22rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  background: rgba(255, 255, 255, 0.16);
  // #ifdef H5
  backdrop-filter: blur(12rpx);
  // #endif
}

.hero__search-icon {
  font-size: 24rpx;
}

.hero__search-placeholder {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.9);
}

.hero__stats {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.hero__stat {
  border-radius: 20rpx;
  padding: 16rpx 14rpx;
  background: rgba(255, 255, 255, 0.12);
}

.hero__stat-label {
  display: block;
  font-size: 18rpx;
  opacity: 0.72;
}

.hero__stat-value {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  font-weight: 800;
}

.tabs-card {
  margin-top: 18rpx;
  padding: 10rpx;
  border-radius: 26rpx;
  @include glass-strong;
}

.tabs-card__rail {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8rpx;
}

.tabs-card__item {
  padding: 16rpx 10rpx;
  border-radius: 20rpx;
  text-align: center;
  font-size: 24rpx;
  font-weight: 700;
  color: $xc-muted;
  transition: transform 0.22s $xc-ease, background 0.22s $xc-ease, color 0.22s $xc-ease;
}

.tabs-card__item--active {
  color: $xc-ink;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 10rpx 22rpx rgba(155, 126, 216, 0.08);
}

.section {
  margin-top: 22rpx;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16rpx;
}

.section-head__eyebrow {
  display: block;
  font-size: 18rpx;
  letter-spacing: 1.2rpx;
  text-transform: uppercase;
  color: $xc-muted;
}

.section-head__eyebrow--light {
  color: rgba(255, 255, 255, 0.78);
}

.section-head__title {
  display: block;
  margin-top: 6rpx;
  font-size: 32rpx;
  font-weight: 900;
  color: $xc-ink;
}

.section-head__meta {
  font-size: 20rpx;
  color: $xc-muted;
}

.horoscope-rail {
  margin-top: 16rpx;
  white-space: nowrap;
}

.horoscope-rail__list {
  display: inline-flex;
  gap: 12rpx;
  padding-right: 24rpx;
}

.horoscope-card {
  width: 220rpx;
  padding: 22rpx 20rpx;
  border-radius: 28rpx;
  @include glass;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.horoscope-card__emoji {
  font-size: 36rpx;
}

.horoscope-card__name {
  font-size: 27rpx;
  font-weight: 800;
  color: $xc-ink;
}

.horoscope-card__brief {
  font-size: 21rpx;
  line-height: 1.6;
  color: $xc-muted;
  white-space: normal;
}

.horoscope-card__score {
  margin-top: 10rpx;
  align-self: flex-start;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 700;
  color: $xc-purple-d;
  background: rgba(155, 126, 216, 0.12);
}

.post-list,
.story-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.post-card {
  padding: 22rpx;
  border-radius: 28rpx;
  @include card-base;
}

.post-card--pink {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(255, 244, 247, 0.98));
}

.post-card--mint {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(245, 255, 251, 0.98));
}

.post-card--gold {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(255, 249, 240, 0.98));
}

.post-card--purple {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 244, 255, 0.98));
}

.post-card--peach {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(255, 246, 241, 0.98));
}

.post-card__head {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
}

.post-card__avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  background: rgba(255, 255, 255, 0.86);
}

.post-card__meta {
  min-width: 0;
  flex: 1;
}

.post-card__userline {
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
}

.post-card__name {
  font-size: 26rpx;
  font-weight: 800;
  color: $xc-ink;
}

.post-card__time {
  font-size: 20rpx;
  color: $xc-hint;
}

.post-card__tags {
  margin-top: 10rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.post-card__tag {
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  font-size: 18rpx;
  color: $xc-purple-d;
  background: rgba(155, 126, 216, 0.1);
}

.post-card__content {
  display: block;
  margin-top: 16rpx;
  font-size: 25rpx;
  line-height: 1.8;
  color: $xc-ink;
}

.post-card__footer {
  margin-top: 18rpx;
  display: flex;
  gap: 12rpx;
  flex-wrap: wrap;
}

.post-card__action {
  padding: 10rpx 14rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  color: $xc-muted;
  background: rgba(255, 255, 255, 0.74);
}

.feature-story {
  margin-top: 16rpx;
  overflow: hidden;
  border-radius: 32rpx;
  @include card-base;
}

.feature-story__cover {
  padding: 22rpx 24rpx 28rpx;
  color: #fff;
}

.feature-story__tag {
  display: inline-flex;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  font-size: 18rpx;
  font-weight: 700;
}

.feature-story__emoji {
  display: block;
  margin-top: 18rpx;
  font-size: 44rpx;
}

.feature-story__title {
  display: block;
  margin-top: 14rpx;
  font-size: 36rpx;
  line-height: 1.3;
  font-family: $xc-font-serif;
  font-weight: 800;
}

.feature-story__body {
  padding: 22rpx 24rpx 24rpx;
}

.feature-story__summary {
  display: block;
  font-size: 24rpx;
  line-height: 1.8;
  color: $xc-muted;
}

.feature-story__foot,
.story-card__foot {
  margin-top: 16rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12rpx;
}

.feature-story__author,
.story-card__author {
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-size: 21rpx;
  color: $xc-ink;
}

.feature-story__author-avatar {
  font-size: 24rpx;
}

.feature-story__meta,
.story-card__read {
  font-size: 20rpx;
  color: $xc-purple-d;
  font-weight: 700;
}

.story-card {
  overflow: hidden;
  border-radius: 28rpx;
  @include card-base;
  display: grid;
  grid-template-columns: 180rpx 1fr;
  gap: 0;
}

.story-card__cover {
  position: relative;
  min-height: 220rpx;
  padding: 20rpx;
  color: #fff;
}

.story-card__emoji {
  font-size: 38rpx;
}

.story-card__tag {
  position: absolute;
  left: 20rpx;
  bottom: 18rpx;
  padding: 8rpx 12rpx;
  border-radius: 999rpx;
  font-size: 18rpx;
  background: rgba(255, 255, 255, 0.14);
}

.story-card__body {
  padding: 20rpx 22rpx;
}

.story-card__title {
  display: block;
  font-size: 28rpx;
  line-height: 1.5;
  font-family: $xc-font-serif;
  font-weight: 800;
  color: $xc-ink;
}

.story-card__summary {
  display: block;
  margin-top: 12rpx;
  font-size: 22rpx;
  line-height: 1.72;
  color: $xc-muted;
}

.zodiac-hero {
  padding: 26rpx 24rpx;
  border-radius: 30rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.18), transparent 34%),
    linear-gradient(145deg, #4f3c77, #8862bd, #e48faa);
  color: #fff;
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
}

.zodiac-hero__title {
  display: block;
  margin-top: 8rpx;
  font-size: 38rpx;
  font-family: $xc-font-serif;
  font-weight: 800;
}

.zodiac-hero__body {
  display: block;
  margin-top: 12rpx;
  font-size: 23rpx;
  line-height: 1.72;
  color: rgba(255, 255, 255, 0.9);
}

.zodiac-hero__chip {
  width: 148rpx;
  flex-shrink: 0;
  align-self: flex-start;
  padding: 14rpx 12rpx;
  border-radius: 22rpx;
  text-align: center;
  background: rgba(255, 255, 255, 0.14);
}

.zodiac-hero__chip-label {
  display: block;
  font-size: 18rpx;
  opacity: 0.78;
}

.zodiac-hero__chip-value {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 800;
}

.zodiac-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.zodiac-card {
  padding: 22rpx 18rpx;
  border-radius: 26rpx;
  @include card-base;
}

.zodiac-card__emoji {
  font-size: 34rpx;
}

.zodiac-card__name {
  display: block;
  margin-top: 12rpx;
  font-size: 28rpx;
  font-weight: 800;
  color: $xc-ink;
}

.zodiac-card__brief {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.65;
  color: $xc-muted;
}

.zodiac-card__luck {
  display: inline-flex;
  margin-top: 14rpx;
  padding: 8rpx 12rpx;
  border-radius: 999rpx;
  font-size: 19rpx;
  color: $xc-purple-d;
  background: rgba(155, 126, 216, 0.1);
}

@media (max-width: 420px) {
  .hero__top,
  .zodiac-hero {
    flex-direction: column;
  }

  .hero__badge,
  .zodiac-hero__chip {
    width: auto;
  }

  .hero__stats,
  .zodiac-grid {
    grid-template-columns: 1fr;
  }

  .story-card {
    grid-template-columns: 1fr;
  }

  .story-card__cover {
    min-height: 180rpx;
  }
}
</style>
