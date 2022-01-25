<template>
  <el-container class="home-container">
    <!-- 头部区域 -->
    <el-header>
      <el-button type="info" @click="logout">退出</el-button>
    </el-header>
    <!-- 内容主题区域 -->
    <el-container>
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse?'64px':'200px'">
        <div class="toggle-button" @click="toggleCollapse">|||</div>
        <tree-menu :routes="routes"></tree-menu>
      </el-aside>
      <!-- 右侧内容 -->
      <el-main>
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
const treeMenu = {
  props: {
    routes: {
      type: Array,
      default () {
        return []
      }
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
                      index: route.title
                    }
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
          },
          class: "el-menu-vertical-demo",
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
    treeMenu
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

  created() {
    this.getMenuList()
    this.activePath = window.sessionStorage.getItem('activePath')
  },
  methods: {
    // 退出功能
    logout() {
      // 清空token
      window.sessionStorage.clear()
      this.$router.push('/login')
    },
    // 获取所有的菜单
    async getMenuList() {
      const {data: res} = await this.$http.get('menus')
      if (res.meta.status !== 200) return this.$message.error(res.meta.msg)
      this.menuList = res.data
      console.log(res)
    },
    // 点击按钮，切换菜单的折叠与展开
    toggleCollapse() {
      this.isCollapse = !this.isCollapse
    },
    // 保存链接的激活状态
    saveNavState(activePath) {
      window.sessionStorage.setItem('activePath', activePath)
      this.activePath = activePath
    },
  }
}
</script>

<style scoped>
.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 200px;
  min-height: 400px;
}

</style>

