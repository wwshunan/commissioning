<template>
   <div class="container">
       <FlashMessage :position="'right bottom'"></FlashMessage>
       <div class="row">
           <div class="col-md-4">
               <b-form-group label="执行序列选择" label-for="sequenceSelection">
                   <b-form-select v-model="selected" :options="options"
                                  :select-size="4" id="sequenceSelection"></b-form-select>
                   <b-button variant="secondary mt-2"
                             @click.prevent="on_load">Load</b-button>
               </b-form-group>
           </div>
       </div>
       <div class="row">
           <div class="col-md-5">
               <b-form-group label="已选择执行序列" label-for="sequenceSelection">
                   <JqxTreeGrid ref="myTreeGrid"
                                :width="width"
                                :editable="true"
                                :columns="columns"
                                :theme="theme"
                                selection-mode="singlecell"
                                :source="dataAdapter">
                   </JqxTreeGrid>

                   <div>
                       <b-btn-group>
                           <b-button variant="secondary mt-2"
                                     @click.prevent="execute">execute</b-button>
                           <b-button variant="secondary mt-2"
                                     @click.prevent="step">step</b-button>
                           <b-button variant="secondary mt-2"
                                     @click.prevent="next">next</b-button>
                           <b-button variant="secondary mt-2"
                                     @click.prevent="stop">stop</b-button>
                       </b-btn-group>
                   </div>

               </b-form-group>
           </div>
       </div>

       <div class="row">
           <div class="col-md-8">
               <b-form-group label="任务执行结果">
                   <b-card class="scroll">
                       <b-card-text v-for="r in task_results"
                                    :class="set_color(r.status)"
                                    :key="r.id">
                           {{r.id}} {{r.name}} {{r.status}}
                       </b-card-text>
                   </b-card>
               </b-form-group>
           </div>
       </div>
       <div class="row" v-if="component">
           <div class="col-md-8">
               <b-form-group label="人为交互任务">
                   <component :is="component"></component>
                   <b-button variant="secondary mt-2"
                             @click.prevent="stop">Done</b-button>
               </b-form-group>
           </div>
       </div>
   </div>
</template>

