<template>
  <el-container>
    <el-header>
      <h3>磁铁和BPM顺序测试工具</h3>
    </el-header>
    <el-main>
      <el-row :gutter="40">
        <el-col :span="8">
          <el-form ref="form" :model="form" label-position="top" style="text-align: left">
            <el-form-item label="选择测试段">
              <el-radio-group v-model="section">
                <el-radio v-for="s in sections" :label="s" :key="s" @change="section_change">{{s}}</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="选择校正铁">
              <el-radio-group v-model="corr">
                <el-radio v-for="s in correctors" :label="s.id" :key="s.id">{{s.id}}</el-radio>
              </el-radio-group>
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
            <el-form-item label="保存文件名">
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-input v-model="form.saved_file"></el-input>
                </el-col>
                <el-col :span="12">
                  <el-button type="primary" size="small" @click="create_saved_file">
                    创建
                  </el-button>
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item
              prop="email"
              label="邮箱"
              :rules="[
                { required: true, message: '请输入邮箱地址', trigger: 'blur' },
                { type: 'email', message: '请输入正确的邮箱地址', trigger: ['blur', 'change'] }
              ]"
            >
              <el-input v-model="form.email"></el-input>
            </el-form-item>
            <el-form-item style="text-align: right">
              <div>
                <el-button type="primary" plain @click="update_orbit">获取当前轨道</el-button>
                <el-button type="primary" plain @click="correct">粗校轨</el-button>
                <el-button type="primary" plain @click="set_corrector">踢轨响应</el-button>
              </div>
            </el-form-item>
          </el-form>
        </el-col>
        <el-col :span="16">
          <div ref="chart"></div>
        </el-col>
      </el-row>
    </el-main>
  </el-container>
</template>

<script>
import request from '@/utils/request'
import Plotly from 'plotly.js-dist-min'
import { Message } from 'element-ui'

