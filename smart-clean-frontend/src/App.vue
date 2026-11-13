<template>
  <div class="app-layout">
    <!-- 左侧 -->
    <div class="left-panel">
      <el-card v-if="showUpload" class="box-card">
        <template #header>
          <div class="card-header">
            <h3>📤 上传并新建任务</h3>
            <el-button link type="primary" @click="showUpload = false">收起</el-button>
          </div>
        </template>
        <el-form label-position="top">
          <el-form-item label="任务名称">
            <el-input v-model="taskName" placeholder="例如：10月份销售数据" />
          </el-form-item>
          <el-form-item>
            <div class="upload-wrapper">
              <el-upload drag action="#" :auto-upload="false" :limit="1" :on-change="handleFileChange" :on-exceed="handleExceed">
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
              </el-upload>
            </div>
          </el-form-item>
          <el-button type="primary" style="width: 100%;" @click="submitUpload" :loading="loading">开始上传并新建任务</el-button>
        </el-form>
      </el-card>
      <el-button v-else type="primary" plain style="width: 100%; border-style: dashed;" @click="showUpload = true">
        ➕ 新建清洗任务
      </el-button>

      <el-card class="box-card config-card">
        <template #header>
          <div class="card-header">
            <h3>🛠️ 清洗工具栏</h3>
            <el-tag v-if="currentTask.id" type="primary" effect="dark" size="small">
              ID: {{ currentTask.id }} | {{ currentTask.taskName }}
            </el-tag>
          </div>
        </template>

        <el-empty v-if="!currentTask.id" description="请在右侧列表点击选择要配置的任务" :image-size="100" />

        <div v-else class="config-container">
          <!-- 阶段一 -->
          <div class="stage-title">阶段一：基础清洗（去杂质）</div>
          <el-collapse v-model="activeCollapse">
            <el-collapse-item name="empty">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.dropEmpty" @click.stop>删除全空行</el-checkbox></div></template>
              <div class="collapse-content text-gray">自动识别并删除表格中完全没有数据的空行。</div>
            </el-collapse-item>
            <el-collapse-item name="summary">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.dropSummary" @click.stop>剔除小计/合计行</el-checkbox></div></template>
              <div class="collapse-content text-gray">自动过滤掉含有“小计”、“合计”等字眼的汇总行。</div>
            </el-collapse-item>
            <el-collapse-item name="phone">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.doCleanPhone" @click.stop>净化电话号码</el-checkbox></div></template>
              <div class="collapse-content text-gray">自动提取纯数字手机号，并去除 +86 等前缀。</div>
            </el-collapse-item>
            <el-collapse-item name="fill">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.doFill" @click.stop>填充空值</el-checkbox><span class="desc-text">配置填充内容</span></div></template>
              <div class="collapse-content"><el-input v-model="configForm.fillText" size="small" placeholder="例如：未知" style="width: 200px;" /></div>
            </el-collapse-item>
            <el-collapse-item name="dup">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.dropDup" @click.stop>删除重复行</el-checkbox></div></template>
              <div class="collapse-content text-gray">删除完全一样的数据行，仅保留第一条。</div>
            </el-collapse-item>
          </el-collapse>

          <!-- 阶段二 -->
          <div class="stage-title">阶段二：标准化与计算（统口径）</div>
          <el-collapse v-model="activeCollapse">
            <el-collapse-item name="num">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.doCleanNum" @click.stop>统一数值与金额</el-checkbox><span class="desc-text">设置清洗格式</span></div></template>
              <div class="collapse-content">
                <el-checkbox v-model="configForm.cleanNoise" style="display: block; margin-bottom: 5px;">清理数字杂音</el-checkbox>
                <el-checkbox v-model="configForm.convertUnits" style="display: block; margin-bottom: 5px;">自动换算数量级 (万/千)</el-checkbox>
                <el-checkbox v-model="configForm.removeCurrency" style="display: block;">去除货币符号 (￥/$)</el-checkbox>
              </div>
            </el-collapse-item>
            <el-collapse-item name="date">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.doUnifyDate" @click.stop>统一日期</el-checkbox><span class="desc-text">配置日期格式</span></div></template>
              <div class="collapse-content">
                <el-input v-model="configForm.dateFormat" size="small" placeholder="例如：2026-05-13" style="width: 200px; margin-bottom: 5px;" />
                <div class="text-gray" style="font-size: 12px;">将支持多种混乱的日期格式转化为统一格式。</div>
              </div>
            </el-collapse-item>
            <el-collapse-item name="calc">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.doAutoCalc" @click.stop>智能逻辑填补</el-checkbox><span class="desc-text">自动计算缺失值</span></div></template>
              <div class="collapse-content">
                <el-checkbox v-model="configForm.calcAmount" style="display: block; margin-bottom: 5px;">补全金额 (数量 × 单价)</el-checkbox>
                <el-checkbox v-model="configForm.calcPrice" style="display: block; margin-bottom: 5px;">补全单价 (金额 ÷ 数量)</el-checkbox>
                <el-checkbox v-model="configForm.calcQty" style="display: block;">补全数量 (金额 ÷ 单价)</el-checkbox>
              </div>
            </el-collapse-item>
          </el-collapse>

          <!-- 阶段三 -->
          <div class="stage-title">阶段三：审查与排版（抓错漏）</div>
          <el-collapse v-model="activeCollapse">
            <el-collapse-item name="check">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.doCheckLogic" @click.stop>金额逻辑审查</el-checkbox><span class="desc-text">校验勾稽关系</span></div></template>
              <div class="collapse-content text-gray">校验“数量 × 单价 = 金额”是否正确，发现异常将在右侧预警。</div>
            </el-collapse-item>
            <el-collapse-item name="total">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.doTotal" @click.stop>自动合计</el-checkbox><span class="desc-text">生成合计行</span></div></template>
              <div class="collapse-content text-gray">在表格底部自动追加一行“合计”汇总数据。</div>
            </el-collapse-item>
          </el-collapse>

          <!-- 阶段四 -->
          <div class="stage-title">阶段四：拆分与导出（切蛋糕）</div>
          <div class="warning-box">【提示】：清洗是后续拆分和脱敏的前提。如果出现脱敏遗漏或拆分结果错乱，请检查是否开启了【阶段一】的基础清洗及【阶段二】的字段值归一化！</div>
          <el-collapse v-model="activeCollapse">
            <el-collapse-item name="desensitize">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.doDesensitize" @click.stop>一键数据脱敏</el-checkbox><span class="desc-text">脱敏设置</span></div></template>
              <div class="collapse-content" style="padding: 10px 0;">
                <p class="text-red" style="font-size: 12px; margin-top: 0; padding: 0 10px;"><b>【重要】</b>：脱敏前请确保内容干净！请在下方配置脱敏规则。</p>
                <div style="width: 100%; overflow: hidden;">
                  <el-table :data="desensitizeList" size="small" max-height="250" v-loading="desensitizeLoading" border style="width: 100%;">
                    <el-table-column prop="columnName" label="列名" width="130" show-overflow-tooltip />
                    <el-table-column label="脱敏规则">
                      <template #default="scope">
                        <el-select v-model="scope.row.rule" size="small" style="width: 100%;">
                          <el-option label="不脱敏" value="不脱敏" /><el-option label="姓名" value="姓名" /><el-option label="手机号" value="手机号" /><el-option label="身份证" value="身份证" /><el-option label="邮箱" value="邮箱" />
                        </el-select>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </div>
            </el-collapse-item>
            <el-collapse-item name="split">
              <template #title><div class="title-row"><el-checkbox v-model="configForm.doSplit" @click.stop disabled>按列拆分打包</el-checkbox><span class="desc-text">拆分设置</span></div></template>
              <div class="collapse-content text-gray">该功能将在下阶段重构中开放。</div>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <div v-if="currentTask.id" style="margin-top: 15px; text-align: right; padding-bottom: 15px;">
          <el-button @click="currentTask = {}">取消选中</el-button>
          <el-button type="primary" @click="saveConfig">保存配置</el-button>
        </div>
      </el-card>
    </div>

    <!-- 右侧 -->
    <div class="right-panel">
      <el-card class="box-card list-card">
        <template #header><div class="card-header"><h3>📋 历史任务列表</h3><el-button size="small" @click="fetchTasks" icon="Refresh">刷新</el-button></div></template>
        <el-table :data="tableData" stripe height="100%" v-loading="tableLoading" @row-click="handleRowClick" highlight-current-row>
          <el-table-column prop="id" label="ID" width="60" />
          <el-table-column prop="taskName" label="任务名称" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="scope"><el-tag :type="scope.row.status === 'PENDING' ? 'warning' : 'success'" size="small">{{ scope.row.status }}</el-tag></template>
          </el-table-column>
          <el-table-column label="操作" width="220" align="center">
            <template #default="scope">
              <el-button type="success" size="small" @click.stop="executeTask(scope.row)" :disabled="scope.row.status === 'SUCCESS'">{{ scope.row.status === 'SUCCESS' ? '已清洗' : '执行导出' }}</el-button>
              <el-button v-if="scope.row.status === 'SUCCESS'" type="warning" size="small" @click.stop="downloadFile(scope.row.id)">下载</el-button>
              <el-button type="danger" size="small" plain @click.stop="handleDelete(scope.row.id)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <div v-if="errorPanelVisible" class="error-collapse-wrapper">
        <el-collapse v-model="activeErrorCollapse">
          <el-collapse-item name="errors">
            <template #title><div style="display: flex; align-items: center; color: #F56C6C; font-weight: bold; font-size: 14px;"><el-icon style="margin-right: 5px;"><WarningFilled /></el-icon> 全局提示与警告</div></template>
            <div class="error-rich-text" v-drag-scroll v-html="formatErrorText"></div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <el-card class="box-card preview-card" v-loading="previewLoading">
        <template #header><div class="card-header"><h3>👁️ 清洗后数据实时预览 (仅展示前100行)</h3><span style="font-size: 12px; color: #909399;" v-if="currentTask.id">当前任务：{{ currentTask.taskName }}</span></div></template>
        <div class="table-container" v-drag-scroll>
          <el-table :data="currentPreviewData" border stripe style="width: 100%;" height="100%" v-if="currentPreviewData.length > 0">
            <el-table-column v-for="col in currentPreviewColumns" :key="col" :prop="col" :label="col" min-width="120" show-overflow-tooltip />
          </el-table>
          <el-empty v-else description="当前 Sheet 无数据或清洗失败，请检查警告信息" />
        </div>
        <div class="sheet-tabs-container" v-if="previewSheets.length > 0">
          <div v-for="(sheet, index) in previewSheets" :key="index" :class="['sheet-tab', { active: currentSheetIndex === index }]" @click="currentSheetIndex = index">{{ sheet.name }}</div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, WarningFilled } from '@element-plus/icons-vue'

