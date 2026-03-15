<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter } from "vue-router";

import {
  createAdminTestVersion,
  getAdminTestDetail,
  getAdminTestVersionContent,
  listAdminTests,
  listAdminTestVersions,
  listInteractionTypes,
  publishAdminTestVersion,
  updateAdminTestVersionContent,
  type AdminCreateVersionRequest,
  type AdminDimensionPayload,
  type AdminOptionPayload,
  type AdminPersonaPayload,
  type AdminQuestionPayload,
  type AdminTestDetail,
  type AdminTestSummary,
  type AdminTestVersionContent,
  type AdminTestVersionContentUpdateRequest,
  type AdminTestVersionSummary,
  type InteractionTypeSummary,
} from "@/services/admin";

interface EditableOption
  extends Omit<AdminOptionPayload, "score_rules" | "ext_config"> {
  score_rules_text: string;
  ext_config_text: string;
}

interface EditableQuestion
  extends Omit<AdminQuestionPayload, "config" | "dim_weights" | "options"> {
  config_text: string;
  dim_weights_text: string;
  options: EditableOption[];
}

interface EditablePersona
  extends Omit<AdminPersonaPayload, "keywords" | "dim_pattern"> {
  keywords_text: string;
  dim_pattern_text: string;
}

interface EditableVersionContent
  extends Omit<AdminTestVersionContent, "dimensions" | "questions" | "personas"> {
  dimensions: AdminDimensionPayload[];
  questions: EditableQuestion[];
  personas: EditablePersona[];
}

const router = useRouter();

const loading = ref(false);
const versionsLoading = ref(false);
const contentLoading = ref(false);
const saving = ref(false);
const publishing = ref(false);
const creatingDraft = ref(false);
const tests = ref<AdminTestSummary[]>([]);
const interactionTypes = ref<InteractionTypeSummary[]>([]);
const activeTestDetail = ref<AdminTestDetail | null>(null);
const versions = ref<AdminTestVersionSummary[]>([]);
const activeVersionId = ref<number | null>(null);
const editForm = ref<EditableVersionContent | null>(null);
const editorTab = ref("basic");
const questionPanels = ref<string[]>([]);

const editableStatuses = new Set(["DRAFT", "IMPORTED_DRAFT"]);

const activeVersion = computed(() =>
  versions.value.find((item) => item.id === activeVersionId.value) || null,
);
const canEdit = computed(() =>
  Boolean(activeVersion.value && editableStatuses.has(activeVersion.value.status)),
);
const questionCount = computed(() => editForm.value?.questions.length || 0);
const dimensionCount = computed(() => editForm.value?.dimensions.length || 0);
const personaCount = computed(() => editForm.value?.personas.length || 0);
const categoryOptions = [
  "性格测试",
  "情感探索",
  "关系匹配",
  "职业测评",
  "趣味测试",
];

function formatDate(value?: string | null) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN", { hour12: false });
}

function statusTagType(status: string) {
  const map: Record<string, "success" | "warning" | "info" | "danger"> = {
    PUBLISHED: "success",
    DRAFT: "warning",
    IMPORTED_DRAFT: "warning",
    ARCHIVED: "info",
    FAILED: "danger",
  };
  return map[status] || "info";
}

function stringifyJson(value: unknown) {
  if (
    value == null ||
    (typeof value === "object" &&
      !Array.isArray(value) &&
      Object.keys(value as Record<string, unknown>).length === 0)
  ) {
    return "";
  }
  return JSON.stringify(value, null, 2);
}

function toEditableContent(content: AdminTestVersionContent): EditableVersionContent {
  return {
    ...content,
    dimensions: content.dimensions.map((item) => ({ ...item })),
    questions: content.questions.map((item) => ({
      ...item,
      config_text: stringifyJson(item.config),
      dim_weights_text: stringifyJson(item.dim_weights),
      options: item.options.map((option) => ({
        ...option,
        score_rules_text: stringifyJson(option.score_rules),
        ext_config_text: stringifyJson(option.ext_config),
      })),
    })),
    personas: content.personas.map((item) => ({
      ...item,
      keywords_text: item.keywords.join(", "),
      dim_pattern_text: stringifyJson(item.dim_pattern),
    })),
  };
}

