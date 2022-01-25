<template>
  <el-container class="home-container">
    <!-- 头部区域 -->
    <el-header>
      <el-button type="info" @click="logout">退出</el-button>
    </el-header>
    <el-container>
      <el-aside :width="isCollapse?'64px':'200px'">
        <div class="toggle-button" @click="toggleCollapse">|||</div>
        <tree-menu :routes="routes" :collapse="isCollapse"></tree-menu>
      </el-aside>
      <el-main>
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>

</template>


<script>
const TreeMenu = {
  props: {
    routes: {
      type: Array,
      default () {
        return []
      }
    },
    collapse: {
      type: Boolean
    }
  },
  methods: {
    elements (routes, r) {
      return routes
          .map(route => {
            if (!route.paths) route.paths = []
            if (route.child && route.child.length) {
              return r('el-submenu', {
                    props: {
                      index: route.title
                    }
                  },
                  [
                    r('template', {
                          slot: 'title'
                        },
                        [
                          r('i', {
                            'class': 'el-icon-menu'
                          }),
                          r('span', {
                                slot: 'title'
                              },
                              [
                                route.title
                              ]
                          ),
                        ]
                    ),
                    r('el-menu-item-group',
                        {},
                        [this.elements(route.child, r)]
                    )
                  ]
              )
            } else if (route.path) {
              return r('el-menu-item', {
                    props: {
                      index: route.title,
                      route: route.path
                    },
                  },
                  [
                    route.title
                  ]
              )
            } else {
              return null
            }
          })
          .filter(item => item)
    },
    onSelect (index) {
      console.log('>>>', index)
    }
  },
  render (r) {
    return r(
        'el-menu',
        {
          props: {
            collapse: this.collapse,
            collapseTransition: false,
            router: true
          },
          "class": "el-menu-vertical-demo",
          on: {
            select: this.onSelect
          }
        },
        this.elements(this.routes, r)
    )
  }
}
export default {
  components: {
    TreeMenu
  },
  data() {
    return {
      routes: [
        {
          title: 'Lattice',
          icon: 'fa fa-list-ul',
          child: [
            {
              path: '/lattice/setting',
              title: 'Lattice Setting',
              icon: 'fa fa-file-alt'
            },
            {
              path: '/lattice/log',
              title: 'Lattice Log'
            }
          ]
        },
        {
          title: 'Log',
          icon: 'fa fa-list-ul',
          child: [
            {
              path: '/log/beam-time',
              title: 'Beam Time',
              icon: 'fa fa-clock-o'
            },
            {
              path: '/log/check',
              title: 'Lattice Check',
              icon: 'fa fa-check'
            }
          ]
        },
        {
          title: 'Commissioning',
          icon: 'fa fa-list-ul',
          child: [
            {
              path: '/commissioning/sequencer',
              title: 'Sequencer',
              icon: 'fa fa-yin-yang'
            },
            {
              path: '/commissioning/energy-compute',
              title: 'Tof energy',
              icon: 'fa fa-atom'
            },
            {
              path: '/commissioning/phase-scan',
              title: 'Phase Scan',
              icon: 'fa fa-atom'
            },
            {
              path: '/commissioning/cavity-epk',
              title: 'Cavity Epeak',
              icon: 'fa fa-thermometer-full'
            },
          ]
        }

      ],
      isCollapse: false,
      // 被激活的链接地址
      activePath: ''
    }
  },
  methods: {
    toggleCollapse () {
      this.isCollapse = !this.isCollapse
    },
  }
}
</script>
<style scoped>
.toggle-button {
  background-color: #4a5064;
  font-size: 10px;
  line-height: 24px;
  color: #fff;
  text-align: center;
  letter-spacing: 0.2em;
  cursor: pointer;
}
.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 200px;
  min-height: 400px;
}
el-main {
  background-color: #eaedf1;
}
el-aside {
  background-color: #333744;
}
el-menu {
  background-color: #333744;
  border-right: none;
}
</style>