// 拖拽指令
const vDragScroll = {
  mounted(el) {
    let isDown = false, startX, startY, scrollLeft, scrollTop, scrollEl;
    el.addEventListener('mousedown', (e) => {
      if (['INPUT', 'BUTTON', 'A', 'TEXTAREA', '.el-select', '.el-checkbox', '.el-switch', '.el-radio', '.el-scrollbar__bar'].some(tag => e.target.closest(tag))) return;
      scrollEl = el.querySelector('.el-scrollbar__wrap') || el.querySelector('.el-table__body-wrapper') || el;
      if (scrollEl.scrollWidth <= scrollEl.clientWidth && scrollEl.scrollHeight <= scrollEl.clientHeight) return;
      isDown = true; el.style.cursor = 'grabbing'; startX = e.clientX; startY = e.clientY; scrollLeft = scrollEl.scrollLeft; scrollTop = scrollEl.scrollTop;
      document.body.style.userSelect = 'none'; e.preventDefault(); 
    });
    window.addEventListener('mousemove', (e) => {
      if (!isDown) return; e.preventDefault(); 
      if (scrollEl) { scrollEl.scrollLeft = scrollLeft - (e.clientX - startX) * 1.5; scrollEl.scrollTop = scrollTop - (e.clientY - startY) * 1.5; }
    });
    window.addEventListener('mouseup', () => { if (isDown) { isDown = false; el.style.cursor = 'grab'; document.body.style.userSelect = ''; } });
    el.style.cursor = 'grab';
  }
};