function parseJsonObject(
  raw: string,
  label: string,
  fallback: Record<string, unknown> | null,
) {
  const trimmed = raw.trim();
  if (!trimmed) {
    return fallback;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(trimmed);
  } catch (error) {
    throw new Error(`${label} 不是合法 JSON`);
  }

  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error(`${label} 必须是 JSON 对象`);
  }

  return parsed as Record<string, unknown>;
}

function toSavePayload(form: EditableVersionContent): AdminTestVersionContentUpdateRequest {
  return {
    title: form.title.trim(),
    category: form.category.trim(),
    is_match_enabled: form.is_match_enabled,
    participant_count: form.participant_count,
    sort_order: form.sort_order,
    description: form.description?.trim() || null,
    duration_hint: form.duration_hint?.trim() || null,
    cover_gradient: form.cover_gradient?.trim() || null,
    report_template_code: form.report_template_code?.trim() || null,
    dimensions: form.dimensions.map((item) => ({
      dim_code: item.dim_code.trim(),
      dim_name: item.dim_name.trim(),
      max_score: item.max_score,
      sort_order: item.sort_order,
    })),
    questions: form.questions.map((item, index) => ({
      question_code: item.question_code?.trim() || null,
      seq: item.seq,
      question_text: item.question_text.trim(),
      interaction_type: item.interaction_type.trim(),
      emoji: item.emoji?.trim() || null,
      config: parseJsonObject(
        item.config_text,
        `第 ${index + 1} 题配置`,
        null,
      ),
      dim_weights:
        parseJsonObject(
          item.dim_weights_text,
          `第 ${index + 1} 题维度权重`,
          {},
        ) || {},
      options: item.options.map((option, optionIndex) => ({
        option_code: option.option_code?.trim() || null,
        seq: option.seq,
        label: option.label.trim(),
        emoji: option.emoji?.trim() || null,
        value: option.value,
        score_rules: parseJsonObject(
          option.score_rules_text,
          `第 ${index + 1} 题选项 ${optionIndex + 1} 评分规则`,
          null,
        ),
        ext_config: parseJsonObject(
          option.ext_config_text,
          `第 ${index + 1} 题选项 ${optionIndex + 1} 扩展配置`,
          null,
        ),
      })),
    })),
    personas: form.personas.map((item, index) => ({
      persona_key: item.persona_key.trim(),
      persona_name: item.persona_name.trim(),
      emoji: item.emoji?.trim() || null,
      rarity_percent: item.rarity_percent ?? null,
      description: item.description?.trim() || null,
      soul_signature: item.soul_signature?.trim() || null,
      keywords: item.keywords_text
        .split(/[\n,，]/)
        .map((keyword) => keyword.trim())
        .filter(Boolean),
      dim_pattern:
        parseJsonObject(
          item.dim_pattern_text,
          `人格 ${index + 1} 维度模式`,
          {},
        ) || {},
      capsule_prompt: item.capsule_prompt?.trim() || null,
    })),
  };
}

async function loadReferenceData() {
  loading.value = true;
  try {
    const [testsPayload, interactionPayload] = await Promise.all([
      listAdminTests(),
      listInteractionTypes(),
    ]);
    tests.value = testsPayload;
    interactionTypes.value = interactionPayload;

    if (!tests.value.length) {
      activeTestDetail.value = null;
      versions.value = [];
      activeVersionId.value = null;
      editForm.value = null;
      return;
    }

    const stillExists = activeTestDetail.value
      ? tests.value.some((item) => item.test_code === activeTestDetail.value?.test_code)
      : false;
    if (!stillExists) {
      await openTest(tests.value[0].test_code);
    } else if (activeTestDetail.value) {
      await openTest(activeTestDetail.value.test_code, activeVersionId.value);
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "加载测试配置失败");
  } finally {
    loading.value = false;
  }
}

