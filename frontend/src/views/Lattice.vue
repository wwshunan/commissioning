<template>
    <div class="container">
        <div class="page-header">
            <h3>加速器硬件参数设置</h3>
        </div>
        <br/>
        <b-alert v-show="showMessage">{{message}}</b-alert>
        <div class="file">
            <form class="md-form" @submit.prevent="onSubmit" enctype="multipart/form-data">
                <div class="form-group">
                    <label>Upload TraceWin Lattice File</label><br/>
                    <div>
                        <a class="btn-floating purple-gradient mt-0">
                            <i class="fas fa-cloud-upload-alt" aria-hidden="true"></i>
                            <input type="file" ref="file" @change="onSelect">
                        </a>
                    </div>
                    <br/>
                    <button class="btn btn-primary" @click.prevent="onSubmit">Submit</button>
                </div>
                <div class="form-group">
                    <label for="databaseSetting" class="col-form-label">Write Lattice to Hardware</label>
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="checkbox"
                               id="databaseSetting" v-model="saveToDB">
                        <label class="form-check-label" for="databaseSetting">
                            Write to Database?
                        </label>
                    </div>
                    <div class="form-group" v-show="saveToDB">
                        <label for="latticeDescription">Description for Lattice</label>
                        <textarea class="form-control"
                                  id="latticeDescription"
                                  rows="3"
                                  v-model="latticeDescription">
                        </textarea>
                    </div>
                    <button type="submit" class="btn btn-primary mb-2" @click.prevent="onLatticeSetting">Submit</button>
                </div>
                <div class="form-group">
                    <label class="col-form-label">Database Query</label>
                    <div class="row">
                        <div class="form-group col-auto">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-calendar"></span></span>
                                </div>
                                <datetime type="datetime" placeholder="From date" v-model="startDate">
                                </datetime>
                            </div>
                        </div>
                        <div class="form-group col-auto">
                            <div class="input-group">
                                <div class="input-group-prepend">
                                    <span class="input-group-text"><span class="fas fa-calendar"></span></span>
                                </div>
                                <datetime type="datetime" placeholder="To date" v-model="toDate">
                                </datetime>
                            </div>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary" @click.prevent="onDBQuery">Query</button>
                </div>
            </form>
        </div>
        <div class="row">
            <div class="col-sm-3">
                <div class="list-group">
                    <a href="#" class="list-group-item list-group-item-action"
                       v-for="operation  in operationToShow"
                       :key="operation['timestamp']"
                       @click.prevent.stop="onLatticeShow(operation['lattice'], operation['description'])">
                        {{ operation['timestamp'] }}
                    </a>
                </div>
            </div>
            <div class="col-auto">
                <div v-show="showLattice">
                    <p>{{ latticeDescription }}</p>
                    <div v-for="(section, section_name) in lattice" :key="section_name">
                        <span class="label label-default">{{ section_name }}</span>
                        <table class="table table-sm"
                               v-for="(element_type, element_type_name) in section"
                               :key="element_type_name">
                            <template v-for="(value, el_name, index) in element_type">
                                <tr v-if="mod3(index)" :key="'row-' + el_name"></tr>
                                <td :key="el_name" v-if="isDict(value)" class="d-inline-block">
                                    <span class="badge badge-info content">{{el_name}}</span>
                                    <div style="display: inline-block">
                                        Amp:{{value['amp']}}
                                        <br/>
                                        Phase:{{value['phase']}}
                                    </div>
                                </td>
                                <td :key="el_name" v-else>
                                    <span class="badge badge-info">{{el_name}}</span>: {{value}}A
                                </td>
                            </template>
                        </table>
                    </div>
                </div>
            </div>
        </div>
        <div class="overflow-atuo" v-if="rows > 0">
            <b-pagination
                    v-model="currentPage"
                    :total-rows="rows"
                    :per-page="perPage"
                    @input="onSelectPage"
                    align="center">
            </b-pagination>
        </div>
    </div>
</template>

<script>
    import axios from 'axios';
    import { Datetime } from 'vue-datetime';

    export default {
        data() {
            return {
                showMessage: false,
                showLattice: false,
                message: '',
                file: '',
                lattice: {},
                saveToDB: false,
                startDate: '',
                toDate: '',
                operations: [],
                selectedDate: '',
                currentPage: 1,
                perPage: 5,
                operationToShow: [],
                latticeDescription: ''
            }
        },
        components: {
            datetime: Datetime
        },
        computed: {
            rows() {
                return this.operations.length;
            }
        },
        methods: {
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
            async onSubmit() {
                const path = 'http://127.0.0.1:5000/lattice-upload';
                let formData = new FormData();
                var newFileName = encodeURIComponent(this.file.name);
                var newFile = new File([this.file],
                    newFileName,
                    {type: this.file.type});
                formData.append('file', newFile);
                try {
                    const response = await axios.post(path, formData);
                    this.showMessage = true;
                    this.message = 'Lattices上传成功';
                    this.showLattice = true;
                    const data = response.data;
                    this.operations = [];
                    this.operationToShow = [];
                    this.lattice = data['lattice'];
                }
                catch (err) {
                    this.message = 'Lattice上传失败';
                    this.showMessage = true;
                }
            },
            async onLatticeSetting() {
                const path = 'http://127.0.0.1:5000/lattice-setting';
                const payLoad = {
                    'saveToDB': this.saveToDB,
                    'latticeDescription': this.latticeDescription
                };
                try {
                    await axios.post(path, payLoad);
                    this.message = 'Lattice设置成功';
                    this.saveToDB = false;
                    this.showMessage = true;
                } catch (e) {
                   this.message = "Lattice设置失败";
                   this.showMessage = true;
                }
            },
            async onDBQuery() {
                const path = 'http://127.0.0.1:5000/lattice-query';
                const payLoad = {
                    'startDate': this.startDate,
                    'toDate': this.toDate
                };
                try {
                    const response = await axios.post(path, payLoad);
                    this.showMessage = true;
                    this.message = 'Lattice读取成功';
                    this.showLattice = true;
                    const data = response.data;
                    this.operations = data['operations'];
                    this.onSelectPage();
                } catch (e) {
                    this.message = "Lattice读取失败";
                    this.showMessage = true;
                }
            }
        },
    }
</script>
<style scoped>
    .content {
        transform: translateY(-55%);
    }
</style>