// 状态变量
const taskName = ref(''); const fileList = ref([]); const loading = ref(false); const showUpload = ref(true)
const tableData = ref([]); const tableLoading = ref(false)
const errorPanelVisible = ref(false); const errorList = ref([]); const activeErrorCollapse = ref(['errors'])
const previewLoading = ref(false); const previewSheets = ref([]); const currentSheetIndex = ref(0)
const currentTask = ref({}); const desensitizeList = ref([]); const desensitizeLoading = ref(false); const activeCollapse = ref([])

const currentPreviewData = computed(() => { if (!previewSheets.value[currentSheetIndex.value]) return []; return previewSheets.value[currentSheetIndex.value].data || [] })
const currentPreviewColumns = computed(() => { if (!previewSheets.value[currentSheetIndex.value]) return []; return previewSheets.value[currentSheetIndex.value].columns || [] })

const defaultConfig = {
  dropEmpty: true, dropSummary: true, dropDup: true, doCleanPhone: true,
  doFill: false, fillText: '未知', doCleanNum: true, cleanNoise: true,
  convertUnits: true, removeCurrency: true, doUnifyDate: false,
  dateFormat: '2026-05-13', 
  doAutoCalc: true, calcAmount: true, calcPrice: true, calcQty: true, doCheckLogic: true, doTotal: true,
  doDesensitize: false, doSplit: false
}
const configForm = ref(JSON.parse(JSON.stringify(defaultConfig)))