async function openTest(testCode: string, preferredVersionId?: number | null) {
  versionsLoading.value = true;
  editForm.value = null;
  try {
    const [detailPayload, versionPayload] = await Promise.all([
      getAdminTestDetail(testCode),
      listAdminTestVersions(testCode),
    ]);
    activeTestDetail.value = detailPayload;
    versions.value = versionPayload;

    const targetVersionId =
      preferredVersionId ||
      detailPayload.published_version_id ||
      versionPayload[0]?.id ||
      null;
    if (targetVersionId) {
      await selectVersion(targetVersionId);
    } else {
      activeVersionId.value = null;
      editForm.value = null;
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "加载测试详情失败");
  } finally {
    versionsLoading.value = false;
  }
}

async function selectVersion(versionId: number) {
  if (!activeTestDetail.value) {
    return;
  }
  contentLoading.value = true;
  activeVersionId.value = versionId;
  try {
    const content = await getAdminTestVersionContent(
      activeTestDetail.value.test_code,
      versionId,
    );
    editForm.value = toEditableContent(content);
    questionPanels.value = content.questions.map((item, index) =>
      `${item.seq}-${index}`,
    );
    editorTab.value = "basic";
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "加载版本内容失败");
  } finally {
    contentLoading.value = false;
  }
}

async function saveVersionContent() {
  if (!activeTestDetail.value || !activeVersionId.value || !editForm.value) {
    return;
  }

  saving.value = true;
  try {
    const payload = toSavePayload(editForm.value);
    await updateAdminTestVersionContent(
      activeTestDetail.value.test_code,
      activeVersionId.value,
      payload,
    );
    ElMessage.success("版本内容已保存");
    await loadReferenceData();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "保存失败");
  } finally {
    saving.value = false;
  }
}

async function publishVersion(versionId?: number) {
  if (!activeTestDetail.value) {
    return;
  }
  const targetId = versionId || activeVersionId.value;
  if (!targetId) {
    return;
  }

  try {
    await ElMessageBox.confirm(
      "发布后 H5 将直接读取这个版本的详情、题目与报告配置，是否继续？",
      "发布测试版本",
      {
        type: "warning",
        confirmButtonText: "确认发布",
        cancelButtonText: "取消",
      },
    );
  } catch {
    return;
  }

  publishing.value = true;
  try {
    await publishAdminTestVersion(activeTestDetail.value.test_code, {
      version_id: targetId,
    });
    ElMessage.success("版本已发布，H5 将读取最新发布态");
    await loadReferenceData();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "发布失败");
  } finally {
    publishing.value = false;
  }
}

async function createDraftFromVersion(sourceVersionId?: number | null) {
  if (!activeTestDetail.value) {
    return;
  }

  const payload: AdminCreateVersionRequest = {
    source_version_id: sourceVersionId ?? activeVersionId.value ?? null,
    clone_content: true,
  };

  creatingDraft.value = true;
  try {
    const created = await createAdminTestVersion(
      activeTestDetail.value.test_code,
      payload,
    );
    ElMessage.success(`已创建 v${created.version} 草稿`);
    await loadReferenceData();
    await openTest(activeTestDetail.value.test_code, created.id);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "创建草稿失败");
  } finally {
    creatingDraft.value = false;
  }
}

function addDimension() {
  if (!editForm.value) {
    return;
  }
  editForm.value.dimensions.push({
    dim_code: "",
    dim_name: "",
    max_score: 100,
    sort_order: editForm.value.dimensions.length + 1,
  });
}