<script>
    import axios from 'axios';
    import JqxTreeGrid from 'jqwidgets-scripts/jqwidgets-vue/vue_jqxtreegrid.vue';
    import Lattice from './Lattice.vue';
    import io from 'socket.io-client';
    let socket = io.connect("127.0.0.1:5000");

    let directiveSource = [
        { directiveName: "RUN", id: 1},
        { directiveName: "BREAKPOINT", id: 2 },
    ];
    //let resultArray = ["<span style='color: red; '>NOT_STARTED</span>", "FINISHED", "FINISHED_FAULTY", "SKIPPED" ];
    export default {
        components: {
            JqxTreeGrid, Lattice
        },
        data: function() {
            return {
                task_results: [],
                component: undefined,
                selected: null,
                selected_sequence: null,
                width: "800px",
                options: [],
                sequences: [],
                theme: 'material',
                dataAdapter: new jqx.dataAdapter(this.source),
                columns: [
                    {
                        text: 'TaskName',
                        dataField: 'name',
                        width: '25%',
                        editable: false
                    },
                    {
                        text: 'Description',
                        dataField: 'description',
                        width: '40%',
                        editable: false
                    },
                    {
                        text: 'Directive',
                        dataField: 'directive',
                        width: '15%',
                        columnType: 'template',
                        createEditor: (row, cellvalue, editor) => {
                            editor.jqxDropDownList({autoDropDownHeight: true,
                                source: directiveSource, displayMember: 'directiveName',
                                valueMember: 'id', width: '100%', height: '100%' });
                        },
                        initEditor: (row, cellvalue, editor) => {
                            editor.jqxDropDownList('selectItem', cellvalue);
                        },
                        getEditorValue: (row, cellvalue, editor) => {
                            // return the editor's value.
                            let val = editor.val();
                            let item = directiveSource.find((x => x.id == val));
                            return item.directiveName;
                        }

                    },
                    {
                        text: 'Result',
                        dataField: 'result',
                        width: '20%',
                        editable: false
                    },
                ],
            }
        },
        mounted() {
            this.load_seqs();
        },
        created() {
            this.task_listen()
        },
        beforeCreate: function () {
            this.source = {
                dataType: "json",
                dataFields: [
                    { name: 'id', type: 'number' },
                    { name: 'name', type: 'string' },
                    { name: 'description', type: 'string' },
                    { name: 'directive', type: 'string' },
                    { name: 'result', type: 'string' },
                    { name: 'children', type: 'array' },
                ],
                hierarchy:
                {
                    root: 'children'
                },
                id: 'id',
                localData: []
            };
        },
        methods: {
            set_color(task_status) {
                let color = 'text-success';
                if (task_status === 'FAILURE') {
                    color = 'text-danger';
                }
                return color;
            },
            async load_seqs() {
                const path = 'http://127.0.0.1:5000/commissioning/load-sequences';
                const response = await axios.get(path);
                this.sequences = response.data["sequences"];

                let sequence_options = [];
                this.sequences.forEach((e) => {
                    sequence_options.push({value: e.name, text: e.name})
                });
                for (let option_name in this.sequences.keys()) {
                    sequence_options.push({value: option_name, text: option_name})
                }
                this.options = sequence_options;
            },
            async on_load() {
                this.selected_sequence = this.sequences.filter((x) => {
                    return x.name===this.selected
                });
                this.source.localdata = this.selected_sequence;
                this.dataAdapter.dataBind();
                this.$refs.myTreeGrid.updateBoundData();
                this.$refs.myTreeGrid.expandAll();
                let sequence_id = this.selected_sequence[0].id;
                this.$refs.myTreeGrid.selectRow(sequence_id);
                const path = 'http://127.0.0.1:5000/commissioning/sequence-init';
                const payload = {'id': this.selected_sequence[0].id};
                const response = await axios.post(path, payload);
                if (response.data.status === 'OK') {
                    this.flashMessage.success({
                        title: '序列装载',
                        message: '序列装载成功，准备执行'
                    })
                }
            },
            async execute() {
                const path = 'http://127.0.0.1:5000/commissioning/sequence-execute';
                const response = await axios.post(path);
                if (this.selected_sequence[0].children !== undefined) {
                    let task_id = this.selected_sequence[0].children[0].id;
                    this.$refs.myTreeGrid.clearSelection();
                    this.$refs.myTreeGrid.selectRow(task_id);
                }
                if (response.data.status === 'OK') {
                    this.flashMessage.success({
                        title: '序列执行',
                        message: '序列正在执行'
                    })
                }

            },
            stop() {
                const path = 'http://127.0.0.1:5000/commissioning/task-stop';
                const response = axios.post(path);
            },
            traverse_tasks(task_list) {
                let task_ids = [];
                task_list.forEach((e) => {
                    if (e.children !== undefined) {
                        let children = this.traverse_tasks(e.children);
                        task_ids.push(...children);
                    }
                    else {
                        task_ids.push(e.id);
                    }
                });
                return task_ids
            },
            next_task(current_task_id) {
                let task_ids = this.traverse_tasks(this.selected_sequence);
                for (let i=0;i < task_ids.length; i++) {
                    if ((task_ids[i] === current_task_id) && (i+1 !== task_ids.length)){
                        this.$refs.myTreeGrid.clearSelection();
                        this.$refs.myTreeGrid.selectRow(task_ids[i+1]);
                    }
                }
            },
            async step() {
                const path = 'http://127.0.0.1:5000/commissioning/task-step';
                const select_row = this.$refs.myTreeGrid.getSelection();
                const payload = {'id': select_row[0].id};
                const response = await axios.post(path, payload);
                if (select_row[0].children !== undefined) {

                }
                //this.$refs.myTreeGrid.selectRow()
            },
            task_listen() {
                socket.on('finished', (data)=>{
                    this.task_results.push(data);
                    this.next_task(data.id);
                });
            }
        }
    }
</script>
<style scoped>
    @import '../../node_modules/jqwidgets-scripts/jqwidgets/styles/jqx.base.css';
    @import '../../node_modules/jqwidgets-scripts/jqwidgets/styles/jqx.material.css';
    .scroll {
        max-height: 200px;
        overflow-y: auto;
    }
</style>
