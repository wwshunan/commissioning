<template>
  <el-container>
    <el-header>
      <h3>加速器硬件参数设置</h3>
    </el-header>
    <br/>
    <el-main>
      <el-form  @submit.prevent="onSubmit" enctype="multipart/form-data" size="mini">
        <el-form-item label="选择lattice设置段">
          <div style="text-align: left">
            <el-radio-group
                v-model="selected"
                :options="sections"
            >
              <el-radio v-for="item in sections"
                        :label="item.value"
                        :key="item.value">
                {{item.text}}
              </el-radio>
            </el-radio-group>
          </div>
        </el-form-item>

        <el-form-item label="TraceWin Lattice文件">
          <div style="text-align: left">
            <el-upload
                ref="upload"
                class="upload-demo"
                action=""
                :limit="1"
                :http-request="upload_file"
                :on-success="success_handler"
                :on-error="error_handler"
            >
              <el-button type="primary">点击上传</el-button>
            </el-upload>
          </div>
        </el-form-item>
        <el-form-item label="将lattice写入硬件">
          <div style="text-align: left">
            <el-button type="primary"
                       @click.native="onLatticeSetting">提交</el-button>
          </div>
        </el-form-item>
        <el-form-item label="查询磁铁硬件设置">
          <div style="text-align: left">
            <el-button type="primary" @click.native="onLatticeCheck">提交</el-button>
          </div>
        </el-form-item>
      </el-form>
      <div>
        <el-table
            :data="diff_magnets"
            :span-method="objectSpanMethod">
          <caption>设定值和回读值超过0.5A的磁铁:</caption>
          <el-table-column
              prop="section"
              label="加速器段">
          </el-table-column>
          <el-table-column
              prop="magnet"
              label="磁铁">
          </el-table-column>
          <el-table-column
              prop="diff"
              label="差异值">
          </el-table-column>
          <!--<b-tbody v-for="(magnets, section, sectionIndex) in diff_magnets" :key="sectionIndex">
            <b-tr>
              <b-th :rowspan="Object.keys(magnets).length+1" class="text-center align-middle">{{section}}</b-th>
            </b-tr>
            <b-tr v-for="(value, name, magnetIndex) in magnets" :key="magnetIndex">
              <b-td class="text-center align-middle">{{name}}</b-td>
              <b-td class="text-center align-middle">{{value}}</b-td>
            </b-tr>
          </b-tbody>-->
        </el-table>
      </div>
    </el-main>
  </el-container>
</template>

<script>
import request from '@/utils/request'
import { Message } from 'element-ui'

export default {
  data() {
    return {
      upload_url: 'http://127.0.0.1:5000/commissioning/lattice-upload',
      sections: [
        {
          text: 'MEBT段到CM段',
          value: 'cm'
        },
        {
          text: 'CM段出口到靶',
          value: 'target'
        },
        {
          text: '靶到终端探测器',
          value: 'detector'
        }],
      selected: 'cm',
      showMessage: false,
      showLattice: false,
      message: '',
      file: '',
      lattice: {},
      saveToDB: false,
      operations: [],
      selectedDate: '',
      currentPage: 1,
      perPage: 5,
      operationToShow: [],
      latticeDescription: '',
      diff_magnets: [],
      diff_section_len: [],
    }
  },
  methods: {
    submit_upload() {
      this.$refs.upload.submit();
    },
    success_handler() {
      Message({
        message: '文件上传成功',
        type: 'success',
        duration: 5 * 1000
      })
    },
    error_handler() {
      Message({
        message: '文件上传失败',
        type: 'error',
        duration: 5 * 1000
      })
    },
    mod3(index) {
      return index % 3 === 0;
    },
    isDict(v) {
      return typeof v === "object";
    },
    onSelectPage() {
      const startLattice = (this.currentPage - 1) * this.perPage;
      const toLattice = startLattice + this.perPage;
      this.operationToShow = this.operations.slice(startLattice, toLattice);
      this.lattice = this.operationToShow[0]['lattice']
      this.latticeDescription = this.operationToShow[0]['description']
    },
    onSelect(e) {
      this.file = e.target.files[0];
    },
    showLatticeInfo(lattice, description) {
      this.showLattice = true;
      this.lattice = lattice;
      this.latticeDescription = description;
    },
    onLatticeShow(lattice, description) {
      this.showLatticeInfo(lattice, description);
    },
    selectElements(elements, isFirst) {
      let [first] = Object.keys(elements);
      if (isFirst) {
        return first
      } else {
        const remainingElements = Object.keys(elements).reduce((object, key) => {
          if (key !== first) {
            object[key] = elements[key]
          }
          return object
        }, {})
        return remainingElements
      }
    },
    async upload_file(params) {
      const path = '/commissioning/lattice-upload';
      let formData = new FormData();
      formData.append('lattice_file', params.file);
      formData.append('section', this.selected);
      try {
        await request({
          url: path,
          data: formData,
          method: 'post',
        })
        this.showLattice = true;
        this.operations = [];
        this.operationToShow = [];
      }
      catch (err) {
        console.log(err)
      }
    },
    async onLatticeSetting() {
      const path = '/commissioning/lattice-setting';
      try {
        await request({
          url: path,
          method: 'post',
        })
        Message({
          message: 'Lattice设置成功！',
          type: 'success',
          duration: 5 * 1000
        })
      } catch (e) {
        Message({
          message: 'Lattice设置失败！',
          type: 'error',
          duration: 5 * 1000
        })
      }
    },
    async onLatticeCheck() {
      const path = '/commissioning/lattice-check';
      try {
        const response = await request({
          url: path,
          method: 'get',
        })
        this.diff_section_len = []
        this.diff_magnets = []
        console.log(response.diff_magnets)
        for (let section in response.diff_magnets) {
          this.diff_section_len.push(Object.keys(response.diff_magnets[section]).length)
          for (let magnet in response.diff_magnets[section]) {
            this.diff_magnets.push({
              'section': section,
              'magnet': magnet,
              'diff': response.diff_magnets[section][magnet]
            })
          }
        }
        console.log(this.diff_section_len)
      } catch (e) {
        Message({
          message: 'PV无法连接！',
          type: 'error',
          duration: 5 * 1000
        })
      }
    },
    objectSpanMethod({ row, column, rowIndex, columnIndex }) {
      let cumsum = 0
      let rowSpanIndex = []
      const non_zero_array = this.diff_section_len.filter((x) => x)
      for (let l of non_zero_array) {
        rowSpanIndex.push(cumsum)
        cumsum += l
      }
      rowSpanIndex.push(cumsum)
      if (columnIndex === 0) {
        if (rowSpanIndex.slice(0, -1).includes(rowIndex)) {
          let i = rowSpanIndex.indexOf(rowIndex)
          console.log(i, rowSpanIndex)
          return {
            rowspan: rowSpanIndex[i+1] - rowSpanIndex[i],
            colspan: 1
          }
        } else {
          return {
            rowspan: 0,
            colspan: 0
          };
        }
      }
    }
  }
}
</script>
<style scoped>
.content {
  transform: translateY(-55%);
}
</style>