function addQuestion() {
  if (!editForm.value) {
    return;
  }
  editForm.value.questions.push({
    question_code: null,
    seq:
      Math.max(
        0,
        ...editForm.value.questions.map((item) => item.seq || 0),
      ) + 1,
    question_text: "",
    interaction_type: interactionTypes.value[0]?.code || "bubble",
    emoji: null,
    config_text: "",
    dim_weights_text: "{}",
    options: [],
  });
  questionPanels.value = editForm.value.questions.map((item, index) => `${item.seq}-${index}`);
}

function addOption(question: EditableQuestion) {
  question.options.push({
    option_code: null,
    seq: question.options.length + 1,
    label: "",
    emoji: null,
    value: 0,
    score_rules_text: "",
    ext_config_text: "",
  });
}

function addPersona() {
  if (!editForm.value) {
    return;
  }
  editForm.value.personas.push({
    persona_key: "",
    persona_name: "",
    emoji: null,
    rarity_percent: null,
    description: null,
    soul_signature: null,
    keywords_text: "",
    dim_pattern_text: "{}",
    capsule_prompt: null,
  });
}

function handleTestRowClick(row: AdminTestSummary) {
  void openTest(row.test_code);
}

onMounted(loadReferenceData);
</script>

<template>
  <div class="tests-view">
    <el-row :gutter="16">
      <el-col :span="10">
        <el-card class="panel-card" v-loading="loading">
          <template #header>
            <div class="panel-header">
              <span>测试列表</span>
              <el-button @click="loadReferenceData">刷新</el-button>
            </div>
          </template>

          <template v-if="tests.length">
            <el-table :data="tests" @row-click="handleTestRowClick">
              <el-table-column prop="test_code" label="编码" min-width="120" />
              <el-table-column prop="title" label="标题" min-width="180" />
              <el-table-column prop="category" label="分类" min-width="120" />
              <el-table-column prop="version_count" label="版本数" width="90" />
              <el-table-column label="操作" width="110" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click.stop="openTest(row.test_code)">
                    配置
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </template>
          <el-empty v-else description="当前没有测试配置">
            <el-button type="primary" @click="router.push('/imports')">
              去导入测试目录
            </el-button>
          </el-empty>
        </el-card>
      </el-col>

      <el-col :span="14">
        <el-card class="panel-card" v-loading="versionsLoading">
          <template #header>
            <div class="panel-header">
              <span>测试概览</span>
              <div class="panel-actions" v-if="activeTestDetail">
                <el-button
                  type="primary"
                  :loading="creatingDraft"
                  @click="createDraftFromVersion()"
                >
                  复制为新草稿
                </el-button>
                <el-button @click="openTest(activeTestDetail.test_code, activeVersionId)">
                  重新加载
                </el-button>
              </div>
            </div>
          </template>

          <template v-if="activeTestDetail">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="测试编码">
                {{ activeTestDetail.test_code }}
              </el-descriptions-item>
              <el-descriptions-item label="分类">
                {{ activeTestDetail.category }}
              </el-descriptions-item>
              <el-descriptions-item label="已发布版本">
                {{ activeTestDetail.published_version || "-" }}
              </el-descriptions-item>
              <el-descriptions-item label="体验人数">
                {{ activeTestDetail.participant_count }}
              </el-descriptions-item>
              <el-descriptions-item label="匹配支持">
                <el-tag :type="activeTestDetail.is_match_enabled ? 'success' : 'info'">
                  {{ activeTestDetail.is_match_enabled ? "开启" : "关闭" }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="来源">
                {{ activeTestDetail.yaml_source || "admin" }}
              </el-descriptions-item>
            </el-descriptions>
            <el-alert
              class="pipeline-alert"
              type="success"
              :closable="false"
              title="发布态会直接进入 H5 的测试列表、详情、问卷、提交与报告链路。"
            />
          </template>
          <el-empty v-else description="请选择一个测试" />
        </el-card>
      </el-col>
    </el-row>

    <div v-if="activeTestDetail" class="workspace">
      <el-card class="workspace__versions" v-loading="versionsLoading || creatingDraft">
        <template #header>
          <div class="panel-header">
            <span>版本列表</span>
            <el-tag type="info">{{ versions.length }} 个版本</el-tag>
          </div>
        </template>

        <template v-if="versions.length">
          <div class="version-list">
            <div
              v-for="version in versions"
              :key="version.id"
              class="version-card"
              :class="{ 'version-card--active': version.id === activeVersionId }"
              @click="selectVersion(version.id)"
            >
              <div class="version-card__top">
                <div>
                  <div class="version-card__title">v{{ version.version }}</div>
                  <div class="version-card__desc">
                    {{ version.description || "未填写版本说明" }}
                  </div>
                </div>
                <el-tag :type="statusTagType(version.status)">
                  {{ version.status }}
                </el-tag>
              </div>
              <div class="version-card__meta">
                <span>时长：{{ version.duration_hint || "-" }}</span>
                <span>创建：{{ formatDate(version.created_at) }}</span>
                <span>发布：{{ formatDate(version.published_at) }}</span>
              </div>
              <div class="version-card__actions">
                <el-button
                  size="small"
                  @click.stop="createDraftFromVersion(version.id)"
                >
                  复制草稿
                </el-button>
                <el-button
                  size="small"
                  type="primary"
                  :disabled="version.status === 'PUBLISHED'"
                  @click.stop="publishVersion(version.id)"
                >
                  {{ version.status === "ARCHIVED" ? "回滚发布" : "发布" }}
                </el-button>
              </div>
            </div>
          </div>
        </template>
        <el-empty v-else description="当前测试还没有版本，可先创建一个草稿版本" />
      </el-card>

      <el-card class="workspace__editor" v-loading="contentLoading || saving || publishing">
        <template #header>
          <div class="panel-header">
            <div>
              <div class="editor-title">
                <span v-if="editForm">版本 v{{ editForm.version }} 配置</span>
                <span v-else>版本内容</span>
              </div>
              <div class="editor-subtitle" v-if="activeVersion">
                {{ dimensionCount }} 维度 · {{ questionCount }} 题 · {{ personaCount }} 人格
              </div>
            </div>
            <div class="panel-actions" v-if="editForm">
              <el-button :disabled="!canEdit" :loading="saving" @click="saveVersionContent">
                保存
              </el-button>
              <el-button
                type="primary"
                :disabled="!activeVersionId"
                :loading="publishing"
                @click="publishVersion()"
              >
                发布到 H5
              </el-button>
            </div>
          </div>
        </template>

        <template v-if="editForm">
          <el-alert
            v-if="!canEdit"
            class="readonly-alert"
            type="warning"
            :closable="false"
            title="当前版本为只读状态，请使用“复制为新草稿”后再编辑。"
          />

          <el-tabs v-model="editorTab">
            <el-tab-pane label="基本信息" name="basic">
              <div class="form-grid">
                <el-form-item label="测试标题">
                  <el-input v-model="editForm.title" :disabled="!canEdit" />
                </el-form-item>
                <el-form-item label="分类">
                  <el-select
                    v-model="editForm.category"
                    filterable
                    allow-create
                    default-first-option
                    :disabled="!canEdit"
                  >
                    <el-option
                      v-for="item in categoryOptions"
                      :key="item"
                      :label="item"
                      :value="item"
                    />
                  </el-select>
                </el-form-item>
                <el-form-item label="体验人数">
                  <el-input-number
                    v-model="editForm.participant_count"
                    :min="0"
                    :disabled="!canEdit"
                  />
                </el-form-item>
                <el-form-item label="排序">
                  <el-input-number
                    v-model="editForm.sort_order"
                    :disabled="!canEdit"
                  />
                </el-form-item>
                <el-form-item label="预计时长">
                  <el-input v-model="editForm.duration_hint" :disabled="!canEdit" />
                </el-form-item>
                <el-form-item label="报告模板">
                  <el-input
                    v-model="editForm.report_template_code"
                    :disabled="!canEdit"
                  />
                </el-form-item>
                <el-form-item label="封面渐变">
                  <el-input v-model="editForm.cover_gradient" :disabled="!canEdit" />
                </el-form-item>
                <el-form-item label="支持匹配">
                  <el-switch
                    v-model="editForm.is_match_enabled"
                    :disabled="!canEdit"
                  />
                </el-form-item>
              </div>

              <el-form-item label="版本说明">
                <el-input
                  v-model="editForm.description"
                  type="textarea"
                  :rows="4"
                  :disabled="!canEdit"
                />
              </el-form-item>
            </el-tab-pane>

            <el-tab-pane :label="`维度 (${dimensionCount})`" name="dimensions">
              <div class="section-toolbar">
                <div class="section-note">配置评分维度，H5 报告会基于这些维度汇总。</div>
                <el-button type="primary" plain :disabled="!canEdit" @click="addDimension">
                  新增维度
                </el-button>
              </div>

              <div class="stack-list">
                <div
                  v-for="(dimension, index) in editForm.dimensions"
                  :key="`dimension-${index}`"
                  class="stack-card"
                >
                  <div class="stack-card__header">
                    <strong>维度 {{ index + 1 }}</strong>
                    <el-button
                      link
                      type="danger"
                      :disabled="!canEdit"
                      @click="editForm.dimensions.splice(index, 1)"
                    >
                      删除
                    </el-button>
                  </div>
                  <div class="form-grid">
                    <el-form-item label="编码">
                      <el-input v-model="dimension.dim_code" :disabled="!canEdit" />
                    </el-form-item>
                    <el-form-item label="名称">
                      <el-input v-model="dimension.dim_name" :disabled="!canEdit" />
                    </el-form-item>
                    <el-form-item label="满分">
                      <el-input-number
                        v-model="dimension.max_score"
                        :min="1"
                        :disabled="!canEdit"
                      />
                    </el-form-item>
                    <el-form-item label="排序">
                      <el-input-number
                        v-model="dimension.sort_order"
                        :disabled="!canEdit"
                      />
                    </el-form-item>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <el-tab-pane :label="`试题 (${questionCount})`" name="questions">
              <div class="section-toolbar">
                <div class="section-note">题型必须与 H5 支持的渲染组件一致。</div>
                <el-button type="primary" plain :disabled="!canEdit" @click="addQuestion">
                  新增题目
                </el-button>
              </div>

              <el-collapse v-model="questionPanels">
                <el-collapse-item
                  v-for="(question, questionIndex) in editForm.questions"
                  :key="`question-${questionIndex}`"
                  :name="`${question.seq}-${questionIndex}`"
                >
                  <template #title>
                    <div class="question-title">
                      <span>Q{{ question.seq }}</span>
                      <span>{{ question.question_text || "未命名题目" }}</span>
                    </div>
                  </template>

                  <div class="stack-card">
                    <div class="stack-card__header">
                      <strong>题目配置</strong>
                      <el-button
                        link
                        type="danger"
                        :disabled="!canEdit"
                        @click="editForm.questions.splice(questionIndex, 1)"
                      >
                        删除题目
                      </el-button>
                    </div>

                    <div class="form-grid">
                      <el-form-item label="题号">
                        <el-input-number
                          v-model="question.seq"
                          :min="1"
                          :disabled="!canEdit"
                        />
                      </el-form-item>
                      <el-form-item label="题目编码">
                        <el-input
                          v-model="question.question_code"
                          :disabled="!canEdit"
                        />
                      </el-form-item>
                      <el-form-item label="题型">
                        <el-select
                          v-model="question.interaction_type"
                          filterable
                          allow-create
                          default-first-option
                          :disabled="!canEdit"
                        >
                          <el-option
                            v-for="item in interactionTypes"
                            :key="item.code"
                            :label="`${item.title} (${item.code})`"
                            :value="item.code"
                          />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="题目 emoji">
                        <el-input v-model="question.emoji" :disabled="!canEdit" />
                      </el-form-item>
                    </div>

                    <el-form-item label="题目文案">
                      <el-input
                        v-model="question.question_text"
                        type="textarea"
                        :rows="3"
                        :disabled="!canEdit"
                      />
                    </el-form-item>

                    <div class="form-grid form-grid--wide">
                      <el-form-item label="题型配置 JSON">
                        <el-input
                          v-model="question.config_text"
                          type="textarea"
                          :rows="6"
                          :disabled="!canEdit"
                        />
                      </el-form-item>
                      <el-form-item label="维度权重 JSON">
                        <el-input
                          v-model="question.dim_weights_text"
                          type="textarea"
                          :rows="6"
                          :disabled="!canEdit"
                        />
                      </el-form-item>
                    </div>

                    <div class="section-toolbar section-toolbar--nested">
                      <div class="section-note">
                        当前题型：{{ question.interaction_type || "-" }}
                      </div>
                      <el-button
                        size="small"
                        type="primary"
                        plain
                        :disabled="!canEdit"
                        @click="addOption(question)"
                      >
                        新增选项
                      </el-button>
                    </div>

                    <div class="stack-list stack-list--compact">
                      <div
                        v-for="(option, optionIndex) in question.options"
                        :key="`option-${questionIndex}-${optionIndex}`"
                        class="stack-card stack-card--subtle"
                      >
                        <div class="stack-card__header">
                          <strong>选项 {{ optionIndex + 1 }}</strong>
                          <el-button
                            link
                            type="danger"
                            :disabled="!canEdit"
                            @click="question.options.splice(optionIndex, 1)"
                          >
                            删除
                          </el-button>
                        </div>

                        <div class="form-grid">
                          <el-form-item label="顺序">
                            <el-input-number
                              v-model="option.seq"
                              :min="1"
                              :disabled="!canEdit"
                            />
                          </el-form-item>
                          <el-form-item label="编码">
                            <el-input
                              v-model="option.option_code"
                              :disabled="!canEdit"
                            />
                          </el-form-item>
                          <el-form-item label="得分">
                            <el-input-number
                              v-model="option.value"
                              :step="0.5"
                              :disabled="!canEdit"
                            />
                          </el-form-item>
                          <el-form-item label="emoji">
                            <el-input v-model="option.emoji" :disabled="!canEdit" />
                          </el-form-item>
                        </div>

                        <el-form-item label="选项文案">
                          <el-input
                            v-model="option.label"
                            :disabled="!canEdit"
                          />
                        </el-form-item>

                        <div class="form-grid form-grid--wide">
                          <el-form-item label="评分规则 JSON">
                            <el-input
                              v-model="option.score_rules_text"
                              type="textarea"
                              :rows="5"
                              :disabled="!canEdit"
                            />
                          </el-form-item>
                          <el-form-item label="扩展配置 JSON">
                            <el-input
                              v-model="option.ext_config_text"
                              type="textarea"
                              :rows="5"
                              :disabled="!canEdit"
                            />
                          </el-form-item>
                        </div>
                      </div>
                    </div>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </el-tab-pane>

            <el-tab-pane :label="`人格 (${personaCount})`" name="personas">
              <div class="section-toolbar">
                <div class="section-note">人格会直接影响 H5 报告中的人格描述与标签。</div>
                <el-button type="primary" plain :disabled="!canEdit" @click="addPersona">
                  新增人格
                </el-button>
              </div>

              <div class="stack-list">
                <div
                  v-for="(persona, index) in editForm.personas"
                  :key="`persona-${index}`"
                  class="stack-card"
                >
                  <div class="stack-card__header">
                    <strong>{{ persona.persona_name || `人格 ${index + 1}` }}</strong>
                    <el-button
                      link
                      type="danger"
                      :disabled="!canEdit"
                      @click="editForm.personas.splice(index, 1)"
                    >
                      删除
                    </el-button>
                  </div>

                  <div class="form-grid">
                    <el-form-item label="人格编码">
                      <el-input v-model="persona.persona_key" :disabled="!canEdit" />
                    </el-form-item>
                    <el-form-item label="人格名称">
                      <el-input v-model="persona.persona_name" :disabled="!canEdit" />
                    </el-form-item>
                    <el-form-item label="emoji">
                      <el-input v-model="persona.emoji" :disabled="!canEdit" />
                    </el-form-item>
                    <el-form-item label="稀有度">
                      <el-input-number
                        v-model="persona.rarity_percent"
                        :min="0"
                        :max="100"
                        :disabled="!canEdit"
                      />
                    </el-form-item>
                  </div>

                  <el-form-item label="人格描述">
                    <el-input
                      v-model="persona.description"
                      type="textarea"
                      :rows="4"
                      :disabled="!canEdit"
                    />
                  </el-form-item>

                  <div class="form-grid form-grid--wide">
                    <el-form-item label="灵魂签名">
                      <el-input
                        v-model="persona.soul_signature"
                        :disabled="!canEdit"
                      />
                    </el-form-item>
                    <el-form-item label="关键词">
                      <el-input
                        v-model="persona.keywords_text"
                        placeholder="多个关键词用逗号分隔"
                        :disabled="!canEdit"
                      />
                    </el-form-item>
                    <el-form-item label="维度模式 JSON">
                      <el-input
                        v-model="persona.dim_pattern_text"
                        type="textarea"
                        :rows="6"
                        :disabled="!canEdit"
                      />
                    </el-form-item>
                    <el-form-item label="时光胶囊提示">
                      <el-input
                        v-model="persona.capsule_prompt"
                        type="textarea"
                        :rows="6"
                        :disabled="!canEdit"
                      />
                    </el-form-item>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>

        <el-empty
          v-else
          description="选择左侧版本后即可开始配置"
        />
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.tests-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-card {
  min-height: 260px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.pipeline-alert {
  margin-top: 16px;
}

.workspace {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.workspace__versions {
  position: sticky;
  top: 0;
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.version-card {
  border: 1px solid #ebe6dd;
  border-radius: 14px;
  padding: 14px;
  cursor: pointer;
  background: #fffdfa;
  transition: all 0.2s ease;
}

.version-card:hover {
  border-color: #d8b18a;
  transform: translateY(-1px);
}

.version-card--active {
  border-color: #c67542;
  box-shadow: 0 10px 30px rgba(198, 117, 66, 0.12);
  background: linear-gradient(180deg, #fffaf6 0%, #ffffff 100%);
}

.version-card__top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.version-card__title {
  font-size: 18px;
  font-weight: 700;
  color: #443127;
}

.version-card__desc {
  margin-top: 6px;
  font-size: 13px;
  color: #7f6a5d;
  line-height: 1.5;
}

.version-card__meta {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 12px;
  color: #8d7c70;
}

.version-card__actions {
  margin-top: 14px;
  display: flex;
  gap: 8px;
}

.editor-title {
  font-size: 18px;
  font-weight: 700;
  color: #443127;
}

.editor-subtitle {
  margin-top: 6px;
  color: #8d7c70;
  font-size: 13px;
}

.readonly-alert {
  margin-bottom: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.form-grid--wide {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.section-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.section-toolbar--nested {
  margin-top: 16px;
}

.section-note {
  color: #8d7c70;
  font-size: 13px;
}

.stack-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stack-list--compact {
  gap: 12px;
}

.stack-card {
  border: 1px solid #eee8dd;
  border-radius: 14px;
  padding: 16px;
  background: #fffdfa;
}

.stack-card--subtle {
  background: #ffffff;
}

.stack-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.question-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  color: #443127;
}

:deep(.el-form-item) {
  margin-bottom: 0;
}

@media (max-width: 1280px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .workspace__versions {
    position: static;
  }
}
</style>
