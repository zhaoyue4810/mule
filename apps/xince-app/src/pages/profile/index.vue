<script setup lang="ts">
import { computed, getCurrentInstance, ref } from "vue";
import { onReady, onShow, onUnload } from "@dcloudio/uni-app";

import CelebrationOverlay from "@/components/feedback/CelebrationOverlay.vue";
import BottomSheet from "@/components/common/BottomSheet.vue";
import TabBuddy from "@/components/mascot/TabBuddy.vue";
import XiaoCe from "@/components/mascot/XiaoCe.vue";
import PersonaRadarCanvas from "@/components/profile/PersonaRadarCanvas.vue";
import ProfileBadgesPanel from "@/components/profile/ProfileBadgesPanel.vue";
import ProfileHeaderStats from "@/components/profile/ProfileHeaderStats.vue";
import ProfileHistoryPanel from "@/components/profile/ProfileHistoryPanel.vue";
import type { TimeCapsuleItem } from "@/shared/models/capsule";
import type {
  AppProfileOverview,
  DailyQuestionStatePayload,
  ProfileBadgeItem,
  ProfileSettingsPayload,
  ProfileReportHistoryItem,
} from "@/shared/models/profile";
import type { AuthUserPayload } from "@/shared/models/auth";
import type {
  CalendarDayDetail,
  CalendarStatsPayload,
} from "@/shared/models/calendar";
import {
  bindPhone,
  ensureAppSession,
  getSessionUser,
  loginWithWechatMiniProgram,
  sendPhoneCode,
} from "@/shared/services/auth";
import {
  fetchMyDailyQuestion,
  fetchMyProfileOverview,
  fetchMyProfileSettings,
  fetchMyProfileReports,
  submitMyDailyQuestion,
  updateMyProfileSettings,
} from "@/shared/services/profile";
import { fetchTimeCapsules as fetchCapsules } from "@/shared/services/capsule";
import type { MemoryGreetingPayload, MemorySuggestPayload } from "@/shared/models/memory";
import { fetchMemoryGreeting, fetchMemorySuggest } from "@/shared/services/memory";
import {
  fetchCalendarMonth,
  fetchCalendarStats,
  fetchCalendarYear,
  recordCalendarMood,
} from "@/shared/services/calendar";
import { SoundManager } from "@/shared/utils/sound-manager";

type CelebrationBadgeSummary = DailyQuestionStatePayload["unlocked_badges"][number];
type CalendarGridCell = { key: string; empty: boolean; item?: CalendarDayDetail };

const overview = ref<AppProfileOverview | null>(null);
const reports = ref<ProfileReportHistoryItem[]>([]);
const loading = ref(false);
const error = ref("");
const sessionUser = ref<AuthUserPayload | null>(null);
const phone = ref("");
const code = ref("");
const sendingCode = ref(false);
const bindingPhone = ref(false);
const linkingWechat = ref(false);
const debugCode = ref("");
const dailyQuestion = ref<DailyQuestionStatePayload | null>(null);
const dailyQuestionSubmitting = ref(false);
const isWechatMiniProgram = ref(false);
const celebrationVisible = ref(false);
const celebrationBadges = ref<CelebrationBadgeSummary[]>([]);
const celebrationTitle = ref("太棒了！");
const celebrationMessage = ref("新的成长印记已经点亮。");
const calendarView = ref<"month" | "year">("month");
const calendarMonth = ref(new Date().getMonth() + 1);
const calendarYear = ref(new Date().getFullYear());
const calendarMonthItems = ref<CalendarDayDetail[]>([]);
const calendarYearItems = ref<CalendarDayDetail[]>([]);
const calendarStats = ref<CalendarStatsPayload | null>(null);
const calendarLoading = ref(false);
const calendarSelectedDay = ref<CalendarDayDetail | null>(null);
const fragmentInsight = ref<{ title: string; emoji: string; body: string } | null>(null);
const moodSaving = ref(false);
const capsules = ref<TimeCapsuleItem[]>([]);
const profileSettings = ref<ProfileSettingsPayload | null>(null);
const savingSound = ref(false);
const greeting = ref<MemoryGreetingPayload | null>(null);
const memorySuggest = ref<MemorySuggestPayload | null>(null);
const soulExpanded = ref(false);
const statsAnimated = ref(false);
const statDisplay = ref({
  testCount: 0,
  matchCount: 0,
  pendingCount: 0,
});
const selectedBadge = ref<ProfileBadgeItem | null>(null);
const badgeSheetVisible = computed({
  get: () => Boolean(selectedBadge.value),
  set: (value: boolean) => {
    if (!value) {
      selectedBadge.value = null;
    }
  },
});
let statsObserver: UniApp.IntersectionObserver | null = null;
const instance = getCurrentInstance();

function playIfEnabled(type: "chime" | "ding" | "whoosh" | "ambient") {
  if (SoundManager.isSoundEnabled()) {
    SoundManager.play(type);
  }
}

// #ifdef MP-WEIXIN
isWechatMiniProgram.value = true;
// #endif

const hasProfile = computed(() => Boolean(overview.value));
const canSubmitPhoneBind = computed(
  () => phone.value.trim().length >= 11 && code.value.trim().length >= 4,
);
const calendarHeatmapWeeks = computed(() => {
  const items = overview.value?.calendar_heatmap || [];
  const weeks: typeof items[] = [];
  for (let index = 0; index < items.length; index += 7) {
    weeks.push(items.slice(index, index + 7));
  }
  return weeks;
});
const calendarMonthGrid = computed(() => {
  const firstDay = new Date(calendarYear.value, calendarMonth.value - 1, 1).getDay();
  const leading: CalendarGridCell[] = Array.from({ length: firstDay }, (_, index) => ({
    key: `leading-${index}`,
    empty: true,
  }));
  const actual: CalendarGridCell[] = calendarMonthItems.value.map((item) => ({
    key: item.date,
    empty: false,
    item,
  }));
  return [...leading, ...actual];
});
const calendarYearWeeks = computed(() => {
  const firstDay = new Date(calendarYear.value, 0, 1).getDay();
  const placeholders: CalendarGridCell[] = Array.from({ length: firstDay }, (_, index) => ({
    key: `y-leading-${index}`,
    empty: true,
  }));
  const actual: CalendarGridCell[] = calendarYearItems.value.map((item) => ({
    key: item.date,
    empty: false,
    item,
  }));
  const allItems: CalendarGridCell[] = [...placeholders, ...actual];
  const weeks: CalendarGridCell[][] = [];
  for (let index = 0; index < allItems.length; index += 7) {
    weeks.push(allItems.slice(index, index + 7));
  }
  return weeks;
});
const fragmentColumns = computed(() => {
  if (!overview.value) {
    return [];
  }
  const categoryEmoji: Record<string, string> = {
    personality: "🪞",
    emotion: "💗",
    relationship: "🤝",
    creativity: "✨",
    inner: "🌙",
  };
  return overview.value.fragment_progress.map((category) => ({
    ...category,
    emoji: categoryEmoji[category.category_code] || "🧩",
    items: overview.value?.fragment_map.filter(
      (item) => item.category === category.category_code,
    ) || [],
  }));
});
const miniStats = computed(() => [
  {
    label: "连续天数",
    value: `${calendarStats.value?.current_streak || 0}`,
  },
  {
    label: "活跃天数",
    value: `${calendarStats.value?.active_days || 0}`,
  },
  {
    label: "平均心情",
    value: `${calendarStats.value?.average_mood || 0}`,
  },
  {
    label: "最佳连续",
    value: `${calendarStats.value?.best_streak || 0}`,
  },
]);
const calendarTone = computed(() => {
  const mood = calendarStats.value?.average_mood || 0;
  if (mood >= 4.5) {
    return {
      emoji: "☀️",
      title: "晴空高能",
      body: "最近的状态很亮，适合去开启一段新的探索。",
    };
  }
  if (mood >= 3.5) {
    return {
      emoji: "🌤️",
      title: "微风顺流",
      body: "节奏稳定而柔和，适合把灵感继续推进一点点。",
    };
  }
  if (mood >= 2.5) {
    return {
      emoji: "⛅",
      title: "云层轻覆",
      body: "最近稍微有点慢下来，记录会帮你重新看见自己的变化。",
    };
  }
  if (mood > 0) {
    return {
      emoji: "🌧️",
      title: "细雨修复",
      body: "先温柔照顾自己，留下一点心情，也是在收集能量。",
    };
  }
  return {
    emoji: "🌙",
    title: "等待落笔",
    body: "从今天开始记录之后，这里会慢慢形成专属于你的天气图。",
  };
});
const calendarActivityTotal = computed(() =>
  (overview.value?.calendar_heatmap || []).reduce(
    (total, item) => total + item.activity_count,
    0,
  ),
);
const dailyQuestionOptionCards = computed(() =>
  (dailyQuestion.value?.options || []).map((option, index) => ({
    option,
    index,
    label: String.fromCharCode(65 + index),
    emoji: ["🕊️", "🌸", "⚡", "🌙", "💭", "✨"][index % 6],
  })),
);
const retroQuestionCards = computed(() =>
  (dailyQuestion.value?.retroactive_dates || []).map((date, index) => ({
    date,
    emoji: ["🪄", "🌙", "💌"][index % 3],
  })),
);
const todayDateText = `${new Date().getFullYear()}-${`${new Date().getMonth() + 1}`.padStart(2, "0")}-${`${new Date().getDate()}`.padStart(2, "0")}`;
const matchReports = computed(() =>
  reports.value.filter(
    (item) =>
      item.test_name.includes("匹配") ||
      item.test_name.toLowerCase().includes("match") ||
      item.test_code.toLowerCase().includes("match"),
  ),
);
const pendingUnlockCount = computed(() => {
  if (!overview.value?.fragment_progress?.length) {
    return 0;
  }
  return overview.value.fragment_progress.reduce(
    (total, item) => total + Math.max(0, item.total_count - item.unlocked_count),
    0,
  );
});
const fragmentCompletionRate = computed(() => {
  const total = overview.value?.fragment_progress.reduce(
    (sum, item) => sum + item.total_count,
    0,
  ) || 0;
  if (!total) {
    return 0;
  }
  const unlocked = overview.value?.fragment_progress.reduce(
    (sum, item) => sum + item.unlocked_count,
    0,
  ) || 0;
  return Math.round((unlocked / total) * 100);
});
const fragmentCompletedCount = computed(() =>
  overview.value?.fragment_progress.filter((item) => item.completed).length || 0,
);
const statTargets = computed(() => ({
  testCount: overview.value?.test_count || 0,
  matchCount: matchReports.value.length,
  pendingCount: pendingUnlockCount.value,
}));
const soulRadarDimensions = computed(() => {
  const source = overview.value?.dominant_dimensions || [];
  if (!source.length) {
    return [];
  }
  const max = Math.max(...source.map((item) => item.total_score), 1);
  return source.slice(0, 5).map((item) => ({
    dim_code: item.dim_code,
    label: item.dim_code.toUpperCase(),
    score: Math.round((item.total_score / max) * 100),
  }));
});
const soulLevel = computed(() => {
  const score = (overview.value?.test_count || 0) * 12 + (overview.value?.distinct_test_count || 0) * 8;
  return Math.max(1, Math.min(99, Math.floor(score / 10) + 1));
});
const soulProgress = computed(() => Math.max(6, Math.min(98, ((overview.value?.test_count || 0) % 8) * 12 + 8)));
const soloBadges = computed(() =>
  (overview.value?.badges || []).filter((item) => {
    const key = item.badge_key.toLowerCase();
    return !key.includes("match") && !key.includes("duo") && !key.includes("pair") && !key.includes("cp");
  }),
);
const duoBadges = computed(() =>
  (overview.value?.badges || []).filter((item) => {
    const key = item.badge_key.toLowerCase();
    return key.includes("match") || key.includes("duo") || key.includes("pair") || key.includes("cp");
  }),
);
const capsuleUnlockedCount = computed(() =>
  capsules.value.filter((item) => item.is_unlocked).length,
);
const accountStatusCards = computed(() => [
  {
    key: "session",
    emoji: sessionUser.value?.is_guest ? "👣" : "🪪",
    title: sessionUser.value?.is_guest ? "访客档案" : "正式账号",
    body: sessionUser.value?.is_guest
      ? "当前记录保存在这台设备里，建议尽快绑定，避免换设备后丢失。"
      : "你的灵魂档案会跟随账号同步，跨设备也能继续接力。",
  },
  {
    key: "wechat",
    emoji: "💬",
    title:
      isWechatMiniProgram.value && sessionUser.value?.has_openid
        ? "已连接微信"
        : "微信身份",
    body: isWechatMiniProgram.value
      ? sessionUser.value?.has_openid
        ? "小程序内会优先复用当前身份，回到测试时不用重新建立新档案。"
        : "还可以升级成微信身份，并把当前记录完整保留下来。"
      : "H5 先保留轻量体验，进入小程序后也能继续升级身份。",
  },
  {
    key: "phone",
    emoji: "📱",
    title: sessionUser.value?.has_phone ? "手机号已绑定" : "手机号未绑定",
    body: sessionUser.value?.has_phone
      ? `当前账号已绑定 ${sessionUser.value.masked_phone || "手机号"}，验证码登录和历史同步已开启。`
      : "绑定手机号后，测试记录、报告、碎片与徽章都能跨设备找回。",
  },
]);
const settingMenuItems = computed(() => [
  {
    key: "edit" as const,
    icon: "👤",
    label: "编辑资料",
    description: "更新头像、昵称和签名，让你的名片更像现在的你。",
  },
  {
    key: "sound" as const,
    icon: "🔊",
    label: "声音与触感",
    description: "控制音效、轻触反馈和答题时的沉浸感节奏。",
  },
  {
    key: "notify" as const,
    icon: "🔔",
    label: "通知设置",
    description: "集中查看匹配提醒、报告生成和系统动态。",
  },
  {
    key: "privacy" as const,
    icon: "🛡️",
    label: "隐私设置",
    description: "管理资料展示和数据可见范围，保护你的灵魂档案。",
  },
  {
    key: "about" as const,
    icon: "💜",
    label: "关于心测",
    description: "查看品牌介绍、核心能力与版本说明。",
  },
]);
const memoryLevel = computed(() => {
  const value = greeting.value?.know_level || 0;
  if (value >= 85) {
    return "灵魂挚友";
  }
  if (value >= 60) {
    return "熟悉同路人";
  }
  if (value >= 35) {
    return "正在了解你";
  }
  return "初识心动";
});
const memoryRecent = computed(() => {
  const latest = reports.value[0];
  if (!latest) {
    return "最近互动：还没有新的记录";
  }
  return `最近互动：${formatTime(latest.completed_at)} · ${latest.test_name}`;
});

