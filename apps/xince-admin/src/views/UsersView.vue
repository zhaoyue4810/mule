<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";

import {
  getAdminUserDetail,
  listAdminUsers,
  updateAdminUserStatus,
} from "@/services/admin";

const loading = ref(false);
const users = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(20);
const keyword = ref("");
const detailVisible = ref(false);
const detailLoading = ref(false);
const detail = ref<any | null>(null);

async function loadUsers() {
  loading.value = true;
  try {
    const payload = await listAdminUsers(page.value, size.value, keyword.value);
    users.value = payload.items || [];
    total.value = payload.total || 0;
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "加载用户列表失败");
  } finally {
    loading.value = false;
  }
}

async function openDetail(row: any) {
  detailVisible.value = true;
  detailLoading.value = true;
  detail.value = null;
  try {
    detail.value = await getAdminUserDetail(row.id);
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "加载用户详情失败");
  } finally {
    detailLoading.value = false;
  }
}

async function toggleStatus(row: any) {
  const nextStatus = row.status === "ENABLED" ? "DISABLED" : "ENABLED";
  try {
    const updated = await updateAdminUserStatus(row.id, nextStatus);
    row.status = updated.status;
    if (detail.value?.id === row.id) {
      detail.value.status = updated.status;
    }
    ElMessage.success("状态已更新");
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : "状态更新失败");
  }
}

onMounted(loadUsers);
</script>

<template>
  <el-card>
    <template #header>
      <div class="header">
        <span>用户管理</span>
        <div class="search">
          <el-input
            v-model="keyword"
            placeholder="按昵称搜索"
            clearable
            style="width: 260px"
            @keyup.enter="loadUsers"
            @clear="loadUsers"
          />
          <el-button type="primary" @click="loadUsers">搜索</el-button>
        </div>
      </div>
    </template>

    <el-table :data="users" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column label="头像" width="90">
        <template #default="{ row }">
          <span style="font-size:22px">{{ row.avatar_value }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="nickname" label="昵称" min-width="140" />
      <el-table-column prop="gender" label="性别" width="90" />
      <el-table-column prop="created_at" label="注册时间" width="180" />
      <el-table-column prop="test_count" label="测试数" width="90" />
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="row.status === 'ENABLED' ? 'success' : 'info'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" @click="openDetail(row)">详情</el-button>
          <el-button link :type="row.status === 'ENABLED' ? 'danger' : 'success'" @click="toggleStatus(row)">
            {{ row.status === "ENABLED" ? "禁用" : "启用" }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="loadUsers"
      />
    </div>
  </el-card>

  <el-drawer v-model="detailVisible" title="用户详情" size="55%">
    <div v-loading="detailLoading">
      <template v-if="detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="用户 ID">{{ detail.id }}</el-descriptions-item>
          <el-descriptions-item label="昵称">{{ detail.nickname }}</el-descriptions-item>
          <el-descriptions-item label="状态">{{ detail.status }}</el-descriptions-item>
          <el-descriptions-item label="注册时间">{{ detail.created_at }}</el-descriptions-item>
          <el-descriptions-item label="测试数">{{ detail.test_count }}</el-descriptions-item>
          <el-descriptions-item label="匹配数">{{ detail.match_count }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>测试记录</el-divider>
        <el-table :data="detail.test_records">
          <el-table-column prop="record_id" label="记录ID" width="90" />
          <el-table-column prop="test_name" label="测试名" />
          <el-table-column prop="total_score" label="分数" width="90" />
          <el-table-column prop="completed_at" label="时间" width="180" />
        </el-table>

        <el-divider>匹配记录</el-divider>
        <el-table :data="detail.match_records">
          <el-table-column prop="session_id" label="会话ID" width="90" />
          <el-table-column prop="test_name" label="测试名" />
          <el-table-column prop="status" label="状态" width="120" />
          <el-table-column prop="compatibility_score" label="匹配分" width="100" />
        </el-table>

        <el-divider>已获徽章</el-divider>
        <el-table :data="detail.badges">
          <el-table-column prop="emoji" label="徽章" width="90" />
          <el-table-column prop="name" label="名称" />
          <el-table-column prop="tier" label="等级" width="90" />
          <el-table-column prop="unlock_count" label="次数" width="90" />
        </el-table>
      </template>
    </div>
  </el-drawer>
</template>

<style scoped>
.header { display:flex; justify-content:space-between; align-items:center; }
.search { display:flex; gap:8px; align-items:center; }
.pager { margin-top: 16px; display:flex; justify-content:flex-end; }
</style>
