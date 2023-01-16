<template>
  <el-container>
    <el-header>
      <h3>调束任务调度工具</h3>
    </el-header>
    <el-main>
      <el-form ref="form" :model="form" size="mini">
        <el-form-item>
          <div style="text-align: left; font-weight: bold">已装载任务序列</div>
          <el-table :data="tasks" ref="table" default-expand-all row-key="id" :tree-props="{children: 'children'}"
            style="width: 100%" max-height="700px" highlight-current-row @current-change="handleCurrentChange">
            <el-table-column prop="name" label="任务名" width="180">
            </el-table-column>
            <el-table-column prop="description" label="描述" width="250">
            </el-table-column>
            <el-table-column prop="directive" label="指令" width="180">
              <template slot-scope="scope">
                <el-select v-model="scope.row.directive">
                  <el-option v-for="item in options" :key="item.value" :label="item.label" :value="item.value">
                  </el-option>
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="id, type" label="执行" width="100">
              <template slot-scope="scope">
                <el-button v-if="scope.row.type !== 'seq'" size="mini" type="success" @click="exec_task(scope.row.id)">RUN</el-button>
              </template>
            </el-table-column>
            <el-table-column prop="result" label="结果">
              <template slot-scope="scope">
                <div v-html="scope.row.result"></div>
              </template>
            </el-table-column>
          </el-table>
        </el-form-item>
        <el-form-item style="text-align: right">
          <el-button type="primary" @click="exec_sequence" text-aligh="right">自动执行</el-button>
          <el-button type="danger" @click="stop" text-aligh="right">停止</el-button>
        </el-form-item>
      </el-form>
    </el-main>
  </el-container>
</template>

<script>
import request from '@/utils/request'
import { Message } from 'element-ui'


const results = {
  'NOT_STARTED': "<span>NOT_STARTED</span>",
  'OK': "<span style='color: green; '>FINISHED</span>",
  'FAILURE': "<span style='color: red; '>FINISHED_FAULTY</span>",
  'SKIPPED': "<span style='color: yellow; '>SKIPPED</span>",
}

function create_info(key, detail) {
  let msg = ''
  switch (key) {
    case 'OK':
      msg = `<span style='color: green; '>${detail}</span>`
      break;
  
    case 'FAILURE':
      msg = `<span style='color: red; '>${detail}</span>`
      break;

    default:
      break;
  }
  return msg
}

function update_task_status(tasks, target_id, status) {
  let result = false
  tasks.forEach(e => {
    if (e.id === target_id) {
      e.result = create_info(status.key, status.detail)
      if (result.key === 'OK') return true
    }
    if ('children' in e) result = update_task_status(e.children, target_id, status)
  })
  return result
}

export default {
  data() {
    return {
      task_status: 'RUN',
      current_row: null,
      options: [
        { 
          value: 'RUN',
          label: 'RUN'
        },
        { 
          value: 'BREAKPOINT',
          label: 'BREAKPOINT'
        }
      ],
      tasks: [],
    }
  },
  async mounted() {
    await this.get_sequences()
    await this.init_sequence()
    this.$refs.table.setCurrentRow(this.tasks[0])
  },
  methods: {
    handleCurrentChange(val) {
      this.current_row = val
    },
    async get_sequences() {
      const path = '/commissioning/sequencer/load-sequences';
      const res = await request({
        url: path,
        method: 'get',
      })
      this.tasks = res.sequences
    },
    async get_status(tasks, id) {
      const path = `/commissioning/sequencer/${tasks[id].task}`;
      try {
        const res = await request({
          url: path,
          method: 'get'
        })
        const taskStatus = res.data.task_status;
        if (taskStatus === 'finished' || taskStatus === 'failed') {
          update_task_status(this.tasks, tasks[id].id, res.data.task_result)
        }
        if (taskStatus === 'finished' && id + 1 === tasks.length || taskStatus === 'failed') return false
        if (taskStatus === 'finished' && id <= tasks.length) id++

        setTimeout(async () => {
          await this.get_status(tasks, id);
        }, 1000);
      } catch (e) {
        console.log(e)
      }
    },
    async init_sequence() {
      const path = '/commissioning/sequencer/init-sequence';
      const res = await request({
        url: path,
        data: {id: this.tasks[0].id},
        method: 'post',
      })
    },
    async exec_sequence() {
      const path = '/commissioning/sequencer/execute';
      const res = await request({
        url: path,
        method: 'post',
      })
      await this.get_status(res.tasks, 0)
    },
    async exec_task(task_id) {
      const path = '/commissioning/sequencer/step';
      const res = await request({
        url: path,
        data: { id: task_id },
        method: 'post',
      })
      await this.get_status(res.tasks, 0)
      Message({
        message: "任务已执行，请等待",
        type: 'success',
        duration: 5 * 1000
      })
    } 
  }
}
</script>

<style scoped>
</style>