function formatTime(value?: string | null) {
  if (!value) {
    return "暂未记录";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  const hour = `${date.getHours()}`.padStart(2, "0");
  const minute = `${date.getMinutes()}`.padStart(2, "0");
  return `${month}-${day} ${hour}:${minute}`;
}

function parseDate(value: string) {
  return new Date(`${value}T00:00:00`);
}

function formatDayLabel(value: string) {
  const date = parseDate(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

function formatCalendarCell(value: string) {
  const date = parseDate(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getDate()}`;
}

function isToday(value?: string) {
  return Boolean(value && value === todayDateText);
}

function heatmapClass(intensity: number) {
  return `heatmap-cell--level-${Math.max(0, Math.min(intensity, 4))}`;
}

function formatCalendarTitle() {
  return `${calendarYear.value} 年 ${calendarMonth.value} 月`;
}

function openCalendarDay(item: CalendarDayDetail) {
  calendarSelectedDay.value = item;
}

function closeCalendarDay() {
  calendarSelectedDay.value = null;
}

async function updateCalendarMood(moodLevel: number) {
  if (!calendarSelectedDay.value || moodSaving.value) {
    return;
  }
  moodSaving.value = true;
  try {
    calendarStats.value = await recordCalendarMood(
      moodLevel,
      calendarSelectedDay.value.date,
    );
    await loadCalendar();
    calendarSelectedDay.value = calendarMonthItems.value.find(
      (item) => item.date === calendarSelectedDay.value?.date,
    ) || calendarYearItems.value.find((item) => item.date === calendarSelectedDay.value?.date) || null;
    playIfEnabled("ding");
    uni.showToast({
      title: "心情已记录",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "记录失败",
      icon: "none",
    });
  } finally {
    moodSaving.value = false;
  }
}

async function changeCalendarMonth(step: number) {
  const nextDate = new Date(calendarYear.value, calendarMonth.value - 1 + step, 1);
  calendarYear.value = nextDate.getFullYear();
  calendarMonth.value = nextDate.getMonth() + 1;
  await loadCalendar();
}

async function toggleCalendarView(view: "month" | "year") {
  if (calendarView.value === view) {
    return;
  }
  calendarView.value = view;
  await loadCalendar();
}

function showBadgeCelebration(
  badges: CelebrationBadgeSummary[],
  title = "太棒了！",
  message = "新的成长印记已经点亮。",
) {
  if (!badges.length) {
    return;
  }
  celebrationBadges.value = badges;
  celebrationTitle.value = title;
  celebrationMessage.value = message;
  celebrationVisible.value = true;
}

function closeCelebration() {
  celebrationVisible.value = false;
}

function openFragmentInsight(title: string, emoji: string, body: string) {
  fragmentInsight.value = { title, emoji, body };
}

function closeFragmentInsight() {
  fragmentInsight.value = null;
}

function openBadgeDetail(item: ProfileBadgeItem) {
  selectedBadge.value = item;
}

function closeBadgeDetail() {
  selectedBadge.value = null;
}

async function loadCalendar() {
  calendarLoading.value = true;
  try {
    const [monthPayload, yearPayload, statsPayload] = await Promise.all([
      fetchCalendarMonth(calendarYear.value, calendarMonth.value),
      fetchCalendarYear(calendarYear.value),
      fetchCalendarStats(calendarYear.value),
    ]);
    calendarMonthItems.value = monthPayload.items;
    calendarYearItems.value = yearPayload.items;
    calendarStats.value = statsPayload;
  } finally {
    calendarLoading.value = false;
  }
}

function openReport(recordId: number) {
  uni.navigateTo({
    url: `/pages/test/result?recordId=${recordId}`,
  });
}

function goHome() {
  uni.switchTab({
    url: "/pages/home/index",
  });
}

function goPersonaCard() {
  uni.navigateTo({
    url: "/pages/profile/persona-card",
  });
}

function goSettings() {
  uni.navigateTo({
    url: "/pages/profile/settings",
  });
}

async function loadProfile() {
  overview.value = null;
  reports.value = [];
  error.value = "";

  loading.value = true;
  try {
    sessionUser.value = await ensureAppSession();
    const [overviewPayload, reportPayload] = await Promise.all([
      fetchMyProfileOverview(),
      fetchMyProfileReports(),
    ]);
    const [memoryGreetingPayload, memorySuggestPayload] = await Promise.all([
      fetchMemoryGreeting().catch(() => null),
      fetchMemorySuggest().catch(() => null),
    ]);
    await loadCalendar();
    overview.value = overviewPayload;
    reports.value = reportPayload;
    greeting.value = memoryGreetingPayload;
    memorySuggest.value = memorySuggestPayload;
    dailyQuestion.value = await fetchMyDailyQuestion();
    capsules.value = (await fetchCapsules()).items;
    profileSettings.value = await fetchMyProfileSettings();
  } catch (err) {
    if (
      err instanceof Error &&
      (err.message.includes("Authorization required") ||
        err.message.includes("Token"))
    ) {
      sessionUser.value = await ensureAppSession();
      return;
    }
    error.value = err instanceof Error ? err.message : "个人中心加载失败";
  } finally {
    loading.value = false;
  }
}

async function toggleSoundSetting(value: boolean) {
  if (savingSound.value) {
    return;
  }
  savingSound.value = true;
  try {
    profileSettings.value = await updateMyProfileSettings({
      sound_enabled: value,
    });
    uni.showToast({
      title: value ? "声音已开启" : "声音已关闭",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "设置失败",
      icon: "none",
    });
  } finally {
    savingSound.value = false;
  }
}

function onProfileSoundSwitchChange(event: { detail: { value: boolean } }) {
  void toggleSoundSetting(Boolean(event.detail.value));
}

function formatRetroDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

function badgeTierLabel(tier: number) {
  return ["铜", "银", "金", "钻"][Math.max(0, Math.min(3, tier - 1))] || "铜";
}

async function answerDailyQuestion(answerIndex: number, answerDate?: string) {
  if (
    dailyQuestionSubmitting.value ||
    !dailyQuestion.value ||
    dailyQuestion.value.answered
  ) {
    return;
  }
  dailyQuestionSubmitting.value = true;
  try {
    const nextDailyQuestion = await submitMyDailyQuestion(
      dailyQuestion.value.question_id,
      answerIndex,
      answerDate,
    );
    dailyQuestion.value = nextDailyQuestion;
    if (nextDailyQuestion.unlocked_badges?.length) {
      showBadgeCelebration(
        nextDailyQuestion.unlocked_badges,
        "勋章已解锁",
        answerDate
          ? "补签成功，你的连续成长轨迹又被补上一块。"
          : "今天的回答留下了新的印记，也点亮了一枚勋章。",
      );
    }
    await loadProfile();
    uni.showToast({
      title: answerDate ? "补签已记录" : "今日心情已记录",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "提交失败",
      icon: "none",
    });
  } finally {
    dailyQuestionSubmitting.value = false;
  }
}

async function sendCode() {
  if (sendingCode.value || phone.value.trim().length < 11) {
    return;
  }
  sendingCode.value = true;
  try {
    const payload = await sendPhoneCode(phone.value.trim());
    debugCode.value = payload.debug_code || "";
    uni.showToast({
      title: payload.debug_code ? `验证码 ${payload.debug_code}` : "验证码已发送",
      icon: "none",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "发送失败",
      icon: "none",
    });
  } finally {
    sendingCode.value = false;
  }
}

async function submitPhoneBind() {
  if (bindingPhone.value || !canSubmitPhoneBind.value) {
    return;
  }
  bindingPhone.value = true;
  try {
    const session = await bindPhone(phone.value.trim(), code.value.trim());
    sessionUser.value = session.user;
    code.value = "";
    debugCode.value = "";
    await loadProfile();
    uni.showToast({
      title: "手机号已绑定",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title: err instanceof Error ? err.message : "绑定失败",
      icon: "none",
    });
  } finally {
    bindingPhone.value = false;
  }
}

async function linkWechatIdentity() {
  if (linkingWechat.value) {
    return;
  }
  linkingWechat.value = true;
  try {
    const session = await loginWithWechatMiniProgram(
      sessionUser.value?.nickname || "微信用户",
      sessionUser.value?.avatar_value || "🧠",
    );
    sessionUser.value = session.user;
    await loadProfile();
    uni.showToast({
      title: "已升级为微信身份",
      icon: "success",
    });
  } catch (err) {
    uni.showToast({
      title:
        err instanceof Error &&
        err.message.includes("credentials are not configured")
          ? "后端还没配置微信小程序凭证"
          : err instanceof Error
            ? err.message
            : "微信升级失败",
      icon: "none",
    });
  } finally {
    linkingWechat.value = false;
  }
}

function startStatsCountUp() {
  if (statsAnimated.value) {
    return;
  }
  statsAnimated.value = true;
  const targets = statTargets.value;
  const keys: Array<keyof typeof targets> = ["testCount", "matchCount", "pendingCount"];
  keys.forEach((key, index) => {
    const timer = setInterval(() => {
      const now = statDisplay.value[key];
      const target = targets[key];
      if (now >= target) {
        clearInterval(timer);
        return;
      }
      const step = Math.max(1, Math.ceil((target - now) / 8));
      statDisplay.value = {
        ...statDisplay.value,
        [key]: Math.min(target, now + step),
      };
    }, 28 + index * 12);
  });
}

function initStatsObserver() {
  if (!instance?.proxy) {
    return;
  }
  statsObserver?.disconnect();
  statsObserver = uni.createIntersectionObserver(instance.proxy, { observeAll: false });
  statsObserver.relativeToViewport({ bottom: 0 }).observe(".stats", (res) => {
    if (res.intersectionRatio > 0.3) {
      startStatsCountUp();
    }
  });
}

function openSettingItem(type: "edit" | "sound" | "notify" | "privacy" | "about") {
  if (type === "edit") {
    uni.navigateTo({
      url: "/pages/profile/edit-profile",
    });
    return;
  }
  if (type === "sound") {
    goSettings();
    return;
  }
  if (type === "notify") {
    uni.navigateTo({
      url: "/pages/profile/notifications",
    });
    return;
  }
  if (type === "about") {
    uni.navigateTo({
      url: "/pages/profile/about",
    });
    return;
  }
  uni.showToast({
    title: "即将上线",
    icon: "none",
  });
}

onShow(() => {
  sessionUser.value = getSessionUser();
  loadProfile();
});

onReady(() => {
  initStatsObserver();
});

onUnload(() => {
  statsObserver?.disconnect();
  statsObserver = null;
});
</script>

<template>
  <view class="page">
    <view class="page__glow page__glow--violet" />
    <view class="page__glow page__glow--pink" />
    <view class="page__mesh" />
    <view class="page__content">
    <view v-if="!hasProfile && !loading && !error" class="panel panel--empty">
      <text class="panel__title">你的旅程还没开始</text>
      <text class="panel__body">
        当前设备还没有生成过测试记录。先去完成一套已发布测试，这里就会自动出现你的历史结果和基础画像。
      </text>
      <button class="panel__button" @tap="goHome">去首页开始测试</button>
    </view>

    <view v-else-if="loading" class="panel">
      <text class="panel__body">正在加载你的记录与画像...</text>
    </view>

    <view v-else-if="error" class="panel panel--error">
      <text class="panel__title">加载失败</text>
      <text class="panel__body">{{ error }}</text>
      <button class="panel__button" @tap="loadProfile">重新加载</button>
    </view>

    <view v-else-if="overview" class="profile">
      <ProfileHeaderStats
        :overview="overview"
        :greeting-text="greeting?.greeting || '灵魂说明书正在慢慢生成中'"
        :stat-display="statDisplay"
        @go-persona-card="goPersonaCard"
        @go-settings="goSettings"
      />

      <view class="panel soul-panel">
        <view class="panel__head">
          <text class="panel__title">灵魂画像</text>
          <text class="panel__head-link" @tap="soulExpanded = !soulExpanded">
            {{ soulExpanded ? "收起详情" : "展开详情" }}
          </text>
        </view>
        <view class="soul-panel__main">
          <view class="soul-panel__radar">
            <PersonaRadarCanvas :dimensions="soulRadarDimensions" />
          </view>
          <view class="soul-panel__meta">
            <text class="soul-panel__level">Lv.{{ soulLevel }} 灵魂等级</text>
            <view class="soul-panel__track">
              <view class="soul-panel__fill" :style="{ width: `${soulProgress}%` }" />
            </view>
            <text class="soul-panel__progress">距离下一级 {{ 100 - soulProgress }}%</text>
            <view class="soul-panel__tags">
              <text v-for="item in overview.dominant_dimensions" :key="item.dim_code" class="soul-tag">
                {{ item.dim_code.toUpperCase() }}
              </text>
            </view>
          </view>
        </view>
        <view v-if="soulExpanded" class="rows rows--soft">
          <view v-for="item in overview.dominant_dimensions" :key="`${item.dim_code}-detail`" class="row row--soft">
            <text class="row__name">{{ item.dim_code.toUpperCase() }}</text>
            <text class="row__value">{{ item.total_score.toFixed(2) }}</text>
          </view>
        </view>
      </view>

      <view class="panel memory-panel">
        <view class="memory-panel__head">
          <XiaoCe expression="happy" size="sm" :animated="true" />
          <text class="panel__title">小测的记忆</text>
        </view>
        <text class="panel__body">{{ greeting?.greeting || "小测正在学习你的节奏" }}</text>
        <view class="memory-panel__track">
          <view class="memory-panel__fill" :style="{ width: `${greeting?.know_level || 0}%` }" />
        </view>
        <text class="memory-panel__meta">
          熟悉度 {{ greeting?.know_level || 0 }}% · {{ memoryLevel }}
        </text>
        <text class="memory-panel__meta">{{ memoryRecent }}</text>
        <text class="memory-panel__meta">
          个性化推荐：{{ memorySuggest?.items?.[0]?.name || "去首页看看今日推荐测试" }}
        </text>
      </view>

      <ProfileHistoryPanel
        :reports="reports"
        :match-reports="matchReports"
        @open-report="openReport"
      />

      <ProfileBadgesPanel
        :solo-badges="soloBadges"
        :duo-badges="duoBadges"
        :show-duo-hint="Boolean(matchReports.length)"
        @open-badge="openBadgeDetail"
      />

      <view class="panel panel--calendar" v-if="overview.calendar_heatmap.length">
        <view class="calendar-hero">
          <view class="calendar-hero__copy">
            <text class="panel__eyebrow">MOOD CALENDAR</text>
            <text class="panel__title">运势晴雨图</text>
            <text class="panel__body">
              日历会汇总测试完成、每日一问、手动心情和碎片收集等事件，点开单元格可查看详情并补记心情。
            </text>
          </view>
          <view class="calendar-hero__badge">
            <text class="calendar-hero__emoji">{{ calendarTone.emoji }}</text>
            <text class="calendar-hero__label">{{ calendarTone.title }}</text>
            <text class="calendar-hero__desc">{{ calendarTone.body }}</text>
          </view>
        </view>
        <view class="calendar-callouts">
          <text class="calendar-callout">🔥 连续 {{ calendarStats?.current_streak || 0 }} 天</text>
          <text class="calendar-callout">🫧 共记录 {{ calendarActivityTotal }} 次</text>
          <text class="calendar-callout">📍 {{ calendarView === "month" ? "月度视图" : "年度视图" }}</text>
        </view>
        <view class="calendar-stats">
          <view v-for="item in miniStats" :key="item.label" class="calendar-stats__card">
            <text class="calendar-stats__value">{{ item.value }}</text>
            <text class="calendar-stats__label">{{ item.label }}</text>
          </view>
        </view>
        <view class="calendar-controls">
          <view class="calendar-toggle">
            <button
              class="calendar-toggle__button"
              :class="{ 'calendar-toggle__button--active': calendarView === 'month' }"
              @tap="toggleCalendarView('month')"
            >
              月
            </button>
            <button
              class="calendar-toggle__button"
              :class="{ 'calendar-toggle__button--active': calendarView === 'year' }"
              @tap="toggleCalendarView('year')"
            >
              年
            </button>
          </view>
          <text class="calendar-panel__all" @tap="toggleCalendarView('year')">切到全年总览</text>
        </view>
        <view class="calendar-toolbar">
          <button class="calendar-toolbar__arrow" @tap="changeCalendarMonth(-1)">‹</button>
          <text class="calendar-toolbar__title">{{ formatCalendarTitle() }}</text>
          <button class="calendar-toolbar__arrow" @tap="changeCalendarMonth(1)">›</button>
        </view>
        <view v-if="calendarLoading" class="calendar-loading">
          <text class="panel__body">正在整理你的日历轨迹...</text>
        </view>
        <view v-else-if="calendarView === 'month'" class="calendar-month">
          <view class="calendar-weekdays">
            <text v-for="weekday in ['日', '一', '二', '三', '四', '五', '六']" :key="weekday">
              {{ weekday }}
            </text>
          </view>
          <view class="calendar-month__grid">
            <view
              v-for="cell in calendarMonthGrid"
              :key="cell.key"
              class="calendar-month__cell"
              :class="[
                cell.empty ? 'calendar-month__cell--empty' : heatmapClass(cell.item?.intensity || 0),
                !cell.empty && isToday(cell.item?.date) ? 'calendar-month__cell--today' : '',
              ]"
              @tap="cell.item && openCalendarDay(cell.item)"
            >
              <template v-if="cell.item">
                <text class="calendar-month__date">{{ formatCalendarCell(cell.item.date) }}</text>
                <text class="calendar-month__emoji">{{ cell.item.mood_emoji || '·' }}</text>
              </template>
            </view>
          </view>
        </view>
        <scroll-view v-else scroll-x class="calendar-year">
          <view class="calendar-year__grid">
            <view
              v-for="(week, weekIndex) in calendarYearWeeks"
              :key="`year-${weekIndex}`"
              class="calendar-year__week"
            >
              <view
                v-for="cell in week"
                :key="cell.key"
                class="calendar-year__cell"
                :class="[
                  cell.empty ? 'calendar-year__cell--empty' : heatmapClass(cell.item?.intensity || 0),
                  !cell.empty && isToday(cell.item?.date) ? 'calendar-year__cell--today' : '',
                ]"
                @tap="cell.item && openCalendarDay(cell.item)"
              >
                <text v-if="cell.item && cell.item.mood_emoji" class="calendar-year__emoji">
                  {{ cell.item.mood_emoji }}
                </text>
              </view>
            </view>
          </view>
        </scroll-view>
        <view class="calendar-legend">
          <view class="calendar-legend__item">
            <view class="calendar-legend__dot heatmap-cell--level-0" />
            <text>轻记录</text>
          </view>
          <view class="calendar-legend__item">
            <view class="calendar-legend__dot heatmap-cell--level-1" />
            <text>开始活跃</text>
          </view>
          <view class="calendar-legend__item">
            <view class="calendar-legend__dot heatmap-cell--level-2" />
            <text>状态在线</text>
          </view>
          <view class="calendar-legend__item">
            <view class="calendar-legend__dot heatmap-cell--level-4" />
            <text>高光时刻</text>
          </view>
        </view>
        <view class="heatmap heatmap--mini">
          <view
            v-for="(week, weekIndex) in calendarHeatmapWeeks"
            :key="`week-${weekIndex}`"
            class="heatmap__week"
          >
            <view
              v-for="item in week"
              :key="item.date"
              class="heatmap-cell"
              :class="heatmapClass(item.intensity)"
            >
              <text class="heatmap-cell__day">{{ formatDayLabel(item.date) }}</text>
              <text class="heatmap-cell__count">
                {{ item.activity_count > 0 ? item.activity_count : "-" }}
              </text>
            </view>
          </view>
        </view>
      </view>

      <view class="panel panel--daily" v-if="dailyQuestion">
        <view class="daily-question__hero">
          <view>
            <text class="panel__eyebrow">SOUL PROMPT</text>
            <text class="panel__title">今日灵魂一问</text>
          </view>
          <view class="daily-question__orb">{{ dailyQuestion.answered ? "✨" : "🪄" }}</view>
        </view>
        <view class="daily-question__question-card">
          <text class="daily-question__date">记录于 {{ formatDayLabel(dailyQuestion.answer_date) }}</text>
          <text class="daily-question__question">{{ dailyQuestion.question_text }}</text>
        </view>
        <view class="daily-question-stats">
          <view class="daily-question-stat">
            <text class="daily-question-stat__value">{{ dailyQuestion.current_streak }}</text>
            <text class="daily-question-stat__label">连续打卡</text>
          </view>
          <view class="daily-question-stat">
            <text class="daily-question-stat__value">{{ dailyQuestion.best_streak }}</text>
            <text class="daily-question-stat__label">最佳记录</text>
          </view>
          <view class="daily-question-stat">
            <text class="daily-question-stat__value">{{ dailyQuestion.recent_answered_days }}</text>
            <text class="daily-question-stat__label">近7天作答</text>
          </view>
        </view>
        <view v-if="!dailyQuestion.answered" class="daily-question-options">
          <button
            v-for="item in dailyQuestionOptionCards"
            :key="`${dailyQuestion?.question_id}-${item.index}`"
            class="daily-question-option"
            :disabled="dailyQuestionSubmitting"
            @tap="answerDailyQuestion(item.index)"
          >
            <view class="daily-question-option__badge">
              <text class="daily-question-option__index">{{ item.label }}</text>
            </view>
            <view class="daily-question-option__copy">
              <text class="daily-question-option__emoji">{{ item.emoji }}</text>
              <text class="daily-question-option__label">{{ item.option }}</text>
            </view>
            <text class="daily-question-option__arrow">›</text>
          </button>
          <view v-if="retroQuestionCards.length" class="daily-question-retro">
            <text class="daily-question-retro__title">最近 3 天可补签</text>
            <view class="daily-question-retro__chips">
              <button
                v-for="item in retroQuestionCards"
                :key="item.date"
                class="daily-question-retro__chip"
                :disabled="dailyQuestionSubmitting"
                @tap="answerDailyQuestion(0, item.date)"
              >
                {{ item.emoji }} 补签 {{ formatRetroDate(item.date) }}
              </button>
            </view>
          </view>
        </view>
        <view v-else class="daily-question-result">
          <view class="daily-question-result__head">
            <text class="daily-question-result__tag">今日选择</text>
            <text class="daily-question-result__choice">
              {{ dailyQuestion.options[dailyQuestion.selected_index || 0] }}
            </text>
          </view>
          <text class="daily-question-result__body">
            {{ dailyQuestion.insight || "今天的答案已经留下，明天再来看看新的问题。" }}
          </text>
          <view
            v-if="dailyQuestion.unlocked_badges && dailyQuestion.unlocked_badges.length"
            class="daily-question-badges"
          >
            <text class="daily-question-badges__title">连续奖励已点亮</text>
            <view class="daily-question-badges__list">
              <text
                v-for="badge in dailyQuestion.unlocked_badges"
                :key="badge.badge_key"
                class="daily-question-badges__item"
              >
                {{ badge.emoji }} {{ badge.name }}
              </text>
            </view>
          </view>
        </view>
      </view>

      <view class="panel panel--fragment" v-if="overview.fragment_progress.length">
        <view class="fragment-panel__hero">
          <view class="fragment-panel__copy">
            <text class="panel__eyebrow">SOUL FRAGMENTS</text>
            <text class="panel__title">灵魂碎片地图</text>
            <text class="panel__body">
              5 个类别会形成一张横向灵魂地图。每列都会显示收集进度，集齐后可以展开更深一层的洞察。
            </text>
          </view>
          <view class="fragment-panel__badge">
            <text class="fragment-panel__badge-value">{{ fragmentCompletionRate }}%</text>
            <text class="fragment-panel__badge-label">已点亮</text>
          </view>
        </view>
        <view class="fragment-panel__meta">
          <text class="fragment-panel__chip">已完成 {{ fragmentCompletedCount }} / {{ overview.fragment_progress.length }} 组</text>
          <text class="fragment-panel__chip">收集 {{ overview.soul_fragments.length }} 片碎片</text>
          <text class="fragment-panel__chip">待解锁 {{ pendingUnlockCount }} 片</text>
        </view>
        <scroll-view scroll-x class="fragment-map">
          <view class="fragment-map__grid">
            <view
              v-for="category in fragmentColumns"
              :key="category.category_code"
              class="fragment-column"
              :class="{ 'fragment-column--completed': category.completed }"
            >
              <view class="fragment-column__aura" />
              <view
                class="fragment-column__head"
                @tap="
                  category.completed &&
                    category.complete_insight &&
                    openFragmentInsight(
                      `${category.category_name} 已完成`,
                      category.emoji,
                      category.complete_insight,
                    )
                "
              >
                <view class="fragment-column__topline">
                  <text class="fragment-column__emoji">{{ category.emoji }}</text>
                  <text class="fragment-column__state">
                    {{ category.completed ? "已完成" : "收集中" }}
                  </text>
                </view>
                <text class="fragment-column__name">{{ category.category_name }}</text>
                <text class="fragment-column__meta">
                  {{ category.unlocked_count }}/{{ category.total_count }}
                </text>
                <view class="fragment-column__track">
                  <view
                    class="fragment-column__progress"
                    :style="{
                      width: `${Math.min(100, (category.unlocked_count / Math.max(1, category.total_count)) * 100)}%`,
                    }"
                  />
                </view>
              </view>
              <view class="fragment-column__list">
                <view
                  v-for="item in category.items"
                  :key="item.fragment_key"
                  class="fragment-column__item"
                  :class="{ 'fragment-column__item--locked': !item.collected }"
                  @tap="
                    item.collected &&
                      openFragmentInsight(item.name, item.emoji || '🧩', item.insight || '这片碎片已经被点亮。')
                  "
                >
                  <text class="fragment-column__item-emoji">{{ item.collected ? item.emoji || '🧩' : '🔒' }}</text>
                  <text class="fragment-column__item-name">{{ item.name }}</text>
                </view>
              </view>
            </view>
          </view>
        </scroll-view>
      </view>

      <view class="panel panel--capsule" v-if="capsules.length">
        <view class="panel__head">
          <view>
            <text class="panel__eyebrow">TIME CAPSULES</text>
            <text class="panel__title">时光胶囊</text>
            <text class="panel__body">
              这里会保存你写给未来的信。锁定中的胶囊会显示剩余天数，已解锁的内容会在首页优先弹出揭示。
            </text>
          </view>
          <view class="capsule-panel__counter">
            <text class="capsule-panel__counter-value">{{ capsuleUnlockedCount }}/{{ capsules.length }}</text>
            <text class="capsule-panel__counter-label">已揭封</text>
          </view>
        </view>
        <view class="capsule-panel__summary">
          <text class="capsule-panel__summary-chip">💌 已开启 {{ capsuleUnlockedCount }} 封</text>
          <text class="capsule-panel__summary-chip">🔒 待开启 {{ capsules.length - capsuleUnlockedCount }} 封</text>
        </view>
        <view class="capsule-list">
          <view
            v-for="item in capsules"
            :key="item.id"
            class="capsule-card"
            :class="{ 'capsule-card--open': item.is_unlocked }"
          >
            <text class="capsule-card__stamp">{{ item.is_unlocked ? "💌" : "🔒" }}</text>
            <text class="capsule-card__dear">亲爱的 {{ overview.nickname || "你" }}，</text>
            <text class="capsule-card__title">{{ item.persona_title || "时光胶囊" }}</text>
            <text class="capsule-card__meta">
              {{
                item.is_unlocked
                  ? `已在 ${formatDayLabel(item.unlock_date)} 打开`
                  : `锁定中 · 还剩 ${item.days_remaining} 天`
              }}
            </text>
            <text class="capsule-card__body">
              {{ item.is_unlocked ? item.message : "等时间到达后，首页会自动帮你揭开这封信。" }}
            </text>
            <text class="capsule-card__sign">
              来自 {{ item.persona_icon || "✨" }} {{ item.is_unlocked ? "过去的你" : "未来的你" }}
            </text>
          </view>
        </view>
      </view>

      <view class="panel" v-if="overview.soul_fragments.length">
        <text class="panel__title">已收集的灵魂碎片</text>
        <text class="panel__body">
          每一片都代表一次更靠近自己的探索，后续这里会继续扩展成更完整的成长资产页。
        </text>
        <view class="fragment-grid">
          <view
            v-for="item in overview.soul_fragments"
            :key="item.fragment_key"
            class="fragment-card"
          >
            <text class="fragment-card__emoji">{{ item.emoji || "✨" }}</text>
            <text class="fragment-card__name">{{ item.name }}</text>
            <text class="fragment-card__category">{{ item.category }}</text>
            <text class="fragment-card__body">
              {{ item.insight || "这片碎片已经被点亮，说明你又看见了自己的一个切面。" }}
            </text>
          </view>
        </view>
      </view>

      <view class="panel panel--account">
        <view class="panel__head">
          <view>
            <text class="panel__eyebrow">ACCOUNT LAYER</text>
            <text class="panel__title">账号与登录</text>
            <text class="panel__body">把这份灵魂档案稳稳保存下来，换设备也不会丢。</text>
          </view>
          <view class="account-panel__badge">
            {{ sessionUser?.is_guest ? "访客模式" : "已保护" }}
          </view>
        </view>
        <view class="account-status">
          <view v-for="item in accountStatusCards" :key="item.key" class="account-status__card">
            <text class="account-status__emoji">{{ item.emoji }}</text>
            <text class="account-status__title">{{ item.title }}</text>
            <text class="account-status__body">{{ item.body }}</text>
          </view>
        </view>
        <view
          v-if="isWechatMiniProgram && sessionUser && !sessionUser.has_openid"
          class="account-form"
        >
          <text class="panel__body">
            当前还是访客身份。你可以先继续使用，也可以立即升级为微信身份并保留已有测试记录。
          </text>
          <button
            class="panel__button panel__button--wechat"
            :disabled="linkingWechat"
            @tap="linkWechatIdentity"
          >
            {{ linkingWechat ? "升级中..." : "升级为微信身份" }}
          </button>
        </view>
        <view v-if="!sessionUser?.has_phone" class="account-form">
          <text class="panel__body">
            绑定手机号后，你的访客记录会升级到正式账号，换设备也能找回历史测试和报告。
          </text>
          <input
            v-model="phone"
            class="field-input"
            type="number"
            maxlength="11"
            placeholder="输入手机号"
          />
          <view class="field-row">
            <input
              v-model="code"
              class="field-input field-input--grow"
              type="number"
              maxlength="6"
              placeholder="输入验证码"
            />
            <button class="field-button" :disabled="sendingCode" @tap="sendCode">
              {{ sendingCode ? "发送中" : "发送验证码" }}
            </button>
          </view>
          <text v-if="debugCode" class="panel__body panel__body--accent">
            当前演示验证码：{{ debugCode }}
          </text>
          <button
            class="panel__button"
            :disabled="!canSubmitPhoneBind || bindingPhone"
            @tap="submitPhoneBind"
          >
            {{ bindingPhone ? "绑定中..." : "绑定手机号" }}
          </button>
        </view>
        <view v-if="profileSettings" class="sound-setting sound-setting--panel">
          <view>
            <text class="sound-setting__label">声音反馈</text>
            <text class="sound-setting__hint">答题、切页和解锁成就时播放轻量反馈</text>
          </view>
          <switch
            :checked="profileSettings.sound_enabled"
            :disabled="savingSound"
            color="#9B7ED8"
            @change="onProfileSoundSwitchChange"
          />
        </view>
      </view>

      <view class="panel panel--settings">
        <view class="panel__head">
          <view>
            <text class="panel__eyebrow">SETTINGS</text>
            <text class="panel__title">系统与偏好</text>
            <text class="panel__body">通知、声音、隐私和关于页面都会从这里继续展开。</text>
          </view>
        </view>
        <view class="settings-menu">
          <view
            v-for="item in settingMenuItems"
            :key="item.key"
            class="settings-item"
            @tap="openSettingItem(item.key)"
          >
            <view class="settings-item__icon-wrap">
              <text class="settings-item__icon">{{ item.icon }}</text>
            </view>
            <view class="settings-item__content">
              <text class="settings-item__label">{{ item.label }}</text>
              <text class="settings-item__desc">{{ item.description }}</text>
            </view>
            <text class="settings-item__arrow">›</text>
          </view>
        </view>
      </view>

      <view
        class="panel archive-panel"
        v-if="overview.dominant_dimensions.length || overview.persona_distribution.length"
      >
        <view class="panel__head">
          <view>
            <text class="panel__eyebrow">ARCHIVE SNAPSHOT</text>
            <text class="panel__title">灵魂档案摘要</text>
            <text class="panel__body">把已经出现得最稳定的维度和人格，压缩成一张易读的总览。</text>
          </view>
          <text class="archive-panel__meta">{{ overview.distinct_test_count }} 类测试</text>
        </view>
        <view v-if="overview.dominant_dimensions.length" class="archive-panel__section">
          <text class="archive-panel__section-title">稳定维度</text>
          <view class="chips">
            <view
              v-for="item in overview.dominant_dimensions"
              :key="item.dim_code"
              class="chip"
            >
              <text class="chip__name">{{ item.dim_code }}</text>
              <text class="chip__score">{{ item.total_score.toFixed(2) }}</text>
            </view>
          </view>
        </view>
        <view v-if="overview.persona_distribution.length" class="archive-panel__section">
          <text class="archive-panel__section-title">人格分布</text>
          <view class="rows">
            <view
              v-for="item in overview.persona_distribution.slice(0, 5)"
              :key="`${item.persona_key || 'unknown'}-${item.count}`"
              class="row"
            >
              <text class="row__name">{{ item.persona_name || "未命名人格" }}</text>
              <text class="row__value">{{ item.count }} 次</text>
            </view>
          </view>
        </view>
      </view>

    </view>
    </view>
  </view>
  <CelebrationOverlay
    :visible="celebrationVisible"
    :title="celebrationTitle"
    :message="celebrationMessage"
    :badges="celebrationBadges"
    @close="closeCelebration"
  />
  <BottomSheet v-model="badgeSheetVisible" max-height="50vh">
    <view v-if="selectedBadge" class="badge-sheet">
      <text class="fragment-reveal__emoji">{{ selectedBadge.emoji }}</text>
      <text class="sheet__title">{{ selectedBadge.name }}</text>
      <text class="sheet__subtitle">
        {{ badgeTierLabel(selectedBadge.tier) }}阶徽章 · 累计 {{ selectedBadge.unlock_count }} 次
      </text>
      <text class="fragment-reveal__body">
        解锁于 {{ formatTime(selectedBadge.unlocked_at) }}。继续保持你的探索节奏，还会点亮更高阶形态。
      </text>
    </view>
  </BottomSheet>
  <view v-if="calendarSelectedDay" class="sheet" @tap="closeCalendarDay">
    <view class="sheet__mask" />
    <view class="sheet__panel" @tap.stop>
      <text class="sheet__title">{{ formatDayLabel(calendarSelectedDay.date) }}</text>
      <text class="sheet__subtitle">
        {{ calendarSelectedDay.mood_emoji || "🙂" }} {{ calendarSelectedDay.activity_count }} 次活动
      </text>
      <view class="sheet__events">
        <view
          v-for="(event, index) in calendarSelectedDay.events"
          :key="`${calendarSelectedDay.date}-${event.source}-${index}`"
          class="sheet__event"
        >
          <text class="sheet__event-emoji">{{ event.emoji || "•" }}</text>
          <text class="sheet__event-label">{{ event.label }}</text>
        </view>
      </view>
      <text class="sheet__block-title">记录这一天的心情</text>
      <view class="sheet__moods">
        <button
          v-for="item in [
            { emoji: '😶', value: 1 },
            { emoji: '🙂', value: 2 },
            { emoji: '😊', value: 3 },
            { emoji: '😄', value: 4 },
            { emoji: '🤩', value: 5 },
          ]"
          :key="item.value"
          class="sheet__mood"
          :disabled="moodSaving"
          @tap="updateCalendarMood(item.value)"
        >
          {{ item.emoji }}
        </button>
      </view>
    </view>
  </view>
  <view v-if="fragmentInsight" class="sheet" @tap="closeFragmentInsight">
    <view class="sheet__mask sheet__mask--dreamy" />
    <view class="sheet__panel sheet__panel--dreamy" @tap.stop>
      <text class="fragment-reveal__emoji">{{ fragmentInsight.emoji }}</text>
      <text class="sheet__title">{{ fragmentInsight.title }}</text>
      <text class="fragment-reveal__body">{{ fragmentInsight.body }}</text>
    </view>
  </view>
  <TabBuddy />
</template>

<style lang="scss" scoped>
/* ── Page shell ── */
.page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  padding: 28rpx 28rpx 40rpx;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.94), rgba(255, 246, 239, 0.78) 46%, #fffaf7 100%);
}

.page__content {
  position: relative;
  z-index: 1;
}

.page__glow,
.page__mesh {
  position: absolute;
  pointer-events: none;
}

.page__glow {
  width: 460rpx;
  height: 460rpx;
  border-radius: 50%;
  filter: blur(34px);
  opacity: 0.42;
}

.page__glow--violet {
  top: -120rpx;
  right: -120rpx;
  background: rgba(155, 126, 216, 0.24);
}

.page__glow--pink {
  left: -140rpx;
  top: 420rpx;
  background: rgba(232, 114, 154, 0.16);
}

.page__mesh {
  inset: 0;
  background-image:
    linear-gradient(rgba(155, 126, 216, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(232, 114, 154, 0.03) 1px, transparent 1px);
  background-size: 44rpx 44rpx;
  opacity: 0.42;
}

.badge-sheet {
  padding: 8rpx 6rpx 12rpx;
  text-align: center;
}

.profile {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

/* ── Hero header (first-pass base, overridden later) ── */
.hero {
  padding: 36rpx 30rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #7C5DBF, #E8729A);
  box-shadow: $xc-shadow;
  color: #fff;
}

.hero__avatar {
  display: inline-flex;
  width: 160rpx;
  height: 160rpx;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.18);
  border: 6rpx solid rgba(255, 255, 255, 0.4);
  font-size: 64rpx;
  box-shadow: 0 4rpx 24rpx rgba(0, 0, 0, 0.12);
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.95);
  }
}

.hero__eyebrow {
  display: block;
  margin-top: 20rpx;
  font-size: 22rpx;
  letter-spacing: 2rpx;
  color: rgba(255, 255, 255, 0.85);
  text-transform: uppercase;
}

.hero__title {
  display: block;
  margin-top: 12rpx;
  font-size: 40rpx;
  font-weight: 700;
  color: #fff;
}

.hero__meta,
.hero__submeta {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.8);
}

/* ── Stats row ── */
.stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.quick-actions__button {
  border-radius: 22rpx;
  @include btn-primary;
  font-size: 24rpx;
}

.quick-actions__button--ghost {
  background: rgba(255, 246, 237, 0.96);
  color: $xc-accent;
  box-shadow: none;
}

/* ── Panels ── */
.panel {
  padding: 28rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(155, 126, 216, 0.12);
  box-shadow: 0 20rpx 52rpx rgba(155, 126, 216, 0.12);
  transition: transform $xc-fast $xc-ease, box-shadow $xc-fast $xc-ease;

  // #ifdef H5
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  // #endif

  &:active {
    transform: scale(0.995);
  }
}

.panel__title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  @include text-gradient;
}

.panel__body {
  display: block;
  margin-top: 14rpx;
  font-size: 26rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.panel__body--accent {
  color: $xc-accent;
}

.panel__button {
  margin-top: 24rpx;
  border-radius: 999rpx;
  @include btn-primary;
}

.panel__button--wechat {
  background: linear-gradient(135deg, #2f8b61, #206848);
}

.account-form {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 18rpx;
}

.field-row {
  display: flex;
  gap: 14rpx;
  align-items: center;
}

.field-input {
  width: 100%;
  min-height: 88rpx;
  padding: 0 24rpx;
  border-radius: 18rpx;
  background: rgba(255, 250, 244, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.12);
  font-size: 28rpx;
  transition: border-color $xc-fast $xc-ease, box-shadow $xc-fast $xc-ease;

  &:focus {
    border-color: $xc-purple-l;
    box-shadow: 0 0 0 4rpx rgba(155, 126, 216, 0.1);
  }
}

.field-input--grow {
  flex: 1;
}

.field-button {
  min-width: 220rpx;
  border-radius: 18rpx;
  background: rgba(155, 126, 216, 0.12);
  color: $xc-accent;
  font-size: 24rpx;
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.96);
    background: rgba(155, 126, 216, 0.2);
  }
}

.sound-setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: rgba(255, 248, 238, 0.96);
}

.sound-setting__label {
  font-size: 24rpx;
  color: $xc-ink;
}

.badge-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.calendar-panel__header {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
}

.calendar-toggle {
  display: flex;
  gap: 10rpx;
  align-items: flex-start;
}

.calendar-toggle__button {
  min-width: 72rpx;
  height: 64rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.1);
  color: $xc-accent;
  font-size: 24rpx;
}

.calendar-toggle__button--active {
  background: linear-gradient(135deg, #9B7ED8, #7C5DBF);
  color: #FBF7F4;
}

.calendar-stats {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.calendar-stats__card {
  padding: 18rpx 12rpx;
  border-radius: 18rpx;
  background: rgba(255, 247, 238, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  text-align: center;
}

.calendar-stats__value {
  display: block;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-accent;
}

.calendar-stats__label {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: $xc-muted;
}

.calendar-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 18rpx;
}

.calendar-toolbar__arrow {
  width: 72rpx;
  height: 72rpx;
  padding: 0;
  border-radius: 50%;
  background: rgba(255, 244, 233, 0.96);
  color: $xc-accent;
  font-size: 34rpx;
}

.calendar-toolbar__title {
  font-size: 28rpx;
  font-weight: 600;
}

.calendar-loading {
  margin-top: 18rpx;
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  margin-top: 18rpx;
  gap: 10rpx;
  text-align: center;
  font-size: 22rpx;
  color: $xc-muted;
}

.calendar-month__grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10rpx;
  margin-top: 12rpx;
}

.calendar-month__cell {
  aspect-ratio: 1;
  border-radius: 12rpx;
  padding: 10rpx;
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform $xc-fast $xc-spring, background $xc-fast $xc-ease;

  &:active {
    transform: scale(0.93);
  }
}

.calendar-month__cell--empty {
  border-style: dashed;
  background: rgba(255, 252, 248, 0.58);
}

.calendar-month__date {
  font-size: 22rpx;
  color: $xc-ink;
}

.calendar-month__emoji {
  text-align: right;
  font-size: 22rpx;
}

.calendar-year {
  margin-top: 18rpx;
}

.calendar-year__grid {
  display: grid;
  grid-auto-flow: column;
  grid-template-rows: repeat(7, 22rpx);
  gap: 6rpx;
  padding-bottom: 4rpx;
}

.calendar-year__week {
  display: contents;
}

.calendar-year__cell {
  width: 22rpx;
  height: 22rpx;
  border-radius: 6rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(1.4);
  }
}

.calendar-year__cell--empty {
  background: transparent;
}

.calendar-year__emoji {
  font-size: 14rpx;
  line-height: 1;
}

.badge-card {
  padding: 18rpx;
  border-radius: 18rpx;
  background: rgba(255, 248, 238, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.12);
  transition: transform $xc-fast $xc-spring, box-shadow $xc-fast $xc-ease;

  &:active {
    transform: scale(0.95);
  }
}

.badge-card__emoji {
  display: block;
  font-size: 34rpx;
}

.badge-card__name {
  display: block;
  margin-top: 8rpx;
  font-size: 24rpx;
  font-weight: 600;
}

.badge-card__time {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: $xc-muted;
}

.badge-card__tier {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: $xc-accent;
}

.fragment-grid {
  margin-top: 18rpx;
  display: grid;
  gap: 14rpx;
}

.fragment-map {
  margin-top: 18rpx;
}

.fragment-map__grid {
  display: grid;
  grid-auto-flow: column;
  grid-auto-columns: 220rpx;
  gap: 14rpx;
}

.fragment-column {
  padding: 18rpx;
  border-radius: 22rpx;
  background: rgba(255, 248, 238, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.fragment-column__head {
  display: flex;
  flex-direction: column;
}

.fragment-column__emoji {
  font-size: 34rpx;
}

.fragment-column__name {
  margin-top: 8rpx;
  font-size: 26rpx;
  font-weight: 600;
}

.fragment-column__meta {
  margin-top: 4rpx;
  font-size: 22rpx;
  color: $xc-muted;
}

.fragment-column__track {
  margin-top: 12rpx;
  height: 10rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.1);
  overflow: hidden;
}

.fragment-column__progress {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #C9B5F0, #9B7ED8);
}

.fragment-column__list {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  margin-top: 16rpx;
}

.fragment-column__item {
  min-height: 92rpx;
  padding: 14rpx 12rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.72);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.96);
  }
}

.fragment-column__item--locked {
  opacity: 0.5;
  filter: grayscale(0.4);
}

.fragment-column__item-emoji {
  display: block;
  font-size: 28rpx;
}

.fragment-column__item-name {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  line-height: 1.5;
  color: $xc-ink;
}

.capsule-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 18rpx;
}

.capsule-card {
  display: grid;
  grid-template-columns: 72rpx 1fr;
  gap: 16rpx;
  padding: 20rpx;
  border-radius: 20rpx;
  background: rgba(255, 247, 238, 0.96);
  border: 2rpx solid rgba($xc-gold, 0.18);
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.98);
  }
}

.capsule-card--open {
  background: linear-gradient(145deg, rgba(253, 244, 222, 0.98), rgba(255, 233, 193, 0.94));
  border-color: rgba($xc-gold, 0.35);
  box-shadow: 0 4rpx 20rpx rgba($xc-gold, 0.15);
}

.capsule-card__icon {
  font-size: 40rpx;
  text-align: center;
}

.capsule-card__title {
  display: block;
  font-size: 26rpx;
  font-weight: 600;
}

.capsule-card__meta {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $xc-gold;
}

.capsule-card__body {
  display: block;
  margin-top: 10rpx;
  font-size: 23rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.fragment-card {
  padding: 20rpx;
  border-radius: 20rpx;
  background:
    linear-gradient(145deg, rgba(255, 247, 235, 0.96), rgba(255, 235, 214, 0.92));
  border: 2rpx solid rgba(155, 126, 216, 0.12);
}

.fragment-card__emoji {
  display: block;
  font-size: 34rpx;
}

.fragment-card__name {
  display: block;
  margin-top: 10rpx;
  font-size: 28rpx;
  font-weight: 600;
}

.fragment-card__category {
  display: block;
  margin-top: 8rpx;
  font-size: 22rpx;
  color: $xc-accent;
}

.fragment-card__body {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.heatmap {
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.heatmap--mini {
  margin-top: 24rpx;
}

.heatmap__week {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 10rpx;
}

.heatmap-cell {
  min-height: 92rpx;
  padding: 12rpx 10rpx;
  border-radius: 16rpx;
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  background: rgba(255, 250, 244, 0.72);
}

.heatmap-cell--level-0 {
  background: rgba(247, 241, 255, 0.45);
}

.heatmap-cell--level-1 {
  background: $xc-purple-p;
}

.heatmap-cell--level-2 {
  background: rgba($xc-purple-l, 0.65);
}

.heatmap-cell--level-3 {
  background: rgba($xc-purple, 0.72);
}

.heatmap-cell--level-4 {
  background: rgba($xc-purple-d, 0.88);
}

.heatmap-cell__day,
.heatmap-cell__count {
  display: block;
  text-align: center;
}

.heatmap-cell__day {
  font-size: 18rpx;
  color: rgba(58, 46, 66, 0.72);
}

.heatmap-cell__count {
  margin-top: 10rpx;
  font-size: 26rpx;
  font-weight: 700;
  color: $xc-ink;
}

.daily-question-options {
  display: grid;
  gap: 12rpx;
  margin-top: 18rpx;
}

.daily-question-retro {
  margin-top: 16rpx;
}

.daily-question-retro__title {
  display: block;
  font-size: 22rpx;
  color: $xc-muted;
}

.daily-question-retro__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 12rpx;
}

.daily-question-retro__chip {
  padding: 0 20rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.12);
  color: $xc-accent;
  font-size: 22rpx;
}

.daily-question-stats {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.daily-question-stat {
  padding: 18rpx 14rpx;
  border-radius: 18rpx;
  background: rgba(255, 248, 238, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  text-align: center;
}

.daily-question-stat__value {
  display: block;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-accent;
}

.daily-question-stat__label {
  display: block;
  margin-top: 8rpx;
  font-size: 20rpx;
  color: $xc-muted;
}

.daily-question-option {
  border-radius: 20rpx;
  background: rgba(255, 245, 235, 0.96);
  color: $xc-ink;
  border: 2rpx solid rgba(155, 126, 216, 0.12);
  transition: transform $xc-fast $xc-spring, background $xc-fast $xc-ease;

  &:active {
    transform: scale(0.97);
    background: rgba($xc-purple-p, 0.8);
  }
}

.daily-question-result {
  margin-top: 18rpx;
  padding: 22rpx;
  border-radius: 20rpx;
  background: rgba(255, 248, 238, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.1);
}

.daily-question-result__label {
  display: block;
  font-size: 24rpx;
  color: $xc-accent;
}

.daily-question-result__body {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.daily-question-badges {
  margin-top: 16rpx;
  padding-top: 14rpx;
  border-top: 2rpx dashed rgba(155, 126, 216, 0.12);
}

.daily-question-badges__title {
  display: block;
  font-size: 22rpx;
  color: $xc-accent;
}

.daily-question-badges__list {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 10rpx;
}

.daily-question-badges__item {
  display: inline-flex;
  align-items: center;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 242, 228, 0.96);
  font-size: 22rpx;
  color: $xc-ink;
}

.stat-card {
  padding: 24rpx;
  border-radius: 22rpx;
  @include glass;
  box-shadow: $xc-sh-md;
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.97);
  }
}

.stat-card__label {
  display: block;
  font-size: 22rpx;
  color: $xc-muted;
}

.stat-card__value {
  display: block;
  margin-top: 10rpx;
  font-size: 34rpx;
  font-weight: 700;
  @include text-gradient;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  margin-top: 18rpx;
}

.chip {
  min-width: 148rpx;
  padding: 18rpx 20rpx;
  border-radius: 20rpx;
  background: rgba(237, 229, 249, 0.72);
}

.chip__name {
  display: block;
  font-size: 24rpx;
  color: $xc-muted;
}

.chip__score {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  font-weight: 700;
  color: $xc-accent;
}

.rows {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-top: 18rpx;
}

.rows--soft {
  margin-top: 16rpx;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: rgba(255, 250, 244, 0.92);
}

.row--soft {
  background: rgba(255, 247, 238, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.row__name,
.row__value {
  font-size: 24rpx;
}

.row__value {
  color: $xc-accent;
}

.history {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 18rpx;
}

.history-card {
  padding: 24rpx;
  border-radius: 22rpx;
  background: rgba(255, 250, 244, 0.96);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.98);
  }
}

.history-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.history-card__title {
  font-size: 28rpx;
  font-weight: 600;
}

.history-card__time,
.history-card__footer {
  font-size: 22rpx;
  color: $xc-muted;
}

.history-card__persona {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: $xc-accent;
}

.history-card__summary {
  display: block;
  margin-top: 12rpx;
  font-size: 24rpx;
  line-height: 1.7;
  color: $xc-muted;
}

.history-card__footer {
  display: block;
  margin-top: 14rpx;
}

.sheet {
  position: fixed;
  inset: 0;
  z-index: $xc-z-modal;
  display: flex;
  align-items: flex-end;
}

.sheet__mask {
  position: absolute;
  inset: 0;
  background: rgba(33, 20, 16, 0.46);
  // #ifdef H5
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  // #endif
}

.sheet__mask--dreamy {
  background: rgba(28, 18, 34, 0.58);
  // #ifdef H5
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  // #endif
}

.sheet__panel {
  position: relative;
  width: 100%;
  padding: 34rpx 30rpx calc(42rpx + #{$xc-safe-b});
  border-radius: 56rpx 56rpx 0 0;
  background: #fffaf5;
  box-shadow: $xc-sh-lg;
  animation: sheet-rise 0.32s $xc-ease;
}

.sheet__panel--dreamy {
  margin: auto 36rpx;
  border-radius: 30rpx;
  background: linear-gradient(180deg, rgba(255, 249, 241, 0.98), rgba(255, 235, 222, 0.94));
}

.sheet__title {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
}

.sheet__subtitle {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  color: $xc-muted;
}

.sheet__events {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-top: 20rpx;
}

.sheet__event {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx 18rpx;
  border-radius: 16rpx;
  background: rgba(255, 247, 238, 0.96);
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.97);
  }
}

.sheet__event-emoji {
  font-size: 28rpx;
}

.sheet__event-label {
  font-size: 24rpx;
  color: $xc-ink;
}

.sheet__block-title {
  display: block;
  margin-top: 22rpx;
  font-size: 24rpx;
  color: $xc-accent;
}

.sheet__moods {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12rpx;
  margin-top: 14rpx;
}

.sheet__mood {
  min-width: 0;
  padding: 18rpx 0;
  border-radius: 18rpx;
  background: rgba(255, 242, 228, 0.96);
  font-size: 30rpx;
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(1.2);
  }
}

.fragment-reveal__emoji {
  display: block;
  font-size: 92rpx;
  text-align: center;
  animation: fragment-float 0.42s ease-out;
}

.fragment-reveal__body {
  display: block;
  margin-top: 18rpx;
  font-size: 26rpx;
  line-height: 1.8;
  text-align: center;
  color: $xc-muted;
  animation: fragment-fade 0.5s ease-out;
}

@keyframes sheet-rise {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

@keyframes fragment-float {
  from {
    opacity: 0;
    transform: scale(0.7) translateY(24rpx);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes fragment-fade {
  from {
    opacity: 0;
    transform: translateY(20rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Polished overrides ── */
.profile {
  gap: 24rpx;
}

.hero {
  background: linear-gradient(135deg, #7C5DBF, #E8729A);
  border-radius: $xc-r-xl;
  padding: 30rpx;
  color: #fff;
  box-shadow: $xc-sh-lg;
  position: relative;
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    top: -30%;
    right: -20%;
    width: 260rpx;
    height: 260rpx;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.08);
  }
}

.hero__top {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.hero__avatar-wrap {
  width: 160rpx;
  height: 160rpx;
  border-radius: 50%;
  padding: 4rpx;
  background: rgba(255, 255, 255, 0.35);
  box-shadow: 0 0 24rpx rgba(155, 126, 216, 0.55);
}

.hero__avatar {
  width: 100%;
  height: 100%;
  margin: 0;
  border-radius: 50%;
  border: 6rpx solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.2);
}

.hero__info {
  flex: 1;
  min-width: 0;
}

.hero__title {
  margin: 0;
  font-family: $xc-font-serif;
  font-size: 46rpx;
}

.hero__signature {
  display: block;
  margin-top: 8rpx;
  font-size: 23rpx;
  color: rgba(255, 255, 255, 0.9);
}

.hero__actions {
  margin-top: 14rpx;
  display: flex;
  gap: 10rpx;
}

.hero__tag-btn,
.hero__icon-btn {
  margin: 0;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border: 2rpx solid rgba(255, 255, 255, 0.3);
  font-size: 22rpx;
  transition: transform $xc-fast $xc-spring, background $xc-fast $xc-ease;

  &:active {
    transform: scale(0.94);
    background: rgba(255, 255, 255, 0.35);
  }
}

.hero__tag-btn {
  padding: 0 22rpx;
}

.hero__icon-btn {
  width: 66rpx;
  min-width: 66rpx;
}

.stats {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.stat-card--highlight {
  @include glass-strong;
  text-align: center;
  padding: 20rpx 14rpx;
}

.stat-card--highlight .stat-card__value {
  @include text-gradient;
  font-size: 38rpx;
}

.stat-card--highlight .stat-card__label {
  margin-top: 8rpx;
  color: $xc-muted;
}

.panel {
  @include card-base;
}

.soul-panel {
  @include glass-strong;
}

.panel__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14rpx;
}

.panel__head-link {
  font-size: 22rpx;
  color: $xc-purple;
}

.soul-panel__main {
  margin-top: 14rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.soul-panel__meta {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.soul-panel__level {
  font-size: 24rpx;
  color: $xc-ink;
  font-weight: 600;
}

.soul-panel__track,
.memory-panel__track {
  height: 12rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.12);
  overflow: hidden;
}

.soul-panel__fill,
.memory-panel__fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #9b7ed8, #e8729a);
}

.soul-panel__progress,
.memory-panel__meta {
  font-size: 22rpx;
  color: $xc-muted;
}

.soul-panel__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.soul-tag {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.12);
  color: $xc-purple-d;
  font-size: 20rpx;
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.94);
  }
}

.memory-panel__head {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.history--timeline {
  position: relative;
  padding-left: 16rpx;
}

.history--timeline::before {
  content: "";
  position: absolute;
  left: 4rpx;
  top: 0;
  bottom: 0;
  width: 2rpx;
  background: rgba(155, 126, 216, 0.2);
}

.history--timeline .history-card {
  position: relative;
  margin-left: 12rpx;
}

.history-card__dot {
  position: absolute;
  left: -22rpx;
  top: 24rpx;
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #9b7ed8;
  box-shadow: 0 0 10rpx rgba(155, 126, 216, 0.45);
}

.match-card {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 18rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 2rpx solid rgba(232, 114, 154, 0.16);
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.97);
  }
}

.match-card__avatars {
  display: flex;
  margin-right: 4rpx;
}

.match-card__avatar {
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  background: rgba(232, 114, 154, 0.2);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-left: -6rpx;
}

.match-card__body {
  flex: 1;
}

.match-card__title {
  display: block;
  font-size: 24rpx;
  font-weight: 600;
}

.match-card__meta {
  display: block;
  margin-top: 6rpx;
  font-size: 21rpx;
  color: $xc-muted;
}

.match-card__tag {
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(232, 114, 154, 0.18);
  color: $xc-pink;
  font-size: 20rpx;
}

.badge-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.badge-card {
  position: relative;
  overflow: visible;
}

.badge-card--unlocked {
  border-color: $xc-purple-l;
  box-shadow: $xc-sh-sm;
}

.badge-card--locked {
  opacity: 0.5;
  filter: grayscale(0.4);
}

.badge-card--new::after {
  content: "NEW";
  position: absolute;
  top: -10rpx;
  right: -10rpx;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  background: $xc-pink;
  color: #fff;
  font-size: 18rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
  box-shadow: 0 2rpx 8rpx rgba($xc-pink, 0.35);
}

.badge-card--duo {
  border-color: rgba(232, 114, 154, 0.24);
  background: linear-gradient(145deg, rgba(253, 230, 239, 0.8), rgba($xc-pink-p, 0.6));
}

.badge-card--t1 {
  border-color: rgba(205, 127, 50, 0.35);
  box-shadow: 0 0 12rpx rgba(205, 127, 50, 0.24);
}

.badge-card--t2 {
  border-color: rgba(192, 192, 192, 0.52);
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.92), rgba(240, 240, 240, 0.86));
}

.badge-card--t3 {
  border-color: rgba($xc-gold, 0.55);
  box-shadow: 0 0 20rpx rgba($xc-gold, 0.32);
  animation: glowGold 2s ease-in-out infinite;
}

.badge-card--t4 {
  border-color: rgba($xc-purple-l, 0.75);
  background:
    linear-gradient(120deg, rgba(185, 242, 255, 0.34), rgba($xc-purple-p, 0.4), rgba(255, 255, 255, 0.9));
  box-shadow: 0 0 28rpx rgba($xc-purple, 0.35);
  animation: glowPurple 2s ease-in-out infinite;
}

.fragment-map__grid {
  grid-auto-columns: 240rpx;
}

.fragment-column__head {
  cursor: pointer;
}

.fragment-column__head:active {
  transform: scale(0.98);
}

.fragment-column__progress {
  background: linear-gradient(90deg, #9b7ed8, #e8729a);
}

.fragment-column__meta {
  color: $xc-purple-d;
}

.fragment-column__item--locked {
  filter: grayscale(0.4);
  opacity: 0.5;
}

.calendar-panel__header {
  align-items: flex-start;
}

.calendar-panel__all {
  margin-top: 6rpx;
  font-size: 22rpx;
  color: $xc-purple;
}

.calendar-month__cell--today,
.calendar-year__cell--today {
  border: 3rpx solid $xc-purple;
  font-weight: 700;
  box-shadow: 0 0 0 3rpx rgba($xc-purple, 0.15);
}

.heatmap-cell--level-0 {
  background: rgba(247, 241, 255, 0.6);
}

.heatmap-cell--level-1 {
  background: rgba(221, 203, 247, 0.72);
}

.heatmap-cell--level-2 {
  background: rgba(195, 165, 239, 0.8);
}

.heatmap-cell--level-3 {
  background: rgba(155, 126, 216, 0.86);
}

.heatmap-cell--level-4 {
  background: rgba(124, 93, 191, 0.9);
}

.settings-menu {
  margin-top: 14rpx;
  display: flex;
  flex-direction: column;
}

.settings-item {
  display: grid;
  grid-template-columns: 44rpx 1fr 20rpx;
  align-items: center;
  gap: 12rpx;
  min-height: 82rpx;
  border-bottom: 1px solid rgba(155, 126, 216, 0.08);
  transition: background $xc-fast $xc-ease;

  &:active {
    background: rgba($xc-purple-p, 0.4);
  }
}

.settings-item:last-child {
  border-bottom: 0;
}

.settings-item__icon {
  font-size: 24rpx;
}

.settings-item__label {
  font-size: 24rpx;
}

.settings-item__arrow {
  font-size: 24rpx;
  color: $xc-hint;
  text-align: right;
}

.panel__eyebrow {
  display: block;
  margin-bottom: 10rpx;
  font-size: 19rpx;
  font-weight: 700;
  letter-spacing: 2.8rpx;
  color: rgba(123, 110, 133, 0.7);
}

.calendar-hero,
.fragment-panel__hero {
  display: flex;
  gap: 18rpx;
  align-items: flex-start;
}

.calendar-hero__copy,
.fragment-panel__copy {
  flex: 1;
  min-width: 0;
}

.calendar-hero__badge,
.fragment-panel__badge {
  width: 188rpx;
  padding: 18rpx 16rpx;
  border-radius: 24rpx;
  background:
    linear-gradient(150deg, rgba(255, 255, 255, 0.92), rgba(245, 235, 255, 0.88));
  border: 2rpx solid rgba(155, 126, 216, 0.12);
  text-align: center;
  box-shadow: 0 16rpx 36rpx rgba(155, 126, 216, 0.12);
}

.calendar-hero__emoji {
  display: block;
  font-size: 40rpx;
}

.calendar-hero__label,
.fragment-panel__badge-value {
  display: block;
  margin-top: 8rpx;
  font-size: 30rpx;
  font-weight: 700;
  color: $xc-accent;
}

.calendar-hero__desc,
.fragment-panel__badge-label {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  line-height: 1.5;
  color: $xc-muted;
}

.calendar-callouts,
.fragment-panel__meta,
.capsule-panel__summary {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 18rpx;
}

.calendar-callout,
.fragment-panel__chip,
.capsule-panel__summary-chip {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 243, 233, 0.95);
  border: 1px solid rgba(155, 126, 216, 0.08);
  font-size: 22rpx;
  color: $xc-ink;
}

.calendar-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  margin-top: 18rpx;
}

.calendar-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx 16rpx;
  margin-top: 20rpx;
}

.calendar-legend__item {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  font-size: 21rpx;
  color: $xc-muted;
}

.calendar-legend__dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 8rpx;
  border: 1px solid rgba(155, 126, 216, 0.08);
}

.daily-question__hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.daily-question__orb {
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background:
    radial-gradient(circle at 35% 30%, rgba(255, 255, 255, 0.92), rgba(255, 236, 245, 0.75)),
    linear-gradient(135deg, rgba(155, 126, 216, 0.26), rgba(232, 114, 154, 0.18));
  box-shadow: 0 16rpx 32rpx rgba(155, 126, 216, 0.14);
  font-size: 34rpx;
}

.daily-question__question-card {
  margin-top: 18rpx;
  padding: 22rpx 22rpx 24rpx;
  border-radius: 24rpx;
  background:
    linear-gradient(145deg, rgba(255, 248, 242, 0.96), rgba(248, 240, 255, 0.92));
  border: 2rpx solid rgba(155, 126, 216, 0.1);
}

.daily-question__date {
  display: block;
  font-size: 21rpx;
  color: $xc-muted;
}

.daily-question__question {
  display: block;
  margin-top: 10rpx;
  font-size: 31rpx;
  line-height: 1.55;
  color: $xc-ink;
  font-weight: 600;
}

.daily-question-option {
  min-height: 112rpx;
  padding: 0 18rpx;
  display: grid;
  grid-template-columns: 64rpx 1fr 24rpx;
  align-items: center;
  gap: 14rpx;
}

.daily-question-option__badge {
  width: 64rpx;
  height: 64rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.86);
}

.daily-question-option__index {
  font-size: 24rpx;
  font-weight: 700;
  color: $xc-purple;
}

.daily-question-option__copy {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.daily-question-option__emoji {
  font-size: 26rpx;
}

.daily-question-option__label {
  flex: 1;
  font-size: 24rpx;
  line-height: 1.55;
  color: $xc-ink;
  text-align: left;
}

.daily-question-option__arrow {
  font-size: 24rpx;
  color: $xc-hint;
}

.daily-question-result__head {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  align-items: center;
}

.daily-question-result__tag {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(155, 126, 216, 0.12);
  font-size: 21rpx;
  color: $xc-purple;
}

.daily-question-result__choice {
  font-size: 25rpx;
  font-weight: 700;
  color: $xc-ink;
}

.fragment-column {
  position: relative;
  overflow: hidden;
}

.fragment-column--completed {
  border-color: rgba(232, 114, 154, 0.22);
  box-shadow: 0 18rpx 34rpx rgba(232, 114, 154, 0.12);
}

.fragment-column__aura {
  position: absolute;
  top: -42rpx;
  right: -30rpx;
  width: 132rpx;
  height: 132rpx;
  border-radius: 50%;
  background: rgba(232, 114, 154, 0.12);
  filter: blur(6px);
  pointer-events: none;
}

.fragment-column__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.fragment-column__state {
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.72);
  font-size: 20rpx;
  color: $xc-purple;
}

.settings-item__icon-wrap {
  width: 44rpx;
  height: 44rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(245, 238, 255, 0.88);
}

.settings-item__content {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.settings-item__label {
  color: $xc-ink;
}

.settings-item__desc {
  font-size: 20rpx;
  line-height: 1.5;
  color: $xc-muted;
}

.capsule-panel__counter {
  min-width: 156rpx;
  padding: 18rpx 16rpx;
  border-radius: 24rpx;
  background:
    linear-gradient(145deg, rgba(253, 244, 222, 0.96), rgba(255, 234, 205, 0.92));
  border: 2rpx solid rgba($xc-gold, 0.24);
  text-align: center;
  box-shadow: 0 18rpx 36rpx rgba($xc-gold, 0.14);
}

.capsule-panel__counter-value {
  display: block;
  font-size: 32rpx;
  font-weight: 700;
  color: #8b6220;
}

.capsule-panel__counter-label {
  display: block;
  margin-top: 8rpx;
  font-size: 21rpx;
  color: rgba(143, 97, 39, 0.82);
}

.capsule-card {
  position: relative;
  display: block;
  padding: 30rpx 24rpx 24rpx;
  border-radius: 28rpx;
  background: linear-gradient(160deg, #faf6ee, #f5ede2);
  border: 2rpx solid rgba($xc-gold, 0.18);
  box-shadow: 0 18rpx 36rpx rgba(132, 96, 41, 0.08);
  overflow: hidden;

  &::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
      repeating-linear-gradient(
        0deg,
        transparent,
        transparent 34rpx,
        rgba(155, 126, 216, 0.04) 34rpx,
        rgba(155, 126, 216, 0.04) 35rpx
      );
    pointer-events: none;
  }
}

.capsule-card__stamp {
  position: absolute;
  top: 16rpx;
  right: 18rpx;
  font-size: 42rpx;
  opacity: 0.62;
  transform: rotate(12deg);
}

.capsule-card__dear {
  display: block;
  font-family: $xc-font-serif;
  font-size: 25rpx;
  font-weight: 700;
  color: $xc-ink;
}

.capsule-card__title {
  margin-top: 16rpx;
  font-family: $xc-font-serif;
  font-size: 30rpx;
  font-weight: 700;
}

.capsule-card__meta {
  margin-top: 12rpx;
  font-size: 22rpx;
  color: rgba(143, 97, 39, 0.84);
}

.capsule-card__body {
  margin-top: 16rpx;
  font-family: $xc-font-serif;
  font-size: 24rpx;
  line-height: 1.95;
  color: rgba(58, 46, 66, 0.82);
}

.capsule-card__sign {
  display: block;
  margin-top: 18rpx;
  text-align: right;
  font-family: $xc-font-serif;
  font-size: 22rpx;
  color: $xc-muted;
  font-style: italic;
}

.account-panel__badge,
.archive-panel__meta {
  align-self: flex-start;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: rgba(245, 238, 255, 0.9);
  font-size: 21rpx;
  color: $xc-purple;
}

.account-status {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
  margin-top: 18rpx;
}

.account-status__card {
  min-height: 172rpx;
  padding: 18rpx 16rpx;
  border-radius: 22rpx;
  background: rgba(255, 247, 239, 0.92);
  border: 2rpx solid rgba(155, 126, 216, 0.08);
}

.account-status__emoji {
  display: block;
  font-size: 32rpx;
}

.account-status__title {
  display: block;
  margin-top: 10rpx;
  font-size: 24rpx;
  font-weight: 700;
  color: $xc-ink;
}

.account-status__body {
  display: block;
  margin-top: 10rpx;
  font-size: 21rpx;
  line-height: 1.6;
  color: $xc-muted;
}

.sound-setting--panel {
  margin-top: 18rpx;
}

.sound-setting__hint {
  display: block;
  margin-top: 6rpx;
  font-size: 20rpx;
  color: $xc-muted;
}

.archive-panel__section {
  margin-top: 18rpx;
}

.archive-panel__section-title {
  display: block;
  font-size: 22rpx;
  font-weight: 700;
  color: $xc-muted;
}

/* ── Cascading entrance animations ── */
.profile > :nth-child(1) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0s; }
.profile > :nth-child(2) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.06s; }
.profile > :nth-child(3) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.12s; }
.profile > :nth-child(4) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.18s; }
.profile > :nth-child(5) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.24s; }
.profile > :nth-child(6) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.30s; }
.profile > :nth-child(7) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.36s; }
.profile > :nth-child(8) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.42s; }
.profile > :nth-child(9) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.48s; }
.profile > :nth-child(10) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.54s; }
.profile > :nth-child(n+11) { animation: cascadeIn 0.4s $xc-ease both; animation-delay: 0.6s; }

@keyframes cascadeIn {
  from {
    opacity: 0;
    transform: translateY(28rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Gold glow for tier-3 badges ── */
@keyframes glowGold {
  0%, 100% {
    box-shadow: 0 0 16rpx rgba($xc-gold, 0.28);
  }
  50% {
    box-shadow: 0 0 28rpx rgba($xc-gold, 0.48);
  }
}

/* ── Purple glow for tier-4 (diamond) badges ── */
@keyframes glowPurple {
  0%, 100% {
    box-shadow: 0 0 20rpx rgba($xc-purple, 0.3);
  }
  50% {
    box-shadow: 0 0 36rpx rgba($xc-purple, 0.55);
  }
}

/* ── Celebration overlay popIn ── */
@keyframes popIn {
  0% {
    opacity: 0;
    transform: scale(0.6);
  }
  60% {
    transform: scale(1.06);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* ── Calendar stats value -- gradient text ── */
.calendar-stats__value {
  @include text-gradient;
}

/* ── Daily question stat value -- gradient text ── */
.daily-question-stat__value {
  @include text-gradient;
}

/* ── Calendar toggle active state ── */
.calendar-toggle__button {
  transition: transform $xc-fast $xc-spring, background $xc-fast $xc-ease;

  &:active {
    transform: scale(0.94);
  }
}

/* ── Calendar toolbar arrow active ── */
.calendar-toolbar__arrow {
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.9);
  }
}

/* ── Retro chip active ── */
.daily-question-retro__chip {
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.94);
  }
}

/* ── Chip active ── */
.chip {
  transition: transform $xc-fast $xc-spring;

  &:active {
    transform: scale(0.95);
  }
}
</style>
