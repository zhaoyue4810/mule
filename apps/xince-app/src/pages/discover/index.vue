<script setup lang="ts">
import { computed, ref } from "vue";

import TabBuddy from "@/components/mascot/TabBuddy.vue";
import { SoundManager } from "@/shared/utils/sound-manager";

const activeTab = ref<"hot" | "story" | "zodiac">("hot");

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
  },
]);

const zodiacList = [
  { key: "aries", emoji: "♈", name: "白羊", brief: "行动力满格，适合启动计划" },
  { key: "taurus", emoji: "♉", name: "金牛", brief: "稳中有进，节奏感很好" },
  { key: "gemini", emoji: "♊", name: "双子", brief: "表达欲上升，社交顺滑" },
  { key: "cancer", emoji: "♋", name: "巨蟹", brief: "情绪细腻，适合疗愈自己" },
  { key: "leo", emoji: "♌", name: "狮子", brief: "魅力在线，适合主导发声" },
  { key: "virgo", emoji: "♍", name: "处女", brief: "细节加分，推进效率高" },
  { key: "libra", emoji: "♎", name: "天秤", brief: "关系平衡感增强" },
  { key: "scorpio", emoji: "♏", name: "天蝎", brief: "洞察力很强，适合深聊" },
  { key: "sagittarius", emoji: "♐", name: "射手", brief: "灵感充足，适合探索新鲜感" },
  { key: "capricorn", emoji: "♑", name: "摩羯", brief: "执行稳定，目标清晰" },
  { key: "aquarius", emoji: "♒", name: "水瓶", brief: "创意跃迁，脑洞在线" },
  { key: "pisces", emoji: "♓", name: "双鱼", brief: "共情力提升，适合创作" },
];

const zodiacScroller = computed(() => zodiacList.slice(0, 12));

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

function openPostAction() {
  uni.showToast({ title: "社区互动即将上线", icon: "none" });
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
    <view class="search glass d1" @tap="openSearch">
      <text>🔍</text>
      <text class="search__placeholder">搜索测试、话题...</text>
    </view>

    <view class="tabs d2">
      <text
        v-for="item in [
          { key: 'hot', label: '热门讨论' },
          { key: 'story', label: '测试故事' },
          { key: 'zodiac', label: '星座运势' },
        ]"
        :key="item.key"
        class="tabs__item"
        :class="{ 'tabs__item--active': activeTab === item.key }"
        @tap="setActiveTab(item.key as 'hot' | 'story' | 'zodiac')"
      >
        {{ item.label }}
      </text>
      <view
        class="tabs__line"
        :style="{
          left: activeTab === 'hot' ? 'calc(16.67% - 24rpx)' : activeTab === 'story' ? 'calc(50% - 24rpx)' : 'calc(83.33% - 24rpx)',
        }"
      />
    </view>

    <template v-if="activeTab === 'hot'">
      <scroll-view scroll-x class="zodiac-row d3">
        <view class="zodiac-row__list">
          <view
            v-for="item in zodiacScroller"
            :key="item.key"
            class="zodiac-chip"
            @tap="openZodiac(item)"
          >
            <text class="zodiac-chip__emoji">{{ item.emoji }}</text>
            <text class="zodiac-chip__name">{{ item.name }}</text>
          </view>
        </view>
      </scroll-view>

      <view class="post-list d4">
        <view v-for="post in hotPosts" :key="post.id" class="post">
          <view class="post__head">
            <view class="post__avatar">{{ post.avatar }}</view>
            <view class="post__meta">
              <text class="post__name">{{ post.nickname }}</text>
              <text class="post__time">{{ post.time }}</text>
            </view>
          </view>
          <text class="post__content">{{ post.content }}</text>
          <view class="post__tags">
            <text v-for="tag in post.tags" :key="tag" class="post__tag">#{{ tag }}</text>
          </view>
          <view class="post__ops">
            <text @tap="openPostAction">❤️ {{ post.likes }}</text>
            <text @tap="openPostAction">💬 {{ post.comments }}</text>
            <text @tap="openPostAction">🔁 {{ post.shares }}</text>
          </view>
        </view>
      </view>
    </template>

    <template v-else-if="activeTab === 'story'">
      <view class="story-list d3">
        <view v-for="item in stories" :key="item.id" class="story-card" @tap="openStory">
          <view class="story-card__cover" :style="{ background: item.gradient }">
            <text>{{ item.emoji }}</text>
          </view>
          <view class="story-card__body">
            <text class="story-card__title">{{ item.title }}</text>
            <text class="story-card__summary">{{ item.summary }}</text>
            <view class="story-card__foot">
              <view class="story-card__author">
                <text>{{ item.authorAvatar }}</text>
                <text>{{ item.author }}</text>
              </view>
              <text>{{ item.reads }} 阅读 · {{ item.likes }} 点赞</text>
            </view>
          </view>
        </view>
      </view>
    </template>

    <template v-else>
      <view class="zodiac-grid d3">
        <view
          v-for="item in zodiacList"
          :key="item.key"
          class="zodiac-card"
          @tap="openZodiac(item)"
        >
          <text class="zodiac-card__emoji">{{ item.emoji }}</text>
          <text class="zodiac-card__name">{{ item.name }}</text>
          <text class="zodiac-card__brief">{{ item.brief }}</text>
        </view>
      </view>
    </template>

    <TabBuddy />
  </view>