const formatErrorText = computed(() => {
  if (!errorList.value || errorList.value.length === 0) return ''
  let htmlStr = ''
  errorList.value.forEach(errStr => {
    let formatted = errStr.replace(/\n/g, '<br>').replace(/\*\*(.*?)\*\*/g, '<strong style="color:#303133; font-size:14px; display:inline-block; margin-top:8px;">$1</strong>').replace(/- (.*?)(<br>|$)/g, '<div style="margin-left: 10px; margin-bottom: 4px;">◦ $1</div>')
    htmlStr += `<div style="margin-bottom: 15px;">${formatted}</div>`
  })
  return htmlStr
})

// 🚨 核心：加了 15 秒超时保护，防止转圈卡死
let previewTimer = null
const fetchPreview = async () => {
  if (!currentTask.value.id) return
  previewLoading.value = true
  try {
    const res = await axios.post(`http://localhost:8080/api/tasks/preview/${currentTask.value.id}`, {
      configJson: JSON.stringify(configForm.value)
    }, {
      timeout: 15000 // 15秒超时，超时直接报错，结束转圈
    })
    const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
    
    if (data.status === 'success') {
      previewSheets.value = data.sheets || []
      if (currentSheetIndex.value >= previewSheets.value.length) currentSheetIndex.value = 0
      let allErrors = []
      previewSheets.value.forEach(sheet => { if (sheet.errors && sheet.errors.length > 0) allErrors = allErrors.concat(sheet.errors) })
      if (allErrors.length > 0) { errorList.value = allErrors; errorPanelVisible.value = true; } 
      else { errorPanelVisible.value = false; }
    } else { ElMessage.error('预览失败：' + data.message); previewSheets.value = []; }
  } catch (error) { 
    console.error('预览请求异常:', error); 
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('清洗超时！可能是数据量太大或后端卡死，请检查 Python 控制台。')
    } else {
      ElMessage.error('接口异常：' + (error.message || '请检查后端'))
    }
    previewSheets.value = [];
  } 
  finally { previewLoading.value = false; }
}

watch(configForm, () => {
  if (!currentTask.value.id) return
  clearTimeout(previewTimer)
  previewTimer = setTimeout(() => { fetchPreview() }, 800) 
}, { deep: true })

const fetchTasks = async (selectFirst = false) => {
  tableLoading.value = true
  try {
    const res = await axios.get('http://localhost:8080/api/tasks/test')
    tableData.value = res.data
    if (selectFirst && tableData.value.length > 0) handleRowClick(tableData.value[0])
  } catch (error) { ElMessage.error('获取列表失败') } finally { tableLoading.value = false }
}

onMounted(() => fetchTasks())

const handleFileChange = (file, files) => fileList.value = files
const handleExceed = () => ElMessage.warning('只能上传一个文件')
const submitUpload = async () => {
  if (!taskName.value.trim()) return ElMessage.warning('请填写任务名称')
  if (fileList.value.length === 0) return ElMessage.warning('请选择文件')
  loading.value = true
  const formData = new FormData()
  formData.append('taskName', taskName.value)
  formData.append('file', fileList.value[0].raw)
  try {
    const res = await axios.post('http://localhost:8080/api/tasks/upload', formData)
    ElMessage.success(res.data)
    taskName.value = ''; fileList.value = []; showUpload.value = false; currentTask.value = {}
    configForm.value = JSON.parse(JSON.stringify(defaultConfig)); desensitizeList.value = []; previewSheets.value = []; activeCollapse.value = []; errorPanelVisible.value = false
    fetchTasks(true)
  } catch (error) { ElMessage.error('上传失败') } finally { loading.value = false }
}

