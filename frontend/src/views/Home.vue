<template>
    <div id="demo" :class="[{'collapsed': collapsed}]">
        <div class="demo">
            <div class="container-fluid">
                <router-view/>
            </div>
            <sidebar-menu
                    :menu="menu"
                    :collapsed="collapsed"
                    :width="sidebar_width"
                    @toggle-collapse="onToggleCollapse"
            ></sidebar-menu>
        </div>
    </div>
</template>

<script>
  export default {
    data() {
      return {
        menu: [
          {
            header: true,
            title: 'Navigation',
            hiddenOnCollapse: true
          },
          {
            title: 'Lattice',
            icon: 'fa fa-list-ul',
            child: [
              {
                href: '/lattice/setting',
                title: 'Lattice Setting',
                icon: 'fa fa-file-alt'
              },
              {
                href: '/lattice/log',
                title: 'Lattice Log'
              }
            ]
          },
        ],
          sidebar_width: '250px',
          collapsed: false
      }
    },
      methods: {
        onToggleCollapse(collapsed) {
            this.collapsed = collapsed
        }
      }
  }
</script>
<style lang="scss">
    body {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 18px;
        background-color: #f2f4f7;
        color: #262626;
    }
    #demo {
        padding-left: 250px;
    }
    #demo.collapsed {
        padding-left: 50px;
    }
    .demo {
        padding: 50px;
    }
</style>
