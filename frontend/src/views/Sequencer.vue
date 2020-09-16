<template>
   <div class="container">
       <b-form-group label="执行序列选择" label-for="sequenceSelection">
           <b-form-select v-model="selected" :options="options"
                          :select-size="4" id="sequenceSelection"></b-form-select>
           <b-button variant="secondary mt-2"
                     @click.prevent="on_load">Load</b-button>
       </b-form-group>
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
               </b-btn-group>
           </div>
       </b-form-group>
       <b-form-group label="任务执行结果">
           <b-card class="scrollbar">
               <b-card-text v-for="r in task_results"
                            :class="set_color(r.status)"
                            :key="r.id">
                   {{r.id}} {{r.name}} {{r.status}}
               </b-card-text>
           </b-card>
       </b-form-group>
   </div>
</template>

<script>
    import axios from 'axios';
    import JqxTreeGrid from 'jqwidgets-scripts/jqwidgets-vue/vue_jqxtreegrid.vue';
    import io from 'socket.io-client';
    let socket = io.connect("127.0.0.1:5000");

    let directiveSource = [
        { directiveName: "RUN", id: 1},
        { directiveName: "BREAKPOINT", id: 2 },
    ];
    //let resultArray = ["<span style='color: red; '>NOT_STARTED</span>", "FINISHED", "FINISHED_FAULTY", "SKIPPED" ];
    export default {
        components: {
            JqxTreeGrid
        },
        data: function() {
            return {
                task_results: [],
                selected: null,
                selected_sequence: null,
                options: [],
                sequences: [],
                width: 800,
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
            on_load() {
                this.selected_sequence = this.sequences.filter((x) => {
                    return x.name===this.selected
                });
                this.source.localdata = this.selected_sequence;
                this.dataAdapter.dataBind();
                this.$refs.myTreeGrid.updateBoundData();
            },
            ready: function () {
                // expand row with 'EmployeeKey = 32'
                this.$refs.myTreeGrid.expandRow(32);
            },
            async execute() {
                const path = 'http://127.0.0.1:5000/commissioning/sequence-execute';
                const payload = {'id': this.selected_sequence[0].id};
                //const payload = {'id': 'xxx'}
                const response = await axios.post(path, payload);

            },
            task_listen() {
                socket.on('finished', (data)=>{
                    console.log('xxx');
                    this.task_results.push(data)
                });
            }
        }
    }
</script>
<style scoped>
    @import '../../node_modules/jqwidgets-scripts/jqwidgets/styles/jqx.base.css';
    @import '../../node_modules/jqwidgets-scripts/jqwidgets/styles/jqx.material.css';
</style>