const handleRowClick = async (row) => {
  currentTask.value = row; showUpload.value = false
  configForm.value = JSON.parse(JSON.stringify(defaultConfig)); desensitizeList.value = []; previewSheets.value = []; currentSheetIndex.value = 0; activeCollapse.value = []; errorPanelVisible.value = false
  
  try {
    const res = await axios.get(`http://localhost:8080/api/tasks/config/${row.id}`)
    if (res.data && Object.keys(res.data).length > 0) {
      configForm.value = res.data
      if (configForm.value.dateFormat) {
        configForm.value.dateFormat = configForm.value.dateFormat.replace(/日/g, '')
      }
      if (res.data.desensitizeList) desensitizeList.value = res.data.desensitizeList
    }
    if (configForm.value.doDesensitize && desensitizeList.value.length === 0) handleDesensitizeChange(true)
    fetchPreview()
  } catch (error) { console.error('获取配置失败') }
}

const handleDesensitizeChange = async (val) => {
  if (!val || !currentTask.value.id) return
  if (desensitizeList.value.length > 0) return
  desensitizeLoading.value = true
  try {
    const res = await axios.get(`http://localhost:8080/api/tasks/columns/${currentTask.value.id}`)
    const resData = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
    desensitizeList.value = (resData.columns || []).map(c => {
      let rule = '不脱敏'
      if (['手机', '电话'].some(k => String(c).includes(k))) rule = '手机号'
      else if (['身份证'].some(k => String(c).includes(k))) rule = '身份证'
      else if (['姓名', '联系人'].some(k => String(c).includes(k))) rule = '姓名'
      return { columnName: c, rule }
    })
  } catch (error) { console.warn('获取列名失败') } finally { desensitizeLoading.value = false }
}

watch(() => configForm.value.doDesensitize, (newVal) => {
  if (newVal) { handleDesensitizeChange(true); if (!activeCollapse.value.includes('desensitize')) activeCollapse.value.push('desensitize') } 
  else { activeCollapse.value = activeCollapse.value.filter(item => item !== 'desensitize') }
})

const saveConfig = async () => {
  if (!currentTask.value.id) return ElMessage.warning('请先选择一个任务')
  try {
    configForm.value.desensitizeList = desensitizeList.value
    await axios.post('http://localhost:8080/api/tasks/config/save', { taskId: currentTask.value.id, configJson: JSON.stringify(configForm.value) })
    ElMessage.success('配置保存成功')
  } catch (error) { ElMessage.error('保存失败') }
}

const executeTask = async (row) => {
  if (currentTask.value.id === row.id) {
    configForm.value.desensitizeList = desensitizeList.value
    await axios.post('http://localhost:8080/api/tasks/config/save', { taskId: row.id, configJson: JSON.stringify(configForm.value) })
  }
  const loadingMsg = ElMessage({ message: '正在导出文件...', type: 'info', duration: 0 })
  try {
    const res = await axios.post(`http://localhost:8080/api/tasks/execute/${row.id}`)
    loadingMsg.close()
    const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data;
    if (data.status === 'success') { ElMessage.success('导出执行成功！'); fetchTasks() } 
    else { ElMessage.error('导出失败：' + data.message) }
  } catch (error) { loadingMsg.close(); ElMessage.error('导出失败，请检查后端') }
}

const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个任务吗？', '警告', { type: 'warning' })
    await axios.post(`http://localhost:8080/api/tasks/delete/${id}`)
    ElMessage.success('删除成功')
    if (currentTask.value.id === id) currentTask.value = {}
    fetchTasks()
  } catch (error) { if (error !== 'cancel') ElMessage.error('删除失败') }
}

const downloadFile = (id) => { window.open(`http://localhost:8080/api/tasks/download/${id}`, '_blank') }
</script>