export default {
  data() {
    return {
      form: {
        rm_step: 4,
        rm_lim: 15,
        sc_step: 14,
        sc_lim: 50,
        saved_file: '',
        email: '',
        dch: 0,
        dcv: 0
      },
      section: '',
      corr: '',
      correctors: [],
      steer_bpm_data: [],
      section_data: [],
      current_xaxis: [],
      current_yaxis_x: [],
      current_yaxis_y: [],
      defaultProps: {
        children: 'children',
        label: 'label'
      },
      chart_data: [
        {
          x: [],
          y: [],
          xaxis: 'x',
          yaxis: 'y',
          name: 'X',
          type: 'scatter'
        },
        {
          x: [],
          y: [],
          xaxis: 'x',
          yaxis: 'y',
          name: 'Y',
          type: 'scatter'
        },
        {
          x: [],
          y: [],
          xaxis: 'x',
          yaxis: 'y2',
          name: 'ΔX',
          type: 'scatter'
        },
        {
          x: [],
          y: [],
          xaxis: 'x',
          yaxis: 'y2',
          name: 'ΔY',
          type: 'scatter'
        },
        {
          x: [],
          y: [],
          xaxis: 'x',
          yaxis: 'y2',
          name: 'react',
          type: 'scatter',
          mode: 'markers',
          marker: {
            symbol: 'x',
            size: 12,
            color: 'blue'
          }
        }
      ],
      layout: {
        grid: {
          rows: 2, 
          columns: 1, 
          //pattern: 'independent',
          subplots: [['xy'], ['xy2']],
          yside: 'left'
        },
        title: "BPM位置",
        xaxis: {
          title:  "BPM序号"
        },
        yaxis: {
          title: {
            text: "BPM位置 [mm]"
          }
        },
        yaxis2: {
          title: {
            text: "BPM位置 [mm]"
          }
        }
      }
    }
  },
  computed: {
    sections() {
      return this.steer_bpm_data.map(e => e.label)
    }
  },
  mounted() {
    this.load_config()
    Plotly.newPlot(this.$refs.chart, this.chart_data, this.layout)
  },
  methods: {
    reset_graph(name) {
      if (name === 'orbit') {
        for (const i of [0, 1]) {
          this.chart_data[i].x.splice(0)
          this.chart_data[i].y.splice(0)
        }
      } else {
        for (const i of [2, 3, 4]) {
          this.chart_data[i].x.splice(0)
          this.chart_data[i].y.splice(0)
        }
      }
    },
    async create_saved_file() {
      if (this.form.saved_file.trim() === "") {
        Message({
          message: "文件名不能为空",
          type: 'error',
          duration: 3 * 1000
        })
      } else {
        const path = '/commissioning/magnet-validation/create-saved-file';
        const response = await request({
          url: path,
          data: {
            filename: this.form.saved_file
          },
          method: 'post',
        })
        if ('msg' in response) {
          Message({
            message: response.msg,
            type: 'info',
            duration: 3 * 1000
          })
        }
      }
    },
    section_change() {
      this.section_data = this.steer_bpm_data.filter(e => e.label === this.section)
      this.correctors = this.section_data[0].children[0].children
      this.reset_graph('orbit')
      this.reset_graph('bpm-var')
      this.corr = ''
      //const bpms = this.form.section_data[0].children[1].children.map(e => e.id)
      //for (const e of bpms) {
      //  this.chart_data[0].x.push(e)
      //  this.chart_data[1].x.push(e)
      //}
      //for (const e of [1, 2, 3]) {
      //  this.chart_data[0].y.push(e)
      //}
      //bpms.forEach((e) => {console.log(this.chart_data[0].x)})
      //this.chart_data[0].x = ['hel', 'why', 'hha']
      //this.chart_data[0].y = [1, 2, 3]
    },

    async load_config() {
      const path = '/commissioning/magnet-validation/get-config';
      const response = await request({
        url: path,
        method: 'get',
      })
      this.steer_bpm_data = response.data
    },

    async correct() {
      const path = '/commissioning/magnet-validation/correct';
      const res = await request({
        url: path,
        data: {
          section_data: this.section_data[0],
          step: (this.section === 'MEBT') ? this.form.rm_step : this.form.sc_step,
          limit: (this.section === 'MEBT') ? this.form.rm_lim : this.form.sc_lim
        },
        method: 'post',
      })

      await this.update_orbit()

      Message({
        message: res.msg,
        type: 'success',
        duration: 3 * 1000
      })
    },

    async update_orbit() {
      const orbit = await this.get_orbit()
      this.reset_graph('orbit')
      for (const e of orbit) {
        this.chart_data[0].x.push(e.label)
        this.chart_data[1].x.push(e.label)
        this.chart_data[0].y.push(e.x)
        this.chart_data[1].y.push(e.y)
      }
      Plotly.redraw(this.$refs.chart)
    },

    async get_orbit() {
      const path = '/commissioning/magnet-validation/get-orbit';

      const res = await request({
        url: path,
        data: {
          section_data: this.section_data[0]
        },
        method: 'post',
      })
      return res.orbit
    },

    async recover_corrector(corr, step) {
      const path = '/commissioning/magnet-validation/recover-corr';
      const res = await request({
        url: path,
        data: {
          set_pv: corr,
          step: step,
        },
        method: 'post',
      })
    },

    async save_data(corr, step) {
      if (this.form.saved_file) {
        const path = '/commissioning/magnet-validation/save-data';
        const res = await request({
          url: path,
          data: {
            corr: corr,
            step: step,
            bpm_names: this.chart_data[2].x,
            bpm_var_xs: this.chart_data[2].y,
            bpm_var_ys: this.chart_data[3].y
          },
          method: 'post',
        })
      }
    },

    async set_corrector() {
      if (this.corr) {
        let orbit = await this.get_orbit()
        const prev_xs = orbit.map(e => e.x)
        const prev_ys = orbit.map(e => e.y)

        const path = '/commissioning/magnet-validation/set-strength';
        const selected_corr = this.correctors.filter(e => e.id === this.corr)[0]
        const res = await request({
          url: path,
          data: {
            name: this.corr,
            set_pv: selected_corr['set_pv'],
            get_pv: selected_corr['get_pv'],
            step: (this.section === 'MEBT') ? this.form.rm_step : this.form.sc_step,
            limit: (this.section === 'MEBT') ? this.form.rm_lim : this.form.sc_lim
          },
          method: 'post',
        })
        const step = res.step
        orbit = await this.get_orbit()
        const current_xlabels = orbit.map(e => e.label)
        const current_xs = orbit.map(e => e.x)
        const current_ys = orbit.map(e => e.y)

        this.reset_graph('bpm-var')
        for (const [i, v] of current_xlabels.entries()) {
          this.chart_data[2].x.push(v)
          this.chart_data[3].x.push(v)
          this.chart_data[2].y.push(current_xs[i] - prev_xs[i])
          this.chart_data[3].y.push(current_ys[i] - prev_ys[i])
        }

        const start_idx = current_xlabels.indexOf(res.start_bpm)
        if (start_idx !== -1) {
          current_xlabels.slice(start_idx).forEach(e => {
            this.chart_data[4].x.push(e)
            this.chart_data[4].y.push(0)

          })
        }

        Plotly.redraw(this.$refs.chart)

        this.recover_corrector(selected_corr['set_pv'], step)
        this.save_data(this.corr, step)
      } else {
        Message({
          message: "请选择对应校正铁",
          type: 'info',
          duration: 3 * 1000
        })
      }
    }
  }
}
</script>

<style scoped>
</style>