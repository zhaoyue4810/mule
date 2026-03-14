<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { getYamlStatus, listAdminBadges } from "@/services/admin";

const loading = ref(false);
const badges = ref<any[]>([]);
const yamlStatus = ref<any | null>(null);
const dialogVisible = ref(false);
const activeBadge = ref<any | null>(null);

const totalCount = computed(() => badges.value.length);
const soloCount = computed(() => badges.value.filter((item) => item.type !== "duo").length);
const duoCount = computed(() => badges.value.filter((item) => item.type === "duo").length);

async function loadData() {
  loading.value = true;
  try {
    const [badgePayload, statusPayload] = await Promise.all([
      listAdminBadges(),
      getYamlStatus(),
    ]);
    badges.value = badgePayload;
    yamlStatus.value = statusPayload;
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "加载徽章配置失败");
  } finally {
    loading.value = false;
  }
}

function openRuleDialog(row: any) {
  activeBadge.value = row;
  dialogVisible.value = true;
}

const activeYamlDefinition = computed(() => {
  if (!activeBadge.value) {
    return null;
  }
  return yamlStatus.value?.badge_definitions?.[activeBadge.value.badge_key] || null;
});

onMounted(loadData);
</script>

<template>
  <div class="stack">
    <el-row :gutter="12">
      <el-col :span="8"><el-statistic title="徽章总数" :value="totalCount" /></el-col>
      <el-col :span="8"><el-statistic title="个人徽章" :value="soloCount" /></el-col>
      <el-col :span="8"><el-statistic title="双人徽章" :value="duoCount" /></el-col>
    </el-row>

    <el-card>
      <template #header>徽章定义（只读）</template>
      <el-table :data="badges" v-loading="loading">
        <el-table-column prop="emoji" label="Emoji" width="90" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column label="类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.type === 'duo' ? 'danger' : 'success'">
              {{ row.type === "duo" ? "双人" : "个人" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="解锁规则描述" min-width="280">
          <template #default="{ row }">
            <span>{{ JSON.stringify(row.unlock_rule) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="yaml_source" label="YAML 来源" width="140" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openRuleDialog(row)">查看规则</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>

  <el-dialog v-model="dialogVisible" :title="activeBadge?.name || '徽章规则'" width="760px">
    <template v-if="activeYamlDefinition">
      <pre class="yaml-preview">{{ JSON.stringify(activeYamlDefinition, null, 2) }}</pre>
    </template>
    <el-empty v-else description="未找到对应 YAML 定义" />
  </el-dialog>
</template>

<style scoped>
.stack { display:flex; flex-direction:column; gap:16px; }
.yaml-preview {
  max-height: 460px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
  background: #f7f7f8;
  border-radius: 8px;
  padding: 12px;
}
</style>