</template>

<style lang="scss" scoped>
/* ─── Page layout ─── */
.page {
  padding: 22rpx 24rpx 40rpx;
}

/* ─── Glass mixin helper ─── */
.glass {
  @include glass;
}

/* ─── Search bar (matches home page glass pill) ─── */
.search {
  @include glass-strong;
  border-radius: $xc-r-pill;
  padding: 18rpx 24rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  transition: transform $xc-fast $xc-ease, box-shadow $xc-fast $xc-ease;

  &:active {
    transform: scale(0.98);
    box-shadow: $xc-sh-sm;
  }
}

.search__placeholder {
  color: $xc-hint;
  font-size: 24rpx;
  letter-spacing: 0.5rpx;
}

/* ─── Tab bar with animated indicator ─── */
.tabs {
  margin-top: 20rpx;
  position: relative;
  display: flex;
  justify-content: space-around;
  padding-bottom: 16rpx;
  border-bottom: 1px solid $xc-line-soft;
}

.tabs__item {
  font-size: 28rpx;
  color: $xc-muted;
  padding: 10rpx 16rpx;
  font-weight: 500;
  transition: color $xc-fast $xc-ease, font-weight $xc-fast $xc-ease;

  &:active {
    transform: scale(0.96);
  }
}

.tabs__item--active {
  color: $xc-purple-d;
  font-weight: 800;
}

.tabs__line {
  position: absolute;
  bottom: -2rpx;
  width: 48rpx;
  height: 6rpx;
  border-radius: $xc-r-pill;
  background: linear-gradient(90deg, $xc-purple, $xc-pink);
  transition: left 0.35s $xc-spring;
  box-shadow: 0 2rpx 12rpx rgba($xc-purple, 0.35);
}

/* ─── Zodiac horizontal scroll chips (glass-morphism) ─── */
.zodiac-row {
  margin-top: 18rpx;
}

.zodiac-row__list {
  display: flex;
  gap: 14rpx;
  padding: 4rpx 0;
}

.zodiac-chip {
  width: 104rpx;
  flex-shrink: 0;
  border-radius: $xc-r-pill;
  padding: 16rpx 10rpx;
  text-align: center;
  @include glass;
  transition: transform $xc-fast $xc-spring, box-shadow $xc-fast $xc-ease;

  &:active {
    transform: scale(0.95);
    box-shadow: $xc-sh-sm;
  }
}

.zodiac-chip__emoji {
  display: block;
  font-size: 28rpx;
}

.zodiac-chip__name {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: $xc-muted;
  font-weight: 600;
}

/* ─── Post cards (glass card styling) ─── */
.post-list {
  margin-top: 16rpx;
  border-radius: $xc-r-lg;
  @include glass-strong;
  overflow: hidden;
}

.post {
  padding: 22rpx 20rpx;
  border-bottom: 1px solid $xc-line-soft;
  transition: transform $xc-fast $xc-ease, background $xc-fast $xc-ease;

  &:active {
    transform: scale(0.98);
    background: rgba($xc-purple, 0.03);
  }
}

