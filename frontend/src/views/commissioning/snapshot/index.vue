<template>
  <el-container>
    <el-header>
      <h3>机器快照</h3>
    </el-header>
    <el-main>
      <el-row :gutter="40">
        <el-col :span="8">
          <el-form ref="form" :model="form" size="mini">
            <el-form-item label="粒子种类">
              <el-select v-model="particle_type">
                <el-option
                    v-for="item in particle_options"
                    :key="item.text"
                    :label="item.text"
                    :value="item.value">
                </el-option>
              </el-select>
            </el-form-item>
            <el-form-item label="流强 [uA]">
              <el-col :span="10">
                <el-input v-model="current"></el-input>
              </el-col>
            </el-form-item>
            <el-form-item label="能量 [MeV]">
              <el-col :span="10">
                <el-input v-model="energy"></el-input>
              </el-col>
            </el-form-item>
            <el-form-item>
              <div style="text-align: left; font-weight: bold">快照描述</div>
              <el-input
                  type="textarea"
                  :rows="3"
                  placeholder="请输入内容"
                  v-model="textarea">
              </el-input>
            </el-form-item>
            <el-form-item>
              <div style="text-align: left; font-weight: bold">选择机器快照元件</div>
              <el-tree
                  ref="tree"
                  :data="form.elements"
                  show-checkbox
                  node-key="id"
                  :props="defaultProps">
              </el-tree>
            </el-form-item>
            <el-form-item style="text-align: center">
              <div>
                <el-button type="primary" plain @click="save">保存快照</el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="16">
            <el-row>
              <el-col :span="10">
                <div class="block">
                  <span>开始时间 </span>
                  <el-date-picker
                      v-model="beginDate"
                      type="datetime"
                      placeholder="选择日期时间"
                      align="right"
                      :picker-options="pickerOptions">
                  </el-date-picker>
                </div>
              </el-col>
              <el-col :span="10">
                <div class="block">
                  <span>结束时间 </span>
                  <el-date-picker
                      v-model="endDate"
                      type="datetime"
                      placeholder="选择日期时间"
                      align="right"
                      :picker-options="pickerOptions">
                  </el-date-picker>
                </div>
              </el-col>
              <el-col :span="4">
                <el-button type="primary" plain @click="acquire">查询快照</el-button>
              </el-col>
            </el-row>

            <div style="margin-top: 20px; margin-bottom: 20px; text-align: left">历史快照:</div>
            <el-table
                v-if="snapshots"
                :data="snapshots"
                ref="table"
                highlight-current-row
                @current-change="handleCurrentChange"
                max-height="700px">
              <el-table-column
                  prop="timestamp"
                  label="时间">
              </el-table-column>
              <el-table-column
                  prop="particle_type"
                  label="粒子种类">
              </el-table-column>
              <el-table-column
                  prop="current"
                  label="流强 (uA)">
              </el-table-column>
              <el-table-column
                  prop="energy"
                  label="能量 (MeV)">
              </el-table-column>
              <el-table-column
                  prop="subject"
                  label="描述">
              </el-table-column>
            </el-table>
          <div style="margin-top: 20px">
            <el-row>
              <el-col :span="6">
                <el-button type="warning" plain @click="restore">还原快照</el-button>
              </el-col>
              <el-col :span="6">
                <el-button type="primary" plain @click="compare">对比快照</el-button>
              </el-col>
              <el-col :span="6">
                <el-button type="danger" plain @click="remove">删除快照</el-button>
              </el-col>
            </el-row>
          </div>
          <div style="margin-top: 20px" v-if="diffs">
            <div style="text-align: left; font-weight: bold">超阈值的元件历史值:</div>
            <el-table :data="diffs">
              <el-table-column
                  prop="label"
                  label="元件名">
              </el-table-column>
              <el-table-column
                  prop="diff"
                  label="历史值">
              </el-table-column>
            </el-table>
          </div>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script>
import request from '@/utils/request'
import { Message } from 'element-ui'


export default {
  data() {
    return {
      form: {
        elements: [],
      },
      defaultProps: {
        children: 'children',
        label: 'label'
      },
      diffs: [],
      corrector_strength: [],
      textarea: '',
      energy: '',
      current: '',
      particle_type: "40Ca13+",
      snapshots: [],
      particle_options: [
        {value: "36Ar12+", text: "36Ar12+"},
        {value: "40Ar13+", text: "40Ar13+"},
        {value: "40Ca13+", text: "40Ca13+"},
        {value: "55Mn17+", text: "55Mn17+"},
      ],
      beginDate: '',
      endDate: '',
      selected_row_id: '',
      pickerOptions: {
        shortcuts: [{
          text: '今天',
          onClick(picker) {
            picker.$emit('pick', new Date());
          }
        }, {
          text: '昨天',
          onClick(picker) {
            const date = new Date();
            date.setTime(date.getTime() - 3600 * 1000 * 24);
            picker.$emit('pick', date);
          }
        }, {
          text: '一周前',
          onClick(picker) {
            const date = new Date();
            date.setTime(date.getTime() - 3600 * 1000 * 24 * 7);
            picker.$emit('pick', date);
          }
        }]
      }
    }
  },
  mounted() {
    this.load_config()
  },
  methods: {
    async load_config() {
      const path = '/commissioning/snapshot/get-config';
      const response = await request({
        url: path,
        method: 'get',
      })
      this.form.elements = response.data
    },
    handleCurrentChange(val) {
      this.selected_row_id = val?.id
    },
    async save() {
      const path = '/commissioning/snapshot/save';
      try {
        const response = await request({
          url: path,
          data: {
            keys: this.$refs.tree.getCheckedKeys(),
            particle_type: this.particle_type,
            current: this.current,
            energy: this.energy,
            subject: this.textarea
          },
          method: 'post',
        })
        Message({
          message: response['message'],
          type: 'success',
          duration: 5000
        }) 
      } catch (e) {
        console.log(e)
      }
    },
    async acquire() {
      const path = '/commissioning/snapshot/acquire';
      const response = await request({
        url: path,
        data: {
          beginDate: this.beginDate,
          endDate: this.endDate,
        },
        method: 'post',
      })
      this.snapshots = response.data
    },
    async remove() {
      const path = '/commissioning/snapshot/remove';
      const response = await request({
        url: path,
        data: {
          id: this.selected_row_id
        },
        method: 'post',
      })
      this.snapshots = this.snapshots.filter(e => 
        e.id !== this.selected_row_id
      )
    },
    async restore() {
      const path = '/commissioning/snapshot/restore';
      const response = await request({
        url: path,
        data: {
          id: this.selected_row_id,
        },
        method: 'post',
      })
      this.diffs = response.data
    },
    async compare() {
      const path = '/commissioning/snapshot/compare';
      try {
        const response = await request({
          url: path,
          data: {
            id: this.selected_row_id,
          },
          method: 'post',
        })
        this.diffs = []
        for (const [label, value] of Object.entries(response.data)) {
          this.diffs.push({
            'label': label,
            'diff': value
          })
        }
      } catch (e) {
        Message({
          message: 'PV无法连接！',
          type: 'error',
          duration: 5 * 1000
        })
      }
    },
  }
}
</script>

<style scoped>
</style>