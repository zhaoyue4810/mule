<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import { getHealthReady, getYamlStatus, reloadYamlConfig } from "@/services/admin";

const loading = ref(false);
const yamlStatus = ref<any | null>(null);
const health = ref<any | null>(null);

async function loadData() {
  loading.value = true;
  try {
    const [yamlPayload, healthPayload] = await Promise.all([getYamlStatus(), getHealthReady()]);
    yamlStatus.value = yamlPayload;
    health.value = healthPayload;
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "加载系统设置失败");
  } finally {
    loading.value = false;
  }
}

async function reloadYaml() {
  try {
    await reloadYamlConfig();
    ElMessage.success("YAML 配置已重新加载");
    await loadData();
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "重载失败");
  }
}

onMounted(loadData);
</script>

<template>
  <div class="stack" v-loading="loading">
    <el-card>
      <template #header>
        <div class="header">
          <span>YAML 配置状态</span>
          <el-button type="primary" @click="reloadYaml">重新加载 YAML</el-button>
        </div>
      </template>
      <el-table :data="yamlStatus?.files || []">
        <el-table-column prop="file_name" label="文件" min-width="220" />
        <el-table-column prop="status" label="状态" width="120" />
        <el-table-column prop="item_count" label="条目数" width="100" />
        <el-table-column prop="updated_at" label="最后更新时间" min-width="190" />
      </el-table>
    </el-card>

    <el-card>
      <template #header>系统信息</template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="服务状态">{{ health?.status || "-" }}</el-descriptions-item>
        <el-descriptions-item label="环境">{{ health?.environment || "-" }}</el-descriptions-item>
        <el-descriptions-item label="数据库">{{ health?.checks?.database?.status || "-" }}</el-descriptions-item>
        <el-descriptions-item label="YAML">{{ health?.checks?.yaml_config?.status || "-" }}</el-descriptions-item>
        <el-descriptions-item label="JWT">{{ health?.checks?.jwt_secret?.status || "-" }}</el-descriptions-item>
        <el-descriptions-item label="微信">{{ health?.checks?.wechat_mini_program?.status || "-" }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<style scoped>
.stack { display:flex; flex-direction:column; gap:16px; }
.header { display:flex; justify-content:space-between; align-items:center; }
</style>