.post:last-child {
  border-bottom: 0;
}

.post__head {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.post__avatar {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, $xc-purple-p, $xc-pink-p);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  box-shadow: 0 2rpx 8rpx rgba($xc-purple, 0.15);
}

.post__meta {
  display: flex;
  flex-direction: column;
}

.post__name {
  font-size: 24rpx;
  font-weight: 800;
  color: $xc-ink;
}

.post__time {
  font-size: 20rpx;
  color: $xc-hint;
  margin-top: 2rpx;
}

.post__content {
  margin-top: 14rpx;
  display: block;
  font-size: 26rpx;
  line-height: 1.7;
  color: $xc-ink;
}

.post__tags {
  margin-top: 10rpx;
  display: flex;
  gap: 10rpx;
  flex-wrap: wrap;
}

.post__tag {
  font-size: 20rpx;
  color: $xc-purple-d;
  background: $xc-purple-p;
  padding: 4rpx 12rpx;
  border-radius: $xc-r-pill;
  font-weight: 600;
  transition: transform $xc-fast $xc-ease;

  &:active {
    transform: scale(0.95);
  }
}

.post__ops {
  margin-top: 14rpx;
  display: flex;
  gap: 28rpx;
  font-size: 22rpx;
  color: $xc-muted;

  text {
    transition: transform $xc-fast $xc-ease, color $xc-fast $xc-ease;

    &:active {
      transform: scale(0.92);
      color: $xc-pink;
    }
  }
}

/* ─── Story cards (gradient covers + glass body) ─── */
.story-list {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.story-card {
  border-radius: $xc-r-lg;
  @include glass-strong;
  overflow: hidden;
  transition: transform $xc-fast $xc-spring, box-shadow $xc-fast $xc-ease;

  &:active {
    transform: scale(0.98);
    box-shadow: $xc-sh-sm;
  }
}

.story-card__cover {
  height: 240rpx;
  color: $xc-white;
  font-size: 76rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;

  /* gradient overlay for text legibility */
  &::after {
    content: "";
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 50%;
    background: linear-gradient(transparent, rgba(0, 0, 0, 0.15));
    pointer-events: none;
  }
}

.story-card__body {
  padding: 20rpx;
}

.story-card__title {
  display: block;
  font-size: 28rpx;
  font-weight: 800;
  font-family: $xc-font-serif;
  color: $xc-ink;
  line-height: 1.45;
}

.story-card__summary {
  margin-top: 10rpx;
  display: block;
  color: $xc-muted;
  font-size: 23rpx;
  line-height: 1.65;
}

.story-card__foot {
  margin-top: 16rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: $xc-hint;
  font-size: 20rpx;
}

.story-card__author {
  display: flex;
  align-items: center;
  gap: 8rpx;
  font-weight: 600;
  color: $xc-muted;
}

/* ─── Zodiac grid (3x4 with hover/press effects) ─── */
.zodiac-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.zodiac-card {
  border-radius: $xc-r-card;
  @include glass;
  box-shadow: $xc-sh-md;
  padding: 18rpx 12rpx;
  text-align: center;
  transition: transform $xc-fast $xc-spring, box-shadow $xc-fast $xc-ease;

  &:active {
    transform: scale(0.96);
    box-shadow: $xc-sh-sm;
  }
}

.zodiac-card__emoji {
  display: block;
  font-size: 36rpx;
}

.zodiac-card__name {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  font-weight: 800;
  color: $xc-ink;
}

.zodiac-card__brief {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: $xc-muted;
  line-height: 1.55;
}

/* ─── Cascading fade-in animations (d1–d5) ─── */
.d1,
.d2,
.d3,
.d4,
.d5 {
  animation: fadeInUp 0.55s $xc-ease both;
}

.d1 {
  animation-delay: 0.05s;
}

.d2 {
  animation-delay: 0.12s;
}

.d3 {
  animation-delay: 0.2s;
}

.d4 {
  animation-delay: 0.28s;
}

.d5 {
  animation-delay: 0.36s;
}
</style>
