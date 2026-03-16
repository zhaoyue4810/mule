<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { onShow } from "@dcloudio/uni-app";

import TabBuddy from "@/components/mascot/TabBuddy.vue";
import type { MatchHistoryResponse } from "@/shared/models/match";
import type { PublishedTestSummary } from "@/shared/models/tests";
import { ensureAppSession } from "@/shared/services/auth";
import { createMatchInvite, fetchMatchHistory } from "@/shared/services/match";
import { fetchPublishedTests } from "@/shared/services/tests";

const loading = ref(false);
const creatingTestCode = ref("");
const error = ref("");
const history = ref<MatchHistoryResponse>({ items: [], duo_badges: [] });
const tests = ref<PublishedTestSummary[]>([]);

const matchEnabledTests = computed(() =>
  tests.value.filter((item) => item.is_match_enabled),
);

const completedHistory = computed(() =>
  history.value.items.filter((item) => item.status === "COMPLETED"),
);

const rankedCP = computed(() =>
  history.value.items
    .filter((item) => item.compatibility_score != null && item.partner)
    .sort((a, b) => (b.compatibility_score || 0) - (a.compatibility_score || 0))
    .slice(0, 3),
);

const heroBadge = computed(() => {
  const score = rankedCP.value[0]?.compatibility_score || 0;
  if (score >= 95) {
    return "已发现天作之合";
  }
  if (score >= 85) {
    return "默契指数正在飙升";
  }
  if (matchEnabledTests.value.length) {
    return `${matchEnabledTests.value.length} 套测试支持双人模式`;
  }
  return "等待后台发布匹配测试";
});

const heroCopy = computed(() => {
  if (rankedCP.value[0]?.partner?.nickname) {
    return `你和 ${rankedCP.value[0].partner.nickname} 的最高匹配度已经达到 ${rankedCP.value[0].compatibility_score} 分，继续解锁更多关系切面。`;
  }
  if (matchEnabledTests.value.length) {
    return "把一套测试变成双人默契实验，从吸引、共鸣到互补都能留下专属报告。";
  }
  return "后台还没有发布支持匹配的测试版本，先导入并发布带有匹配能力的测试即可点亮这里。";
});

const heroStats = computed(() => [
  {
    label: "可匹配测试",
    value: `${matchEnabledTests.value.length}`,
    hint: matchEnabledTests.value.length ? "现在就能发起邀请" : "等待配置",
  },
  {
    label: "已完成双人局",
    value: `${completedHistory.value.length}`,
    hint: completedHistory.value.length ? "报告已归档" : "首份报告待解锁",
  },
  {
    label: "双人徽章",
    value: `${history.value.duo_badges.length}`,
    hint: history.value.duo_badges.length ? "关系成就已点亮" : "完成匹配后解锁",
  },
]);

const featuredModes = computed(() => {
  const first = matchEnabledTests.value[0] || null;
  const second = matchEnabledTests.value[1] || first;
  return [
    {
      key: "exclusive",
      emoji: "🎯",
      badge: "双人同题作答",
      title: "专属匹配测试",
      desc: first
        ? `推荐「${first.name}」，双方完成同一套题后会直接生成匹配报告。`
        : "选择一套支持匹配的测试，双方作答后即可进入专属关系报告。",
      note: first
        ? `${first.question_count || 0} 题 · ${first.duration_hint || "约 5 分钟"}`
        : "等待后台发布支持匹配的测试",
      testCode: first?.test_code || "",
      button: "开始匹配",
      className: "mode-card--violet",
    },
    {
      key: "share",
      emoji: "🔗",
      badge: "邀请好友加入",
      title: "分享匹配",
      desc: second
        ? `把「${second.name}」分享给好友，对方加入后自动同步进入匹配流程。`
        : "把你的测试邀请发给对方，对方加入后就能继续匹配链路。",
      note: second
        ? `优先点亮 ${second.category || "双人"} 徽章`
        : "适合快速发起一次关系实验",
      testCode: second?.test_code || "",
      button: "发起邀请",
      className: "mode-card--peach",
    },
  ];
});

const leaderboardIntro = computed(() => {
  if (!rankedCP.value.length) {
    return "还没有完成中的双人报告，先邀请一位朋友来试试。";
  }
  return "完成度越高，榜单里会越快浮现你们的默契组合。";
});

