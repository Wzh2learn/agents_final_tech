/**
 * 知识库页面重构方案 - Dify 风格
 * 
 * 核心改进：
 * 1. 左侧边栏导航 - 知识库列表（固定 240px）
 * 2. 主内容区 - 文档列表 + 分段预览（双栏）
 * 3. 右侧配置面板 - 知识库设置（固定 320px）
 * 
 * 路由结构：
 * - /knowledge - 知识库首页（卡片网格）
 * - /knowledge/{kb_id} - 知识库详情（文档+分段+设置三栏）
 */

// ==================== 新布局结构 ====================

const LAYOUT_STRUCTURE = {
  // 左侧边栏 - 知识库导航（固定 240px）
  sidebar: {
    width: '240px',
    fixed: true,
    components: [
      'logo-area',
      'new-kb-button',
      'kb-list',       // 可滚动的知识库列表
      'global-settings' // 全局设置入口
    ]
  },
  
  // 主内容区 - 根据路由变化
  main: {
    // 首页：知识库卡片网格
    home: {
      layout: 'grid',
      columns: 'repeat(auto-fill, minmax(360px, 1fr))',
      gap: '24px',
      cards: [
        'kb-icon',
        'kb-name',
        'kb-tags',      // 分段模式、检索模式标签
        'kb-stats',     // 文档数、分段数
        'kb-actions'    // 进入、设置按钮
      ]
    },
    
    // 详情页：三栏布局
    detail: {
      layout: 'three-column',
      left: {
        width: '280px',
        components: ['doc-list', 'upload-button']
      },
      center: {
        flex: 1,
        components: ['chunk-preview', 'segment-tree']
      },
      right: {
        width: '320px',
        components: ['kb-config', 'retrieval-settings']
      }
    }
  }
};

// ==================== 父子分段可视化 ====================

const PARENT_CHILD_VISUALIZATION = {
  // 父分段卡片
  parentCard: {
    style: 'filled',           // 实心背景
    color: '#f0fdf4',        // 浅绿色背景
    border: '2px solid #0f766e',
    icon: '👨‍👧',
    title: '父分段 · 上下文',
    content: '显示父分段完整内容（约2000字符）',
    childrenIndicator: true    // 显示子分段数量
  },
  
  // 子分段卡片
  childCard: {
    style: 'outlined',       // 线框风格
    color: '#ffffff',
    border: '1px solid #e5e7eb',
    icon: '🔍',
    title: '子分段 · 检索',
    content: '显示子分段内容（约500字符）',
    score: true               // 显示匹配分数
  },
  
  // 层级连接线
  connector: {
    type: 'vertical-line',
    color: '#0f766e',
    width: '2px',
    animation: 'pulse'       // 脉冲动画指示关联
  }
};

// ==================== 交互动效规范 ====================

const INTERACTION_SPECS = {
  // 卡片悬停
  cardHover: {
    transform: 'translateY(-4px)',
    shadow: '0 12px 24px rgba(0,0,0,0.1)',
    borderColor: '#0f766e',
    transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
  },
  
  // 分段展开
  chunkExpand: {
    height: 'from 60px to auto',
    opacity: '0 to 1',
    duration: '300ms',
    easing: 'ease-out'
  },
  
  // 父子关联高亮
  parentChildHighlight: {
    trigger: 'hover child',
    effect: 'parent glow + connector pulse',
    color: '#0f766e',
    duration: '200ms'
  },
  
  // 上传进度
  uploadProgress: {
    type: 'circular + percentage',
    color: '#0f766e',
    successAnimation: 'checkmark draw'
  }
};

// ==================== 颜色系统 ====================

const COLOR_SYSTEM = {
  // 品牌色
  primary: {
    50: '#f0fdf4',
    100: '#dcfce7',
    500: '#0f766e',
    600: '#0d9488',
    700: '#0f766e'
  },
  
  // 功能色
  parent: {
    bg: '#f0fdf4',
    border: '#0f766e',
    text: '#166534'
  },
  child: {
    bg: '#ffffff',
    border: '#e5e7eb',
    text: '#374151'
  },
  
  // 状态色
  retrievalModes: {
    vector: { color: '#8b5cf6', icon: '🧠' },
    fulltext: { color: '#3b82f6', icon: '📖' },
    hybrid: { color: '#0f766e', icon: '🔀' }
  }
};
