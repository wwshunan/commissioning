<template>
  <el-container>
    <el-header>
      <h3>轨道校正</h3>
    </el-header>
    <el-main>
      <el-row :gutter="40">
        <el-col :span="8">
          <el-form ref="form" :model="form" label-position="top" style="text-align: left">
            <el-form-item label="轨道偏移量减小比例">
              <el-input v-model="form.alpha"></el-input>
            </el-form-item>
            <el-form-item label="选择校正铁和bpm">
              <el-tree
                  ref="tree"
                  :data="form.steer_data"
                  show-checkbox
                  node-key="id"
                  :props="defaultProps">
              </el-tree>
            </el-form-item>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="常温铁电流改变量 (A)">
                  <el-input v-model="form.rm_step"></el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="超导铁电流改变量 (A)">
                  <el-input v-model="form.sc_step"></el-input>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="常温铁电流限制量 (A)">
                  <el-input v-model="form.rm_lim"></el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="超导铁电流限值量 (A)">
                  <el-input v-model="form.sc_lim"></el-input>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item style="text-align: right">
              <div>
                <el-button type="primary" plain @click="compute_strength">计算校正量</el-button>
                <el-button type="primary" plain @click="set_corrector">设置校正铁电流</el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="16">
          <div>
            <el-table :data="corrector_strength" max-height="700px">
              <caption>校正铁值:</caption>
              <el-table-column
                  prop="label"
                  label="校正铁名称">
              </el-table-column>
              <el-table-column
                  prop="value"
                  label="校正电流">
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
        steer_data: [],
        alpha: 0,
        rm_step: 4,
        rm_lim: 15,
        sc_step: 14,
        sc_lim: 50,
      },
      defaultProps: {
        children: 'children',
        label: 'label'
      },
      corrector_strength: []
    }
  },
  mounted() {
    this.load_config()
  },
  methods: {
    async get_status(task_id) {
      const path = `/commissioning/orbit-correction/${task_id}`;
      try {
        const res = await request({
          url: path,
          method: 'get'
        })
        const taskStatus = res.data.task_status;
        Message({
          message: res.data.task_status,
          type: 'info',
          duration: 3 * 1000
        })
        if (taskStatus === 'finished') {
          this.corrector_strength = []
          for (const [key, obj] of Object.entries(res.data.task_result)) {
            this.corrector_strength.push({
              "label": key,
              "value": obj["strength"],
              "pv": obj["pv"]
            })
          }
        }

        if (taskStatus === 'finished' || taskStatus === 'failed') return false;
        setTimeout(async () => {
          await this.get_status(res.data.task_id);
        }, 5000);
      } catch (e) {
        console.log(e)
      }
    },
    async load_config() {
      const path = '/commissioning/orbit-correction/get-config';
      const response = await request({
        url: path,
        method: 'get',
      })
      this.form.steer_data = response.data
    },
    async compute_strength() {
      const path = '/commissioning/orbit-correction/compute-strength';

      const res = await request({
        url: path,
        data: {
          keys: this.$refs.tree.getCheckedKeys(),
          rm_step: this.form.rm_step,
          sc_step: this.form.sc_step,
          rm_lim: this.form.rm_lim,
          sc_lim: this.form.sc_lim,
          alpha: this.form.alpha
        },
        method: 'post',
      })
      await this.get_status(res.task_id)
    },
    async set_corrector() {
      const path = '/commissioning/orbit-correction/set-strength';
      const res = await request({
        url: path,
        data: {
          keys: this.$refs.tree.getCheckedKeys(),
          strength: this.corrector_strength
        },
        method: 'post',
      })
    }
  }
}
</script>

<style scoped>
</style>