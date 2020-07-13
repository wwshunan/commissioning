<template>
    <div class="container">
        <div class="page-header">
            <h3>机器状态检测</h3>
        </div>
        <b-alert :show="showMessage">{{message}}</b-alert>
        <form class="md-form">
            <div class="form-group">
                <div class="form-check" v-for="item in sectionItems" :key="item.id">
                    <input type="checkbox" class="form-check-input"
                           v-model="selectedSections" :id="item.name" :ref="item.name"
                           :value="item.name" @change="onSelectHEBT($event)">
                    <label for="item.id" class="form-check-label">{{item.name}}</label>
                </div>

            </div>
            <div class="form-group">
                <label>Snapshot Machine Status</label><br/>
                <button type="submit" class="btn btn-primary mb-2" @click.prevent="onSnapshot">Submit</button>
            </div>
            <div class="form-group">
                <label>Machine status checkout</label><br/>
                <button type="submit" class="btn btn-primary mb-2" @click.prevent="onCheckout">Submit</button>
            </div>
        </form>
        <div :show="showDiff">
            <h5 v-if="!diffIgnore">Lattice Differences</h5>
            <div v-for="(items, k) in diffs" :key="k">
                <label v-if="Object.keys(items).length !== 0">{{k.toUpperCase()}}</label>
                <ul class="list-group list-group-horizontal">
                    <li class="list-group-item list-group-item-danger"
                        v-for="(val, name) in items" :key="name">
                        {{ name }}: {{ val }}
                    </li>
                </ul>
            </div>
        </div>
    </div>
</template>

<script>
    import axios from 'axios';
    export default {
        data() {
            return {
                items: [],
                message: '',
                showMessage:  false,
                diffs: {},
                showDiff: false,
                sectionItems: [
                    {
                        name: 'LEBT'
                    },
                    {
                        name: 'MEBT'
                    },
                    {
                        name: 'SC'
                    },
                    {
                        name: 'S-HEBT'
                    },
                    {
                        name: 'B-HEBT'
                    },
                ],
                selectedSections: ['LEBT', 'MEBT', 'SC', 'S-HEBT']
            }
        },
        mounted() {
            this.$refs['B-HEBT'][0].disabled = true;
        },
        methods: {
            async onSnapshot() {
                const path = 'http://127.0.0.1:5000/log/snapshot';
                this.showMessage = true;
                const payload = {
                    selected_sections: this.selectedSections
                };
                try {
                    const response = await axios.post(path, payload);
                    this.message = response.data['status'];
                } catch (e) {
                    this.message = 'Failure';
                }
            },
            async onCheckout() {
                const path = 'http://127.0.0.1:5000/log/snapshot-checkout';
                this.showMessage = true;
                try {
                    const response = await axios.get(path);
                    this.showDiff = true;
                    this.diffs = response.data['diffs'];
                    if (this.diffIgnore) {
                        this.message = "Lattice is normal";
                    } else {
                        this.message = "Lattice has difference";
                    }
                } catch (e) {
                    this.message = 'Failure';
                }
            },
            onSelectHEBT(e) {
                if (e.target.value === 'S-HEBT') {
                    this.$refs['B-HEBT'][0].disabled = e.target.checked;
                } else if (e.target.value === 'B-HEBT') {
                    this.$refs['S-HEBT'][0].disabled = e.target.checked;
                }
            }
        },
        computed: {
            diffIgnore: function () {
                let isEmpty = true;
                for (let k in this.diffs) {
                    isEmpty = isEmpty && Object.keys(this.diffs[k]).length === 0;
                }
                return isEmpty;
            }
        }
    }
</script>