<style scoped>
/* 样式部分和之前保持一致，不用动 */
:global(body) { margin: 0; padding: 0; overflow: hidden; background-color: #f0f2f5; }
.app-layout { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; box-sizing: border-box; padding: 15px; display: flex; gap: 20px; }
.left-panel { width: 460px; flex-shrink: 0; height: 100%; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; box-sizing: border-box; scrollbar-width: thin; }
.left-panel::-webkit-scrollbar { width: 6px; }
.left-panel::-webkit-scrollbar-thumb { background-color: #c0c4cc; border-radius: 3px; }
.right-panel { flex: 1; min-width: 0; height: 100%; display: flex; flex-direction: column; gap: 15px; overflow: hidden; }
.box-card { border-radius: 8px; box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05); display: flex; flex-direction: column; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-header h3 { margin: 0; font-size: 16px; color: #303133; }
.list-card { height: 220px; flex-shrink: 0; }
.preview-card { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
:deep(.el-card__body) { flex: 1; display: flex; flex-direction: column; padding: 15px; overflow: hidden; }
.config-card :deep(.el-card__body) { overflow-y: auto; padding: 0; }
.error-collapse-wrapper { background-color: #FEF0F0; border: 1px solid #FDE2E2; border-radius: 8px; flex-shrink: 0; max-height: 220px; display: flex; flex-direction: column; }
:deep(.error-collapse-wrapper .el-collapse) { border: none; background-color: transparent; height: 100%; display: flex; flex-direction: column; }
:deep(.error-collapse-wrapper .el-collapse-item) { height: 100%; display: flex; flex-direction: column; }
:deep(.error-collapse-wrapper .el-collapse-item__header) { background-color: transparent; border-bottom: 1px solid #FDE2E2; padding: 0 15px; height: 40px; flex-shrink: 0; }
:deep(.error-collapse-wrapper .el-collapse-item__wrap) { background-color: transparent; border-bottom: none; flex: 1; overflow-y: hidden; }
:deep(.error-collapse-wrapper .el-collapse-item__content) { padding: 10px 15px; height: 100%; }
.error-rich-text { font-size: 13px; color: #606266; line-height: 1.6; max-height: 140px; overflow-y: auto; padding-right: 5px; scrollbar-width: thin; }
.error-rich-text::-webkit-scrollbar { width: 6px; }
.error-rich-text::-webkit-scrollbar-thumb { background-color: #f5a3a3; border-radius: 3px; }
.upload-wrapper, :deep(.el-upload) { width: 100% !important; display: block !important; }
:deep(.el-upload-dragger) { width: 100% !important; box-sizing: border-box !important; padding: 30px 10px !important; display: flex; flex-direction: column; justify-content: center; align-items: center; }
.table-container { flex: 1; overflow: hidden; border: 1px solid #ebeef5; border-radius: 4px; }
.table-container :deep(.el-table) { cursor: inherit !important; }
.table-container :deep(.el-table th), .table-container :deep(.el-table tr), .table-container :deep(.el-table td) { cursor: inherit !important; }
.sheet-tabs-container { display: flex; overflow-x: auto; border-top: 1px solid #ebeef5; background: #f8f9fa; padding: 5px 10px; gap: 8px; flex-shrink: 0; }
.sheet-tab { padding: 4px 16px; background: #fff; border: 1px solid #dcdfe6; border-radius: 4px; cursor: pointer; font-size: 13px; white-space: nowrap; user-select: none; transition: all 0.2s; color: #606266; }
.sheet-tab:hover { border-color: #409eff; color: #409eff; }
.sheet-tab.active { background: #409eff; color: white; border-color: #409eff; font-weight: bold; }
.config-container { padding: 10px 15px 20px 15px; }
.stage-title { font-size: 14px; font-weight: bold; color: #303133; background-color: #f4f4f5; padding: 8px 12px; border-radius: 4px; margin-top: 15px; margin-bottom: 5px; border-left: 3px solid #409EFF; }
:deep(.el-collapse) { border-top: none; border-bottom: none; }
:deep(.el-collapse-item__header) { border-bottom: none; height: 40px; line-height: 40px; padding-left: 0; padding-right: 10px; }
:deep(.el-collapse-item__wrap) { border-bottom: none; background-color: #fafafa; border-radius: 4px; margin-bottom: 5px; }
.title-row { display: flex; justify-content: space-between; align-items: center; width: 100%; }
.desc-text { color: #909399; font-size: 12px; }
.collapse-content { padding: 10px 15px; background-color: #fafafa; border-radius: 4px; font-size: 13px; }
.text-gray { color: #606266; }
.text-red { color: #F56C6C; }
.warning-box { background-color: #fdf6ec; color: #e6a23c; font-size: 12px; padding: 10px; border-radius: 4px; margin: 10px 0; line-height: 1.5; }
</style>