const historyIntro = computed(() => {
  if (!history.value.items.length) {
    return "双人测试、等待中的邀请和已完成的匹配都会收进这里。";
  }
  return `${history.value.items.length} 条关系记录已经归档，可继续进入等待页或查看结果。`;
});

const badgeIntro = computed(() => {
  if (!history.value.duo_badges.length) {
    return "首份双人报告完成后，这里会先点亮一枚关系纪念徽章。";
  }
  return "每一枚都对应一次双人共振时刻，继续玩更多测试会升级阶位。";
});

function formatTime(value?: string | null) {
  if (!value) {
    return "刚刚";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getMonth() + 1}/${date.getDate()} ${`${date.getHours()}`.padStart(2, "0")}:${`${date.getMinutes()}`.padStart(2, "0")}`;
}

function formatStatus(status: string) {
  if (status === "COMPLETED") {
    return "已完成";
  }
  if (status === "WAITING_PARTNER") {
    return "等待加入";
  }
  if (status === "RUNNING") {
    return "进行中";
  }
  return status;
}

function statusClass(status: string) {
  if (status === "WAITING_PARTNER") {
    return "history-card__status--waiting";
  }
  if (status === "RUNNING") {
    return "history-card__status--running";
  }
  return "history-card__status--done";
}

function tierBadge(tier?: string | null) {
  if (!tier) {
    return "默契搭档";
  }
  return tier;
}

function rankStyle(index: number) {
  if (index === 0) {
    return "leaderboard-card__rank--gold";
  }
  if (index === 1) {
    return "leaderboard-card__rank--silver";
  }
  return "leaderboard-card__rank--bronze";
}

function scoreLabel(score?: number | null) {
  if (score == null) {
    return "等待生成";
  }
  if (score >= 95) {
    return "天作之合";
  }
  if (score >= 85) {
    return "灵魂共振";
  }
  if (score >= 70) {
    return "高契合";
  }
  return "互补搭档";
}

function openSession(item: MatchHistoryResponse["items"][number]) {
  if (item.status === "COMPLETED") {
    uni.navigateTo({ url: `/pages/match/report?sessionId=${item.session_id}` });
    return;
  }
  uni.navigateTo({
    url: `/pages/match/waiting?sessionId=${item.session_id}&code=${item.invite_code}`,
  });
}

async function createInvite(testCode: string) {
  if (!testCode) {
    uni.showToast({
      title: "后台还没发布可匹配测试",
      icon: "none",
    });
    return;
  }
  if (creatingTestCode.value) {
    return;
  }
  creatingTestCode.value = testCode;
  try {
    const payload = await createMatchInvite(testCode);
    uni.navigateTo({
      url: `/pages/match/waiting?sessionId=${payload.session_id}&code=${payload.invite_code}`,
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "创建邀请失败",
      icon: "none",
    });
  } finally {
    creatingTestCode.value = "";
  }
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    await ensureAppSession();
    const [historyPayload, testsPayload] = await Promise.all([
      fetchMatchHistory(),
      fetchPublishedTests(),
    ]);
    history.value = historyPayload;
    tests.value = testsPayload;
  } catch (err) {
    error.value = err instanceof Error ? err.message : "匹配中心加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
onShow(load);
</script>

<template>
  <view class="page">
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--pink" />
    <view class="page__mesh" />

    <view class="page__content">
      <view class="hero">
        <view class="hero__spark hero__spark--left" />
        <view class="hero__spark hero__spark--right" />
        <view class="hero__topline">
          <text class="hero__eyebrow">SOUL MATCH LAB</text>
          <text class="hero__badge">{{ heroBadge }}</text>
        </view>

        <view class="hero__avatars">
          <view class="hero__avatar-wrap">
            <view class="hero__avatar hero__avatar--primary">
              {{ history.items[0]?.partner?.avatar_value || "🌿" }}
            </view>
            <text class="hero__avatar-name">{{ history.items[0]?.partner?.nickname || "等待搭档" }}</text>
          </view>
          <view class="hero__orbit">❤</view>
          <view class="hero__avatar-wrap">
            <view class="hero__avatar hero__avatar--secondary">💫</view>
            <text class="hero__avatar-name">你</text>
          </view>
        </view>

        <text class="hero__title">灵魂匹配站</text>
        <text class="hero__body">{{ heroCopy }}</text>

        <view class="hero__stats">
          <view v-for="item in heroStats" :key="item.label" class="hero-stat">
            <text class="hero-stat__value">{{ item.value }}</text>
            <text class="hero-stat__label">{{ item.label }}</text>
            <text class="hero-stat__hint">{{ item.hint }}</text>
          </view>
        </view>
      </view>

      <view v-if="loading" class="surface-card panel">
        <text class="panel__eyebrow">SYNCING</text>
        <text class="panel__title">正在同步匹配中心</text>
        <text class="panel__body">测试配置、邀请记录和双人成就会一起刷新进来。</text>
      </view>

      <view v-else-if="error" class="surface-card panel panel--error">
        <text class="panel__eyebrow">UNAVAILABLE</text>
        <text class="panel__title">匹配中心暂时没连上</text>
        <text class="panel__body">{{ error }}</text>
        <button class="panel__button" @tap="load">重新加载</button>
      </view>

      <template v-else>
        <view class="section-head">
          <view>
            <text class="section-head__title">匹配模式</text>
            <text class="section-head__desc">
              {{ matchEnabledTests.length ? "选择一种关系实验方式，立刻发起邀请。" : "后台还没有发布支持匹配的测试版本。" }}
            </text>
          </view>
        </view>
        <view class="mode-grid">
          <view
            v-for="mode in featuredModes"
            :key="mode.key"
            class="surface-card mode-card"
            :class="mode.className"
          >
            <view class="mode-card__head">
              <text class="mode-card__emoji">{{ mode.emoji }}</text>
              <text class="mode-card__badge">{{ mode.badge }}</text>
            </view>
            <text class="mode-card__title">{{ mode.title }}</text>
            <text class="mode-card__desc">{{ mode.desc }}</text>
            <text class="mode-card__note">{{ mode.note }}</text>
            <button
              class="mode-card__button"
              :disabled="!mode.testCode"
              :loading="creatingTestCode === mode.testCode"
              @tap="createInvite(mode.testCode)"
            >
              {{ mode.button }} →
            </button>
          </view>
        </view>

        <view class="section-head">
          <view>
            <text class="section-head__title">最佳 CP 排行</text>
            <text class="section-head__desc">{{ leaderboardIntro }}</text>
          </view>
        </view>
        <view v-if="rankedCP.length" class="leaderboard">
          <view
            v-for="(item, index) in rankedCP"
            :key="`cp-${item.session_id}`"
            class="surface-card leaderboard-card"
            @tap="openSession(item)"
          >
            <view class="leaderboard-card__rank" :class="rankStyle(index)">{{ index + 1 }}</view>
            <view class="leaderboard-card__pair">
              <view class="leaderboard-card__avatars">
                <text class="leaderboard-card__avatar">🙂</text>
                <text class="leaderboard-card__heart">❤</text>
                <text class="leaderboard-card__avatar">
                  {{ item.partner?.avatar_value || "✨" }}
                </text>
              </view>
              <view class="leaderboard-card__copy">
                <text class="leaderboard-card__name">{{ item.partner?.nickname || "匿名搭档" }}</text>
                <text class="leaderboard-card__meta">
                  {{ item.test_name }} · {{ tierBadge(item.tier) }}
                </text>
              </view>
            </view>
            <view class="leaderboard-card__score">
              <text class="leaderboard-card__score-value">{{ item.compatibility_score }}%</text>
              <text class="leaderboard-card__score-label">{{ scoreLabel(item.compatibility_score) }}</text>
            </view>
          </view>
        </view>
        <view v-else class="surface-card panel">
          <text class="panel__title">还没有进入榜单的组合</text>
          <text class="panel__body">发起一场双人测试后，这里就会开始记录你们的默契排名。</text>
        </view>

        <view class="section-head">
          <view>
            <text class="section-head__title">我的匹配记录</text>
            <text class="section-head__desc">{{ historyIntro }}</text>
          </view>
          <text class="section-head__meta">{{ history.items.length }} 条</text>
        </view>
        <view v-if="history.items.length" class="history-list">
          <view
            v-for="item in history.items"
            :key="item.session_id"
            class="surface-card history-card"
            @tap="openSession(item)"
          >
            <view class="history-card__top">
              <view class="history-card__copy">
                <text class="history-card__title">{{ item.test_name }}</text>
                <text class="history-card__meta">
                  {{ item.partner?.nickname || "等待好友加入" }} · {{ tierBadge(item.tier) }}
                </text>
              </view>
              <text class="history-card__status" :class="statusClass(item.status)">
                {{ formatStatus(item.status) }}
              </text>
            </view>
            <view class="history-card__meter">
              <view
                class="history-card__meter-fill"
                :style="{ width: `${Math.max(18, Math.min(100, item.compatibility_score || 18))}%` }"
              />
            </view>
            <view class="history-card__foot">
              <text class="history-card__time">{{ formatTime(item.completed_at || item.created_at) }}</text>
              <text class="history-card__score">
                {{ item.compatibility_score != null ? `${item.compatibility_score} 分 · ${scoreLabel(item.compatibility_score)}` : "邀请已发出，等待对方加入" }}
              </text>
            </view>
          </view>
        </view>
        <view v-else class="surface-card panel">
          <text class="panel__title">你的双人档案还是空白</text>
          <text class="panel__body">先发起一次邀请，等好友加入并完成作答后，就能在这里看到完整进度。</text>
        </view>

        <view class="section-head">
          <view>
            <text class="section-head__title">双人成就徽章</text>
            <text class="section-head__desc">{{ badgeIntro }}</text>
          </view>
          <text class="section-head__meta">{{ history.duo_badges.length }} 枚</text>
        </view>
        <view v-if="history.duo_badges.length" class="badge-grid">
          <view
            v-for="badge in history.duo_badges"
            :key="badge.badge_key"
            class="surface-card badge-card"
          >
            <view class="badge-card__halo" />
            <text class="badge-card__emoji">{{ badge.emoji }}</text>
            <text class="badge-card__name">{{ badge.name }}</text>
            <text class="badge-card__time">{{ formatTime(badge.unlocked_at) }}</text>
          </view>
        </view>
        <view v-else class="surface-card panel">
          <text class="panel__title">徽章位已经准备好</text>
          <text class="panel__body">完成首次双人报告后，这里会先点亮一枚专属关系纪念徽章。</text>
        </view>

        <button
          class="invite-cta"
          :loading="creatingTestCode === (featuredModes[0]?.testCode || '')"
          @tap="createInvite(featuredModes[0]?.testCode || '')"
        >
          <text class="invite-cta__shine" />
          邀请朋友开始匹配
        </button>
      </template>
    </view>
    <TabBuddy />
  </view>
</template>

<style lang="scss" scoped>
.page {
  position: relative;
  min-height: 100vh;
  padding: 28rpx 24rpx calc(56rpx + env(safe-area-inset-bottom, 0rpx));
  overflow: hidden;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.92), rgba(255, 246, 239, 0.78) 46%, #fffaf7 100%);
}

.page__content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.page__glow,
.page__mesh {
  position: absolute;
  inset: auto;
  pointer-events: none;
}

.page__glow {
  width: 460rpx;
  height: 460rpx;
  border-radius: 50%;
  filter: blur(32px);
  opacity: 0.46;
}

.page__glow--violet {
  top: -110rpx;
  right: -120rpx;
  background: rgba(155, 126, 216, 0.28);
}

.page__glow--pink {
  bottom: 140rpx;
  left: -120rpx;
  background: rgba(232, 114, 154, 0.18);
}

.page__mesh {
  inset: 0;
  background-image:
    linear-gradient(rgba(155, 126, 216, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(232, 114, 154, 0.03) 1px, transparent 1px);
  background-size: 44rpx 44rpx;
  opacity: 0.4;
}

.surface-card {
  position: relative;
  overflow: hidden;
  border-radius: 36rpx;
  border: 1px solid rgba(155, 126, 216, 0.12);
  background: rgba(255, 255, 255, 0.76);
  box-shadow: 0 24rpx 64rpx rgba(155, 126, 216, 0.11);

  // #ifdef H5
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  // #endif

  // #ifdef MP-WEIXIN
  background: rgba(255, 255, 255, 0.94);
  // #endif
}

.hero {
  position: relative;
  padding: 32rpx 28rpx 30rpx;
  border-radius: 42rpx;
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.22), transparent 38%),
    linear-gradient(140deg, #7b64c7 0%, #9b7ed8 36%, #e8729a 100%);
  color: #fff;
  box-shadow: 0 28rpx 80rpx rgba(128, 91, 183, 0.28);
  animation: fadeInUp 0.55s $xc-ease both;
}

.hero__spark {
  position: absolute;
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  filter: blur(12px);
  opacity: 0.22;
}

.hero__spark--left {
  top: -16rpx;
  left: -18rpx;
  background: rgba(255, 255, 255, 0.42);
}

.hero__spark--right {
  right: 24rpx;
  bottom: 92rpx;
  background: rgba(255, 218, 229, 0.42);
}

.hero__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.hero__eyebrow,
.panel__eyebrow {
  font-size: 20rpx;
  letter-spacing: 4rpx;
  text-transform: uppercase;
}

.hero__eyebrow {
  color: rgba(255, 255, 255, 0.82);
}

.hero__badge {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.18);
  font-size: 20rpx;
  color: rgba(255, 255, 255, 0.92);
}

.hero__avatars {
  margin-top: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
}

.hero__avatar-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.hero__avatar {
  width: 122rpx;
  height: 122rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 54rpx;
  color: #47335f;
  border: 4rpx solid rgba(255, 255, 255, 0.72);
}

.hero__avatar--primary {
  background: rgba(255, 255, 255, 0.88);
}

.hero__avatar--secondary {
  background: rgba(255, 243, 247, 0.84);
}

.hero__avatar-name {
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.84);
}

.hero__orbit {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.16);
  font-size: 28rpx;
  animation: heartbeat 2.4s ease-in-out infinite;
}

.hero__title {
  display: block;
  margin-top: 22rpx;
  text-align: center;
  font-size: 50rpx;
  font-family: $xc-font-serif;
  font-weight: 700;
}

.hero__body {
  display: block;
  margin-top: 14rpx;
  text-align: center;
  font-size: 24rpx;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.92);
}

.hero__stats {
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.hero-stat {
  padding: 18rpx 12rpx 16rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.14);
  text-align: center;
}

.hero-stat__value {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.hero-stat__label {
  display: block;
  margin-top: 4rpx;
  font-size: 21rpx;
  color: rgba(255, 255, 255, 0.84);
}

.hero-stat__hint {
  display: block;
  margin-top: 6rpx;
  font-size: 18rpx;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.68);
}

.section-head {
  margin: 4rpx 4rpx 0;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18rpx;
}

.section-head__title {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.section-head__desc {
  display: block;
  margin-top: 6rpx;
  font-size: 22rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.section-head__meta {
  flex-shrink: 0;
  font-size: 22rpx;
  color: $xc-hint;
}

.panel {
  padding: 28rpx;
}

.panel__eyebrow {
  color: rgba(124, 93, 191, 0.54);
}

.panel__title {
  display: block;
  margin-top: 10rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-ink;
}

.panel__body {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel--error {
  border-color: rgba(232, 114, 154, 0.18);
}

.panel__button {
  margin-top: 18rpx;
  border-radius: 999rpx;
  @include btn-primary;
}

.mode-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.mode-card {
  padding: 22rpx;
}

.mode-card--violet {
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.55), transparent 34%),
    linear-gradient(155deg, rgba(123, 100, 199, 0.2), rgba(201, 181, 240, 0.08)),
    rgba(255, 255, 255, 0.78);
}

.mode-card--peach {
  background:
    radial-gradient(circle at top right, rgba(255, 255, 255, 0.58), transparent 36%),
    linear-gradient(155deg, rgba(232, 114, 154, 0.18), rgba(255, 212, 189, 0.14)),
    rgba(255, 255, 255, 0.78);
}

.mode-card__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10rpx;
}

.mode-card__emoji {
  width: 64rpx;
  height: 64rpx;
  border-radius: 20rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.74);
  font-size: 30rpx;
}

.mode-card__badge {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(124, 93, 191, 0.08);
  font-size: 18rpx;
  color: $xc-purple;
}

.mode-card__title {
  display: block;
  margin-top: 18rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-ink;
}

.mode-card__desc {
  display: block;
  margin-top: 10rpx;
  font-size: 22rpx;
  line-height: 1.7;
  color: $xc-muted;
  min-height: 150rpx;
}

.mode-card__note {
  display: block;
  margin-top: 12rpx;
  font-size: 20rpx;
  color: $xc-hint;
}

.mode-card__button {
  margin-top: 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(124, 93, 191, 0.12);
  color: $xc-purple;
  font-size: 22rpx;
  font-weight: 600;
}

.leaderboard,
.history-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.leaderboard-card {
  padding: 18rpx 20rpx;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 16rpx;
}

.leaderboard-card__rank {
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 800;
}

.leaderboard-card__rank--gold {
  background: linear-gradient(135deg, #fff3d8, #f5d78b);
  color: #b6831d;
}

.leaderboard-card__rank--silver {
  background: linear-gradient(135deg, #f6f7fb, #d8dce8);
  color: #768099;
}

.leaderboard-card__rank--bronze {
  background: linear-gradient(135deg, #f7ead8, #e9c39a);
  color: #a86b32;
}

.leaderboard-card__pair {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.leaderboard-card__avatars {
  display: flex;
  align-items: center;
}

.leaderboard-card__avatar,
.leaderboard-card__heart {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.leaderboard-card__avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: rgba(155, 126, 216, 0.16);
  font-size: 24rpx;
}

.leaderboard-card__heart {
  margin: 0 6rpx;
  font-size: 18rpx;
  color: $xc-pink;
}

.leaderboard-card__copy {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.leaderboard-card__name {
  font-size: 25rpx;
  font-weight: 700;
  color: $xc-ink;
}

.leaderboard-card__meta {
  font-size: 21rpx;
  color: $xc-muted;
}

.leaderboard-card__score {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2rpx;
}

.leaderboard-card__score-value {
  font-size: 32rpx;
  font-weight: 800;
  color: $xc-purple-d;
}

.leaderboard-card__score-label {
  font-size: 18rpx;
  color: $xc-hint;
}

.history-card {
  padding: 20rpx;
}

.history-card__top,
.history-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.history-card__copy {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.history-card__title {
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-ink;
}

.history-card__meta,
.history-card__time {
  font-size: 22rpx;
  color: $xc-muted;
}

.history-card__status {
  flex-shrink: 0;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  font-size: 20rpx;
  font-weight: 600;
}

.history-card__status--waiting {
  background: rgba(255, 211, 142, 0.22);
  color: #b77a1f;
}

.history-card__status--running {
  background: rgba(155, 126, 216, 0.14);
  color: $xc-purple-d;
}

.history-card__status--done {
  background: rgba(71, 190, 158, 0.16);
  color: #248167;
}

.history-card__meter {
  margin-top: 18rpx;
  height: 12rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(124, 93, 191, 0.08);
}

.history-card__meter-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #9b7ed8, #e8729a);
}

.history-card__foot {
  margin-top: 16rpx;
}

.history-card__score {
  font-size: 21rpx;
  color: $xc-purple-d;
}

.badge-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.badge-card {
  min-height: 188rpx;
  padding: 20rpx 12rpx 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  text-align: center;
}

.badge-card__halo {
  position: absolute;
  top: -26rpx;
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(232, 114, 154, 0.24), transparent 70%);
  filter: blur(6px);
}

.badge-card__emoji {
  position: relative;
  font-size: 42rpx;
}

.badge-card__name {
  position: relative;
  font-size: 22rpx;
  line-height: 1.5;
  color: $xc-ink;
  font-weight: 600;
}

.badge-card__time {
  position: relative;
  font-size: 18rpx;
  line-height: 1.4;
  color: $xc-hint;
}

.invite-cta {
  position: relative;
  overflow: hidden;
  margin-top: 10rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #7c5dbf, #e8729a);
  color: #fff;
  font-size: 28rpx;
  font-weight: 700;
  box-shadow: 0 24rpx 48rpx rgba(155, 126, 216, 0.22);
}

.invite-cta__shine {
  position: absolute;
  top: -28rpx;
  left: -120rpx;
  width: 120rpx;
  height: calc(100% + 56rpx);
  transform: rotate(18deg);
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.36), transparent);
  animation: shineSweep 2.8s ease-in-out infinite;
}

@keyframes shineSweep {
  0%,
  18% {
    transform: translateX(0) rotate(18deg);
  }

  55%,
  100% {
    transform: translateX(760rpx) rotate(18deg);
  }
}
</style>
